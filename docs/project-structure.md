# Project structure

Every folder and significant file: what it is responsible for, whether it runs at runtime
or offline, what belongs in it, and — often more usefully — what does not.

---

## Top level

```
CycloVision/
├── README.md                   entry point and documentation index
├── API_CONTRACT.md             canonical type contract (TypeScript is the source)
├── docker-compose.yml          PostGIS only
├── .env.example                every environment variable, with local defaults
├── frontend/                   React Command Center                    [runtime]
├── backend/                    Spring Boot orchestration               [runtime]
├── ai-service/                 FastAPI inference                       [runtime]
├── ml/                         offline data engineering and training   [OFFLINE]
├── data/                       datasets, frames, BT arrays             [offline]
├── models/                     weights and evaluation artefacts        [both]
├── docs/                       this documentation package
└── scripts/                    PowerShell dev and demo scripts
```

| File | Responsibility | Do not put here |
|---|---|---|
| `API_CONTRACT.md` | The single definition of every API type. Java and Python mirror it. | Prose about endpoints — that is `docs/api.md` |
| `docker-compose.yml` | PostgreSQL + PostGIS on port 5433 | Frontend/backend/AI containers; they run natively in development |
| `.env.example` | Every variable with a working local default | Real secrets |

---

## `frontend/` — runtime

```
frontend/
├── index.html
├── package.json  vite.config.ts  tsconfig*.json  .oxlintrc.json
└── src/
    ├── main.tsx                 QueryClient + Router + theme import
    ├── App.tsx                  renders AppRoutes, nothing else
    ├── routes.tsx               exactly two routes
    ├── theme/tokens.css         Tailwind v4 @theme + design tokens
    ├── types/api.ts             mirrors API_CONTRACT.md — the drift check
    ├── api/                     client.ts · storms.ts · forecast.ts · modelCard.ts
    ├── hooks/                   TanStack Query wrappers, one per resource
    ├── store/timeline.ts        Zustand: THREE fields only
    ├── lib/                     format.ts · provenance.ts
    ├── components/
    │   ├── ui/                  GlassPanel · ProvenanceChip · Metric · Segmented
    │   │                        Drawer · ConfidenceBar · DemoDataBanner
    │   ├── map/                 StormMap.tsx + layers/{track,irOverlay}.ts
    │   ├── timeline/            TimelineScrubber · IntensitySparkline
    │   ├── panels/              HeaderBar · StormRail · IntelligencePanel
    │   ├── drawers/             EvidenceDrawer · AnaloguesDrawer
    │   └── viz/                 GradCamView · StructureMetrics · ShapBars
    │                            AnalogueOutcomeChart · VerificationReadout
    └── pages/                   CommandCenter.tsx · ModelCard.tsx
```

