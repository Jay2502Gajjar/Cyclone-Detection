# CycloVision API contract

**Status: locked (spec-1.0).** Changes require agreement across all three services.

Three services are written against this contract in three languages. Nothing catches
drift automatically, so the contract is expressed **once**, as TypeScript, and the other
two mirror it:

| Language | File | Checked by |
|---|---|---|
| TypeScript (source of truth) | `frontend/src/types/api.ts` | `npm run build` (`tsc -b`) |
| Java | `backend/src/main/java/com/cyclovision/dto/*.java` | `ProvenanceTest`, `StormControllerTest` |
| Python | `ai-service/app/schemas/*.py` | `tests/test_contract_shapes.py` |

If you change a field, change all three and run all three suites.

---

## 1. Provenance

Every analysis block carries a `Source`. This is the mechanism by which nothing heuristic,
placeholder or untrained is ever presented as a trained model's output.

```ts
type Provenance =
  | 'OBSERVED'              // ground truth from a dataset; never a model output
  | 'TRAINED_MODEL'         // trained and evaluated on held-out storms
  | 'DERIVED_MEASUREMENT'   // deterministic physics over raw data; not fitted
  | 'STATISTICAL_BASELINE'  // from the empirical distribution of held-out errors
  | 'ANALOGUE_ENSEMBLE'     // empirical outcome distribution of retrieved analogues
  | 'RULE_ENGINE'           // transparent hand-written rules; thresholds shown
  | 'LLM_NARRATION'         // wording over computed values; originates no number
  | 'DEMO_DATA'             // placeholder; no trained model produced this

interface MetricInfo {
  name: string              // e.g. "MAE (kt)"
  value: number
  baseline?: string | null  // required for a TRAINED_MODEL claim to be auditable
  baselineValue?: number | null
  n?: number | null
}

interface Source {
  provenance: Provenance
  model?: string | null     // model_key
  version?: string | null
  isTrained?: boolean | null
  metric?: MetricInfo | null
}
```

Rules, enforced in code (see `docs/provenance.md`):

1. `TRAINED_MODEL` requires `isTrained: true` **and** a `metric` with its baseline.
   `ai-service/app/registry.py` downgrades any violation to `DEMO_DATA`; the database
   refuses the corresponding `model_registry` row; `Source.enforceTrainedFlag()` in Java
   applies the same rule again before anything reaches the browser.
2. `OBSERVED` originates only from `storm_frame` columns read by the backend.
3. Any block whose component cannot run on the given input is stamped `DEMO_DATA` and
   returns `null` values — **absent, never estimated**.

## 2. Errors

Every non-2xx response is an `ApiError`.

```ts
interface ApiError { code: string; message: string; detail?: string | null }
```

| Code | Status | Meaning |
|---|---|---|
| `STORM_NOT_FOUND` | 404 | No storm with that SID |
| `FRAME_NOT_FOUND` | 404 | No observation at that instant, or none at/before it |
| `AI_SERVICE_UNAVAILABLE` | 503 | AI service down and no cached or demo result exists |
| `TEMPORAL_MASK_VIOLATION` | 422 | History contained an observation later than `asOf` |
| `INVALID_TIME` | 400 | Not an ISO-8601 instant with offset |
| `MODEL_NOT_LOADED` | 404 | DEMO_MODE is on but no scenario exists |
| `INTERNAL_ERROR` | 500 | Unexpected |

---

## 3. React → Spring Boot

Seven endpoints. That is the entire public surface.

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | `HealthResponse` |
| GET | `/api/storms` | `StormSummary[]` |
| GET | `/api/storms/{sid}` | `StormDetail` |
| GET | `/api/storms/{sid}/frames/{isoTime}` | `FrameAnalysis` |
| POST | `/api/storms/{sid}/forecast?from={iso}&reveal={bool}` | `ForecastResponse` |
| GET | `/api/model-card` | `ModelCard` |
| POST | `/api/analyze/image` *(Phase 3)* | `FrameAnalysis` |

Satellite frames and Grad-CAM overlays are served as static files from `/media/**`.
Images are files; the database stores paths only.

### `GET /api/health`

```jsonc
{
  "status": "DEGRADED",              // UP only when the AI service has a trained model
  "aiService": {
    "status": "UP",
    "models": [
      { "key": "ir_intensity", "version": "phase0",
        "provenance": "DEMO_DATA", "isTrained": false }
    ]
  },
  "database": "UP",
  "demoMode": false,
  "bundleVersion": "phase0"
}
```

`DEGRADED` is the correct Phase 0 answer, not a failure.

### `GET /api/storms/{sid}`

Metadata plus the storm's **entire** frame index, in one response. This is deliberate:
the timeline scrubber reads this array on every drag, so scrubbing issues no network
request and triggers no inference. A few hundred thin frames is ~15 KB.

