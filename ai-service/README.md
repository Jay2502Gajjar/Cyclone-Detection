# CycloVision AI service

Stateless inference. Loads a model bundle once at startup and answers questions about
frames and forecasts. No database connection, no downloads, no training code — those live
in [`../ml/`](../ml/README.md).

## Two things it will never do

- **See the future.** `InferFullRequest` has no field capable of carrying an observation
  later than `asOf`, and its validator rejects one with a 422 rather than silently
  dropping it.
- **Produce verification.** `InferFullResponse` has no verification field. Ground truth is
  read from the database by the backend, after inference has already returned.

## Layout

```
app/
├─ main.py          lifespan → registry.load_all()
├─ registry.py      the only place a provenance stamp is created
├─ schemas/         Pydantic, mirroring API_CONTRACT.md
├─ routers/         health · full · frame · analogues
├─ structure/       polar regrid → 7 metrics → transparent regime rules
├─ inference/       model protocols + Phase 0 placeholders
├─ pipeline/        composes every step and stamps the result
├─ risk/ · report/  weighted rules · deterministic template
└─ io/              brightness-temperature loading, path-guarded
```

## Running

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
.\.venv\Scripts\python.exe -m pytest
```

`GET /health` reports `DEGRADED` with all nine components untrained in Phase 0. That is
the correct answer, not a failure.
