# ml/ — offline data engineering, training and precomputation

Everything heavy and offline lives here. This package **is not deployed**: it runs on a
laptop, writes to `data/`, `models/` and PostgreSQL, and then gets out of the way.

## Why this is separate from `ai-service/`

The deployed inference service loads weights and runs forward passes. It has no reason to
carry PyTorch's training stack, netCDF readers, plotting libraries or download clients —
so it doesn't. Keeping the two apart means the AI service boots fast, and the ML engineer
can iterate on training without restarting an API.

It also settles ownership of the data pipeline. Python owns **all** of it. The backend
never parses IBTrACS or HURSAT: doing it in Java would mean writing the same join twice,
in two languages, with two chances to disagree about what a match is.

## Boundaries

| This package may | This package may not |
|---|---|
| Download IBTrACS / HURSAT | Be imported by `ai-service` at request time |
| Join, engineer features, train, evaluate | Be deployed anywhere |
| Write `storm`, `storm_frame`, `model_registry` | Serve HTTP |
| Write `data/` and `models/` | Read from the running services |

One shared-code exception: `ml/features/structural.py` and
`ai-service/app/structure/metrics.py` must produce identical numbers, so there is only
one implementation. It lives in `ai-service/app/structure/`, and `ml/` imports it via the
path in `config.yaml`. Two copies of that code would drift, and a drift there would mean
the metrics a model trained on are not the metrics it is served.

## Pipeline order

```
download_ibtracs.py ─┐
                     ├─► join_ibtracs_hursat.py ─► coastline_distance.py ─► render_frames.py
download_hursat.py ──┘        (SID, |Δt| ≤ 90 min)
                                        │
                                        ▼
                     features/{structural, track_features, fusion}.py
                                        │
                     train/splits.py  ── STORM-WISE. Demo storms forced to 'test'.
                                        │
        ┌───────────────┬───────────────┼───────────────┬────────────────┐
   train_ir_       train_dvmax_    train_track_    build_analogue_
   intensity.py    ri.py           cliper.py       index.py
        └───────────────┴───────────────┼───────────────┴────────────────┘
                                        ▼
              eval/{evaluate_all, ablation, cone_calibration}.py
                        → models/metrics.json  (drives the Model Card)
                                        ▼
                     precompute/precompute_frames.py
                        → storm_frame.analysis_json, one row per frame
                                        ▼
                        db/write_to_postgres.py
```

## The rule that matters most

**Never train on a demo storm.** Rewind & Verify only means something if the model could
not have seen the storm it is being verified against. This is enforced in three places:

1. `train/splits.py` asserts it before writing a split.
2. The database rejects it: `CHECK (NOT is_demo OR split = 'test')`.
3. The Model Card reports `demoStormsInTest` on the page.

If verification results ever look suspiciously good, assume leakage and check before
believing them.

## Phase 0 status

Nothing here is implemented yet — by design. Phase 0 builds the runnable architecture;
Phase 1 writes `ingest/`, Phase 2 writes `train/` and `eval/`, Phase 3 writes
`precompute/`. Requirements are pinned now so the environment is ready.

## Running

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-train.txt
```