```jsonc
{
  "sid": "2019114N06084",
  "name": "FANI", "basin": "NI", "seasonYear": 2019,
  "startTime": "2019-04-26T00:00:00Z", "endTime": "2019-05-05T00:00:00Z",
  "peakVmaxKt": 135, "peakCategory": "EXTREMELY_SEVERE",
  "frameCount": 74, "framesWithImagery": 61,
  "isDemo": true, "split": "test",     // demo storms are ALWAYS held out
  "landfall": { "time": "2019-05-03T02:30:00Z", "lat": 19.8, "lon": 85.8,
                "place": "Puri, Odisha" },
  "frames": [
    { "t": "2019-05-02T06:00:00Z", "lat": 17.2, "lon": 85.1,
      "vmaxKt": 125, "pressureHpa": 936, "category": "EXTREMELY_SEVERE",
      "imageUrl": "/media/frames/2019114N06084/20190502T0600.png",
      "hasAnalysis": true,
      "cnnVmaxKt": 118,                // the dashed line on the sparkline
      "regime": "EYE" }
  ],
  "sources": {
    "track": { "provenance": "OBSERVED" },
    "cnnVmaxKt": { "provenance": "TRAINED_MODEL", "model": "ir_intensity",
                   "version": "v1.2", "isTrained": true },
    "regime": { "provenance": "RULE_ENGINE", "model": "regime_rules" }
  }
}
```

### `POST /api/storms/{sid}/forecast?from={iso}&reveal={bool}`

The one AI call. Everything the Command Center needs comes back here, including the
verification reveal, so the frontend never chases follow-up requests mid-demo.

`from` is the temporal-mask boundary **T**: only observations at or before it are used.
`reveal` controls whether ground truth is attached **afterwards**; it never changes what
the models were given.

```jsonc
{
  "sid": "2019114N06084",
  "issuedFor": "2019-05-02T06:00:00Z",
  "modelBundleVersion": "cv-2026.09.1",

  "current": {
    "lat": 17.2, "lon": 85.1, "vmaxKt": 125, "pressureHpa": 936,
    "category": "EXTREMELY_SEVERE", "distToCoastKm": 310,
    "source": { "provenance": "OBSERVED" }
  },

  "structure": {
    "regime": "EYE", "regimeLabel": "Eye pattern — well organised",
    "eyePresent": true, "eyeRadiusKm": 22, "eyeRingBtContrastK": 41.3,
    "minBtK": 191.4, "cdoFraction100km": 0.88, "axisymmetry": 0.89,
    "convectiveRingRadiusKm": 38, "coldCloudOffsetKm": 9,
    "rulesApplied": ["eyePresent == true", "axisymmetry (0.89) >= 0.70",
                     "coldCloudOffsetKm (9) < 40"],
    // Two stamps, not one: the measurements and the label built on them have
    // different standing and must not borrow each other's credibility.
    "metricsSource": { "provenance": "DERIVED_MEASUREMENT", "model": "structure" },
    "regimeSource": { "provenance": "RULE_ENGINE", "model": "regime_rules" }
  },

  "vision": {
    "vmaxKt": 118, "category": "EXTREMELY_SEVERE", "confidence": 0.81,
    "gradcamUrl": "/media/gradcam/2019114N06084/20190502T0600.png",
    "source": { "provenance": "TRAINED_MODEL", "model": "ir_intensity",
                "version": "v1.2", "isTrained": true,
                "metric": { "name": "MAE (kt)", "value": 12.4,
                            "baseline": "mean predictor", "baselineValue": 24.1,
                            "n": 1204 } }
  },

  "intensityForecast": {
    "deltaVmax24hKt": 8, "predictedVmax24hKt": 133,
    "trend": "INTENSIFYING", "confidence": 0.72,
    "riProbability": 0.34,
    "riBaseRate": 0.052,              // always travels with riProbability
    "topFactors": [
      { "feature": "axisymmetry", "shap": 0.31, "direction": "increases" },
      { "feature": "deltaVmax12h", "shap": 0.22, "direction": "increases" },
      { "feature": "distToCoastKm", "shap": -0.14, "direction": "decreases" }
    ],
    "source": { "provenance": "TRAINED_MODEL", "model": "dvmax_ri", "isTrained": true }
  },

  "trackForecast": {
    "points": [
      { "leadHours": 12, "lat": 18.1, "lon": 85.4,
        "coneRadiusP67Km": 58, "coneRadiusP90Km": 96, "predictedVmaxKt": 130 },
      { "leadHours": 24, "lat": 19.4, "lon": 85.7,
        "coneRadiusP67Km": 104, "coneRadiusP90Km": 178, "predictedVmaxKt": 133 },
      { "leadHours": 48, "lat": 22.6, "lon": 87.9,
        "coneRadiusP67Km": 231, "coneRadiusP90Km": 394, "predictedVmaxKt": 96 }
    ],
    "source": { "provenance": "TRAINED_MODEL", "model": "track_cliper" },
    // The cone is a percentile of the model's own held-out error, not a model output.
    "coneSource": { "provenance": "STATISTICAL_BASELINE", "model": "track_cone" },
    "coneBasis": "67th/90th percentile of held-out track error (n = 1,204 forecasts)"
  },

  "analogues": {
    "k": 20,
    "outcome": { "intensifiedCount": 14, "weakenedCount": 6,
                 "meanDeltaVmax24hKt": 16, "riCount": 5,
                 "riFraction": 0.25, "riBaseRate": 0.052 },
    "matches": [
      { "rank": 1, "sid": "1999293N09088", "name": "ODISHA",
        "time": "1999-10-27T06:00:00Z", "similarity": 0.94,
        "outcomeDeltaVmax24hKt": 25, "wasRi": true,
        "onwardTrack": [[17.9, 85.6], [19.1, 85.9]] }
    ],
    "exclusions": ["same-storm", "same-season"],
    "source": { "provenance": "ANALOGUE_ENSEMBLE", "model": "analogue" }
  },

  "risk": {
    "score": 0.78, "level": "HIGH",
    "formula": "0.35*vmaxNorm + 0.25*riProbability + 0.25*(1 - coastDistNorm) + 0.15*categoryNorm",
    "terms": { "vmaxNorm": 0.78, "riProbability": 0.34,
               "coastDistNorm": 0.39, "categoryNorm": 0.90 },
    "nearestCoast": "Odisha, India", "landfallWindowHours": 42,
    "source": { "provenance": "RULE_ENGINE", "model": "risk_rules" }
  },

  "report": {
    "text": "FANI is at 125 kt (extremely severe) at the selected time. …",
    "source": { "provenance": "RULE_ENGINE", "model": "report_template" }
  },

  // Assembled by Spring Boot from the database, AFTER inference returns.
  // The AI service has no field for this in either direction.
  "verification": {
    "available": true,
    "observedAt24h": { "t": "2019-05-03T06:00:00Z", "lat": 19.6, "lon": 85.8,
                       "vmaxKt": 135 },
    "observedAt48h": null,
    "trackErrorKm24h": 63, "trackErrorKm48h": null,
    "intensityErrorKt24h": 2,
    "insideConeP67": true, "insideConeP90": true,
    "riOccurred": false, "riWarningIssued": true,
    "source": { "provenance": "OBSERVED" }
  },

  "degraded": false,
  "servedFrom": "live"                // live | cache | demo
}
```

