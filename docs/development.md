# Development

## Prerequisites

| | Version here | Notes |
|---|---|---|
| Java | 17.0.12 | Use the Maven Wrapper (`mvnw.cmd`), not a system `mvn` |
| Node | 24.14.1 | |
| Python | 3.13 | `ai-service/.venv` already exists with the full stack |
| Docker Desktop | 29.4.0 | PostGIS only |

## Two environment quirks worth knowing up front

**Run Maven from PowerShell, not Git Bash.** The Maven install on this machine lives at
`D:\Aditya's\JavaLibs\apache-maven-3.9.11`, and the apostrophe in that path breaks the
bash launcher script (`ClassNotFoundException: plexus.classworlds.launcher.Launcher`).
The repository ships the **Maven Wrapper**, which sidesteps the problem entirely — always
use `.\mvnw.cmd`.

**The default ports avoid the usual collisions.** On this machine 5432 was already taken
by another project's Postgres container and 8080 by a local Jenkins. Rather than asking
anyone to stop their other work, CycloVision uses:

| Service | Port | Override |
|---|---|---|
| PostgreSQL + PostGIS | **5433** | `docker-compose.yml` |
| Spring Boot | **8090** | `SERVER_PORT` |
| FastAPI | 8000 | `--port` |
| Vite | 5173 | `vite.config.ts` |

## Starting everything

```powershell
.\scripts\dev-up.ps1
```

That brings up PostGIS, waits for it to accept connections, then opens three windows for
the backend, the AI service and the frontend.

Manually, if you prefer:

```powershell
docker compose up -d postgres

cd backend
.\mvnw.cmd spring-boot:run                     # :8090, applies Flyway V1-V3 on startup

cd ..\ai-service
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

cd ..\frontend
npm run dev                                     # :5173
```

| | |
|---|---|
| App | http://localhost:5173 |
| API health | http://localhost:8090/api/health |
| Swagger | http://localhost:8090/swagger-ui.html |
| AI service docs | http://localhost:8000/docs |

## What a healthy Phase 0 looks like

```jsonc
// GET /api/health
{ "status": "DEGRADED",
  "aiService": { "status": "UP", "models": [ /* 9, all isTrained: false */ ] },
  "database": "UP", "demoMode": false, "bundleVersion": "phase0" }
```

`DEGRADED` with every component untrained **is the correct answer**. `status` only reaches
`UP` when the AI service is reachable *and* at least one model is genuinely trained.
`GET /api/storms` returning `[]` is also correct — Phase 1 loads the data.

## Testing

```powershell
.\scripts\test-all.ps1                  # backend + ai-service + frontend
.\scripts\test-all.ps1 -WithDatabase    # also the PostGIS migration test
```

Individually:

```powershell
cd backend      ; .\mvnw.cmd test
cd backend      ; .\mvnw.cmd test "-Dcyclovision.db.it=true"   # needs Postgres up
cd ai-service   ; .\.venv\Scripts\python.exe -m pytest
cd frontend     ; npm run build ; npm run lint
```

The backend's unit tests are deliberately **database-free** — they are slice and unit
tests, so they run anywhere. `SchemaMigrationTest` needs real PostgreSQL and is opt-in;
H2 cannot stand in, because the schema depends on PostGIS geography, a generated column
and CHECK constraints that carry two of our architectural invariants.

## Database

```powershell
docker exec -it cyclovision-postgres psql -U cyclovision -d cyclovision
```

Flyway owns the schema; Hibernate is set to `ddl-auto: validate` and must never alter it.
To change the schema, add a new `V{n}__*.sql` — never edit an applied migration.

Reset completely (destroys ingested data):

```powershell
.\scripts\dev-down.ps1 -Purge
docker compose up -d postgres
```

## Demo insurance

```powershell
.\scripts\demo-check.ps1
```

Run this immediately before demonstrating, every time. It verifies the three services,
counts storms and precomputed frames, checks that every demo storm is still in the `test`
split, and reports whether `DEMO_MODE` is on.

`DEMO_MODE=true` (or `--spring.profiles.active=demo`) forces every forecast to come from
stored `demo_scenario` rows, stamped `DEMO_DATA` and `servedFrom: "demo"`. The timeline is
unaffected — it reads precomputed frames and never touches the AI service — so the primary
interaction survives the AI service being switched off entirely.

## Making a change

The API contract is locked and written **once**, as TypeScript, in `API_CONTRACT.md`. Java
records and Pydantic models mirror it. Changing a field means changing all three and
running all three suites; nothing detects drift automatically.

Layer boundaries are load-bearing, not stylistic:

| Layer | May do | May not |
|---|---|---|
| `frontend/` | render | call FastAPI directly, compute forecasts |
| `backend/` | read the DB, orchestrate, verify | parse IBTrACS/HURSAT, run models, schedule jobs |
| `ai-service/` | load models, read `FRAMES_DIR` | connect to the DB, train, see data later than `asOf` |
| `ml/` | download, train, precompute, write the DB | be imported at request time, be deployed |

## Troubleshooting

| Symptom | Cause |
|---|---|
| `ClassNotFoundException: plexus.classworlds` | Running `mvn` in Git Bash. Use `.\mvnw.cmd` in PowerShell. |
| `Bind for 0.0.0.0:5433 failed` | Something else holds the port. `docker ps` / `Get-NetTCPConnection -LocalPort 5433`. |
| Backend exits at startup | Postgres not up. `docker compose up -d postgres`. |
| `aiService.status: DOWN` | AI service not running. Forecasts return 503; the timeline still works. |
| Everything says `DEMO_DATA` | Correct for Phase 0. No model is trained yet. |