| Path | Responsibility | Belongs here | Does **not** belong here |
|---|---|---|---|
| `types/api.ts` | Mirror of the contract. `tsc -b` is the frontend's half of the drift check. | Interfaces matching `API_CONTRACT.md` exactly | Types the backend does not send; helper types (put those in `lib/`) |
| `api/` | Thin fetch wrappers, one file per resource | URL construction, the error envelope | Business logic, caching (that is TanStack Query's job) |
| `hooks/` | TanStack Query wrappers | Query keys, stale times, prefetch policy | Data transformation for display |
| `store/timeline.ts` | The **only** global state | `selectedSid`, `cursorTime`, `mode`, plus verify cursor/reveal | Anything else. A growing store means something is misplaced. |
| `lib/format.ts` | Unit formatting | `knots()`, `km()`, `kelvin()`, `percent()` | Anything that computes a result |
| `lib/provenance.ts` | Tag labels and descriptions | Display strings for the eight tags | Enforcement — that is the server's job |
| `components/ui/` | Reusable primitives | Generic, storm-agnostic components | Anything that knows about cyclones |
| `components/map/` | The MapLibre instance and its layers | Imperative layer updates | React state; the map owns its own |
| `components/map/layers/` | Source and layer manipulation | GeoJSON assembly, paint properties | Fetching |
| `components/viz/` | Evidence and analogue visualisations | Charts and readouts | Data fetching |
| `pages/` | Route-level composition | Wiring hooks to components | Presentational markup of any depth |

**Why the map is imperative.** MapLibre owns a WebGL canvas and its own layer graph.
Wrapping that in a declarative component tree buys little for the six layers needed and adds
a version-compatibility dependency. Confining it to `components/map/` is also what makes a
swap to React Leaflet a local change rather than a rewrite.

---

## `backend/` — runtime

```
backend/
├── pom.xml   mvnw   mvnw.cmd   .mvn/wrapper/
└── src/
    ├── main/java/com/cyclovision/
    │   ├── BackendApplication.java
    │   ├── domain/Provenance.java        the enum, mirrored from the contract
    │   ├── dto/                          Java records, 1:1 with API_CONTRACT.md
    │   ├── entity/                       JPA entities, 1:1 with tables
    │   ├── repository/                   7 Spring Data interfaces
    │   ├── service/                      StormService · ForecastService
    │   │                                 VerificationService · InferRequestBuilder
    │   │                                 ModelCardService · DemoFallbackService
    │   ├── client/                       AiServiceClient (+ its exception)
    │   ├── controller/                   4 controllers, 7 endpoints
    │   ├── config/                       Cors · WebClient · Media · OpenApi
    │   ├── exception/                    GlobalExceptionHandler · NotFoundException
    │   └── util/GeoUtil.java             haversine
    ├── main/resources/
    │   ├── application.yml               ports, datasource, timeouts
    │   ├── application-demo.yml          the demo profile
    │   └── db/migration/                 V1 schema · V2 indexes · V3 registry seed
    └── test/java/com/cyclovision/        6 test classes + TestFixtures
```

| Path | Responsibility | Belongs here | Does **not** belong here |
|---|---|---|---|
| `dto/` | Wire types as Java records | Nested records grouped by payload | Entities; never expose those directly |
| `entity/` | JPA mappings | Column mappings, JSONB as `String` with `@JdbcTypeCode` | Business logic, computed properties |
| `repository/` | Data access | Derived query methods | Any query that returns data later than a mask boundary, except in `VerificationService` |
| `service/InferRequestBuilder` | **Invariant I1.** Pure function (frames, asOf) → request. | The re-filter and the frame-reference selection | Repository or network access — it must stay unit-testable without a database |
| `service/VerificationService` | **Invariant I2.** The only place ground truth is read for scoring. | Error arithmetic, RI determination, cone containment | Anything sent to the AI service |
| `service/StormService` | The read path | Mapping `storm_frame` rows to DTOs, parsing `analysis_json` | Any AI service call (invariant I5) |
| `service/ForecastService` | Orchestration | Mask → cache → infer → persist → verify → degrade | Model logic |
| `client/AiServiceClient` | The single point of contact with FastAPI | Timeout, failure handling, health normalisation | Retries; a hanging demo is worse than a fast fallback |
| `config/MediaConfig` | Serves `/media/**` from `MEDIA_DIR` | The static resource handler | Image processing |
| `db/migration/` | The schema, owned by Flyway | New `V{n}__*.sql` files | Edits to already-applied migrations |

**Deliberately absent:** any ingestion code, any `@Scheduled` job, any alerts module, any
MapStruct mapper layer, any model loading.

---

## `ai-service/` — runtime

```
ai-service/
├── requirements.txt        RUNTIME ONLY — no training or netCDF dependencies
├── pytest.ini  .env.example
├── app/
│   ├── main.py             FastAPI app; lifespan calls registry.load_all()
│   ├── config.py           three paths and a version string
│   ├── registry.py         ★ the only constructor of a provenance stamp
│   ├── schemas/            common · frame · forecast · analogue · health
│   ├── routers/            health · full · frame · analogues
│   ├── structure/          polar.py · metrics.py · regime_rules.py
│   ├── inference/          base.py (protocols) · placeholders.py
│   ├── pipeline/           full_analysis.py — composes and stamps
│   ├── risk/rules.py       the weighted formula
│   ├── report/template.py  deterministic interpolation
│   └── io/bt_loader.py     path-guarded .npy loading
└── tests/                  6 test modules
```

| Path | Responsibility | Belongs here | Does **not** belong here |
|---|---|---|---|
| `registry.py` | **Invariant I3.** Every `Source` in the service is built here. | Registration, the downgrade rules, health reporting | Direct `Source(...)` construction anywhere else |
| `schemas/forecast.py` | **Invariant I1.** Carries the temporal-mask validator. | Request/response models mirroring the contract | Any field that could hold a future observation or ground truth |
| `structure/polar.py` | Cartesian → polar resampling | Bilinear sampling, background estimation | Metric definitions |
| `structure/metrics.py` | The seven measurements | Deterministic numpy over the BT field | Thresholds that produce a label |
| `structure/regime_rules.py` | The transparent classifier | Thresholds and `rulesApplied` | Any fitted parameter |
| `inference/base.py` | Model protocols | `FrameModel`, `IntensityChangeModel`, `TrackModel`, `AnalogueIndex` | Implementations |
| `inference/placeholders.py` | Phase 0 stand-ins | Persistence extrapolation and honest `None`s | Random or hardcoded plausible values |
| `pipeline/full_analysis.py` | Composition | The ten ordered steps and the stamping | Model internals |
| `io/bt_loader.py` | Reading Kelvin arrays | Path-traversal guard, shape validation | Writing anything |

**Deliberately absent:** a database connection, any downloader, any training loop, any
`verification` field.

**Files from spec-1.0 that do not exist yet, on purpose:**
`inference/ir_intensity.py`, `dvmax_ri.py`, `track_cliper.py`, `analogue_index.py`,
`gradcam.py`, `shap_explain.py`, `report/llm.py`. These are Phase 3 work; their interfaces
are already defined in `inference/base.py`. Creating them empty would be architecture
theatre.

---

## `ml/` — offline, never deployed

```
ml/
├── README.md  config.yaml  requirements-train.txt
├── ingest/       download_ibtracs · download_hursat · parse_hursat
│                 join_ibtracs_hursat · coastline_distance · render_frames
├── features/     structural · track_features · fusion · analogue_matrix
├── train/        splits · train_ir_intensity · train_dvmax_ri
│                 train_track_cliper · build_analogue_index
├── eval/         evaluate_all · ablation · cone_calibration
├── precompute/   precompute_frames
├── db/           write_to_postgres · seed_demo_scenarios
└── notebooks/    scratch (gitignored)
```

**Phase 0 state:** package structure and `config.yaml` exist; no scripts are implemented.
Phase 1 writes `ingest/`, Phase 2 exercises `features/`, Phase 3 writes `train/` and
`eval/`, Phase 4 writes `precompute/` and `db/`.

| Path | Responsibility | Belongs here | Does **not** belong here |
|---|---|---|---|
| `config.yaml` | The whole pipeline's configuration, reviewable in one place | Paths, basins, join tolerance, split seed, demo storms, model hyperparameters | Secrets |
| `ingest/` | Acquisition and the join | Download, parse, `(SID, ±90 min)` match, coastline distance, PNG/`.npy` render | Feature engineering |
| `features/` | Feature construction | Track features, fusion, the analogue matrix | The structural metrics themselves — those are imported from `ai-service` |
| `train/splits.py` | **Invariant I4.** Storm-wise splitting. | The split, and the assertion that demo storms are in `test` | Frame-wise splitting, ever |
| `eval/` | Honest measurement | Held-out metrics, the ablation, cone calibration → `models/metrics.json` | Anything that writes to the running services |
| `precompute/` | Filling `storm_frame.analysis_json` | Running the full pipeline once per frame | Live inference |
| `db/` | The only writer to `storm`, `storm_frame`, `model_registry` | Bulk upserts | Reads by the running services |

---

## `data/` — offline

```
data/
├── MANIFEST.md          COMMITTED — sources, licences, counts, match rate
├── raw/{ibtracs,hursat}/
├── interim/joined.parquet
├── processed/features.parquet · analogue_matrix.npz
├── frames/{sid}/{ts}.png     8-bit render, fixed 180–300 K scale
├── frames/{sid}/{ts}.npy     raw Kelvin — what the metrics measure
└── gradcam/{sid}/{ts}.png
```

Everything except `MANIFEST.md` is gitignored: large, and regenerable from the manifest.

**Both a PNG and an `.npy` per frame, deliberately.** Quantising to 8 bits for display
costs roughly half a Kelvin per level — enough to move the eye-contrast and CDO-fraction
thresholds. The metrics read the array; only the browser reads the picture.

## `models/`

```
models/
├── *.pt / *.json / *.npz    weights — gitignored
├── metrics.json             COMMITTED — drives the Model Card
└── model_card.md            COMMITTED — the human-readable version
```

`metrics.json` is written by `ml/eval/evaluate_all.py` and **never hand-edited**. The Model
Card is only as honest as this file.

## `scripts/`

| Script | Purpose |
|---|---|
| `dev-up.ps1` | PostGIS, then backend, AI service and frontend in their own windows |
| `dev-down.ps1` | Stops the database; `-Purge` also drops the volume |
| `test-all.ps1` | Every suite; `-WithDatabase` adds the PostGIS migration test |
| `demo-check.ps1` | Preflight. Run immediately before demonstrating, every time. |

PowerShell rather than bash because the Maven bash launcher fails on the development
machine (an apostrophe in the install path breaks the classworlds classpath). The Maven
Wrapper sidesteps it.

## `docs/`

One file per concern; `README.md` is the index. `docs/api/`, `docs/architecture/`,
`docs/database/` and `docs/development/` are legacy subdirectories containing pointer
READMEs to the current top-level documents.

---

## Files in spec-1.0 that do not exist yet

Recorded so the difference between "specified" and "built" stays visible.

| Specified | Status | Why |
|---|---|---|
| `ai-service/app/inference/{ir_intensity,dvmax_ri,track_cliper,analogue_index,gradcam,shap_explain}.py` | not created | Phase 3. Interfaces exist in `base.py`. |
| `ai-service/app/report/llm.py` | not created | Deferred — [`future-work.md`](future-work.md) |
| `frontend/src/theme/base.css` | merged | Folded into `tokens.css`; one file was enough |
| `frontend/src/components/map/layers/{forecastCone,analogueTracks,marker}.ts` | merged | All in `layers/track.ts`; splitting three small functions across files added nothing |
| `frontend/src/components/timeline/PlaybackControls.tsx` | merged | Three buttons, inlined in `TimelineScrubber` |
| `frontend/src/hooks/useModelCard.ts` | **added** | Needed by the Model Card page; not in the spec tree |
| `backend/.../ProvenanceTest.java`, `TestFixtures.java` | **added** | I3 coverage on the Java side and shared fixtures |
| root `db/`, root `tests/` | not created | Migrations live with the backend (Flyway convention); tests live with their service |
| `docs/decisions/ADR-*.md` | replaced | Single `docs/decisions.md` |
| `shared/` | should be deleted | Superseded by `API_CONTRACT.md` + `types/api.ts`. **Still present** — deletion was blocked in Phase 0 and needs a manual `rm -rf shared/`. |
| `frontend/dist/` | should be untracked | **Still tracked.** Needs a manual `git rm -r --cached frontend/dist`. |

Two further manual cleanups are outstanding: stale `__pycache__` directories under
`ai-service/app/{models,preprocessing,services}/` left by a pre-Phase-0 experiment.