**Degradation.** If the AI service is unreachable, the backend returns the cached run for
`(sid, issuedFor)` — or a stored demo scenario — with `degraded: true` and
`servedFrom: "cache" | "demo"`. It never fabricates a forecast; with no fallback available
it returns `AI_SERVICE_UNAVAILABLE`.

### `GET /api/model-card`

Datasets with counts and match rates, the storm-wise split, every model with its held-out
metric and baseline, the multi-source ablation, cone calibration, and an explicit list of
what was **not** built and why. See `ModelCard` in `frontend/src/types/api.ts`.

---

## 4. Spring Boot → FastAPI (internal)

Never exposed publicly.

| Method | Path | Purpose |
|---|---|---|
| POST | `/infer/full` | The only call made in normal operation |
| POST | `/infer/frame` | One frame; used by the offline precompute job |
| POST | `/infer/analogues` | Standalone analogue query |
| GET | `/health` | Loaded components, versions, provenance, `isTrained` |

### `POST /infer/full`

```jsonc
{
  "sid": "2019114N06084",
  "asOf": "2019-05-02T06:00:00Z",
  "history": [                        // every t MUST be <= asOf
    { "t": "2019-05-01T06:00:00Z", "lat": 15.9, "lon": 84.6,
      "vmaxKt": 100, "pressureHpa": 960,
      "translationSpeedKt": 9, "headingDeg": 15, "distToCoastKm": 420 }
  ],
  "frameRef": { "btPath": "2019114N06084/20190502T0600.npy",
                "imageUrl": "/media/frames/2019114N06084/20190502T0600.png",
                "imageTime": "2019-05-02T05:45:00Z", "imageSource": "HURSAT-B1" },
  "options": { "analogueK": 20, "wantGradcam": true, "wantShap": true }
}
```

Response: `ForecastResponse` **minus** `verification`, `degraded` and `servedFrom`.

---

## 5. The two invariants this contract encodes

**I1 — temporal masking.** `InferFullRequest` has no field capable of carrying a future
observation, and its Pydantic validator rejects any `history[].t > asOf` with 422 rather
than silently dropping it. Spring Boot filters first (`InferRequestBuilder`); FastAPI
filters again. Two independent mistakes would be required to leak the future — and a leak
would not look like a bug, it would look like an unusually accurate model.

**I2 — verification is never round-tripped.** `InferFullResponse` has no `verification`
field. Ground truth is read from `storm_frame` by `VerificationService` after inference
has already returned. Both halves are asserted by tests in both languages.
