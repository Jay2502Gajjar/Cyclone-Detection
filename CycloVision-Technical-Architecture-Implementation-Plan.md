# CycloVision — Technical Architecture \& Implementation Plan

### Tropical Cyclone Intelligence and Early Warning Platform

\---

## 1\. Executive Technical Summary

This document is the implementation-ready blueprint for **CycloVision**: a three-tier system (React frontend → Spring Boot orchestration layer → FastAPI ML service, backed by PostgreSQL/PostGIS) that ingests multi-source satellite and weather data, runs real trained models for detection/classification/prediction, and surfaces the results as a live command-center dashboard. Everything here is scoped for a 4-person team working a 24–36 hour hackathon window — no Kubernetes, no microservice sprawl, no infrastructure that can't be stood up and debugged live under time pressure. Every recommendation below states *why it's needed*, its *hackathon feasibility* (🟢🟡🔴), and whether it's **MVP**, **Enhanced**, or **Future Production**.

\---

## 2\. Final Architecture

```
                         ┌─────────────────────┐
                         │    React Frontend    │
                         │ React + Vite + TS    │
                         └──────────┬───────────┘
                                    │  REST (JSON) via Axios
                                    ▼
                         ┌─────────────────────┐
                         │     Spring Boot      │
                         │  Backend / API /     │
                         │  Orchestration       │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              │                     │                       │
              ▼                     ▼                       ▼
     ┌────────────────┐    ┌────────────────┐    ┌────────────────────┐
     │ PostgreSQL +    │    │ Python FastAPI │    │ External Data       │
     │ PostGIS         │    │ AI/ML Service  │    │ Sources (NOAA,      │
     │ (persistence +  │    │ (stateless      │    │ IBTrACS, OpenWeather)│
     │ geospatial)     │    │  inference)     │    │ pulled by a Spring  │
     └────────────────┘    └───────┬────────┘    │ scheduled job        │
                                    ▼             └────────────────────┘
                          ┌──────────────────┐
                          │  Trained ML       │
                          │  Models (ResNet,  │
                          │  XGBoost, Kalman, │
                          │  KNN) + LLM call   │
                          │  for report agent  │
                          └──────────────────┘
```

**One change from the original diagram:** external data sources are pulled *by Spring Boot* (a scheduled ingestion job) directly into PostgreSQL, not routed through FastAPI. FastAPI stays a pure, stateless inference service — it receives a feature payload and returns predictions, nothing else. This keeps the AI service simple, restartable, and easy to test in isolation, and keeps all persistence logic in one place (Spring Boot + Postgres).

### Layer Responsibilities

**Frontend (React):** dashboard, live map, satellite image visualization, charts, prediction visualization, risk alerts, historical comparison. Owns UI state only — no business logic, no direct DB or AI service calls (always through Spring Boot).

**Backend (Spring Boot):** REST API surface, orchestration between DB/AI service/external APIs, business logic (risk scoring rules, alert thresholds), prediction/result persistence, alert generation, retry/fallback logic when the AI service or external APIs are unavailable.

**AI/ML (FastAPI):** image preprocessing, cyclone detection, classification, trajectory prediction, intensity prediction, historical similarity, explainability generation (Grad-CAM, feature importance). Stateless — loads models once at boot, no DB connection.

**Database (PostgreSQL + PostGIS):** cyclone records, historical tracks, predictions, satellite metadata, risk zones, alerts, AI analysis results. All geospatial computation (buffers, intersections, distance) happens here via PostGIS functions, not in application code.

**Data Source Layer:** IBTrACS (historical bulk data, one-time import), OpenWeather (live numeric parameters, polled every few minutes), a small folder of pre-downloaded NOAA/INSAT satellite images (for both training and live demo selection). **Most realistic ingestion approach for a hackathon:** a Spring Boot `@Scheduled` job polling OpenWeather every 5 minutes + a one-time IBTrACS CSV import script run once at project setup — no real-time satellite feed integration (too heavy for 24–36 hours); satellite images are pre-selected from a curated folder per demo cyclone.

\---

## 3\. MVP Scope

### Feasibility check on the requested MVP list

All 8 requested MVP items are achievable **only if** trajectory prediction and historical similarity use the lightweight models specified below (Kalman+XGBoost, KNN) rather than deep sequence models. If time is tight, **cut satellite image analysis down to classification only** (skip real-time eye/center localization) and treat Grad-CAM as an Enhanced item, not MVP-blocking.

|#|Feature|Realistic for MVP?|Notes|
|-|-|-|-|
|1|Cyclone data ingestion|✅ Yes|IBTrACS import + OpenWeather polling + demo JSON fallback|
|2|Interactive cyclone map|✅ Yes|React Leaflet, well-documented, low risk|
|3|Satellite image analysis|✅ Yes (classification only)|Grad-CAM visualization → push to Enhanced if behind schedule|
|4|Cyclone classification|✅ Yes|Fusion of CNN embedding + numeric features|
|5|Trajectory prediction|✅ Yes|Kalman filter (6h/12h) + XGBoost (24h/48h)|
|6|Risk scoring|✅ Yes|Rule-based (see Part/Flow E)|
|7|Historical similarity|✅ Yes|KNN/cosine on precomputed IBTrACS feature vectors|
|8|AI-generated situation report|✅ Yes, but keep it P1 not P0|One LLM call over structured JSON — cut first if time runs out|

### MVP / Enhanced / Future split

**MVP (must build):** cyclone dashboard + map, satellite classification (no localization), multi-modal intensity classification, trajectory prediction with confidence corridor, rule-based risk scoring, historical similarity (top-3), core REST APIs, PostGIS schema populated.

**Enhanced (if time allows):** Grad-CAM explainability overlay, AI situation report (LLM), alerts panel, timeline scrubber on map, charts (wind/pressure/intensity trend over time).

**Future Production:** live multi-satellite ingestion, ensemble ML + physics-based NWP forecasting, mobile push alerts, population/exposure risk layers, automated retraining pipeline.

\---

## 4\. System Components

|Component|Technology|Deployment Unit|
|-|-|-|
|Web client|React + Vite + TS|Static build, served via Vercel|
|Orchestration API|Spring Boot|Single JVM process|
|ML inference service|FastAPI + PyTorch/XGBoost/scikit-learn|Single Python process|
|Data store|PostgreSQL + PostGIS extension|Single managed Postgres instance|
|Scheduled ingestion|Spring `@Scheduled` job (inside the same Spring Boot app — **not** a separate service)|Runs in-process|

Keeping ingestion inside the Spring Boot app (rather than a 5th microservice) avoids unnecessary deployment surface area — this is a deliberate hackathon simplification.

\---

## 5\. Frontend Architecture

### Folder Structure

```text
frontend/
├── src/
│   ├── api/                      # Axios instances + endpoint functions per domain
│   │   ├── client.ts              # base Axios instance, interceptors
│   │   ├── cyclones.ts
│   │   ├── predictions.ts
│   │   ├── satellite.ts
│   │   ├── risk.ts
│   │   ├── historical.ts
│   │   └── alerts.ts
│   ├── components/
│   │   ├── ui/                    # shadcn/ui primitives
│   │   ├── layout/                # Navbar, Sidebar, DashboardLayout
│   │   ├── dashboard/              # ActiveCyclonesCard, RiskOverview, AIInsightCard
│   │   ├── map/                    # CycloneMap, CycloneMarker, tracks, risk layers
│   │   ├── charts/                 # WindSpeedChart, PressureChart, etc. (Recharts)
│   │   └── cyclone/                 # CycloneDetailHeader, CycloneStatsPanel
│   ├── pages/                      # one file per route (see Pages below)
│   ├── hooks/                      # useCyclones, useCyclonePredictions, etc. (TanStack Query wrappers)
│   ├── types/                      # TS interfaces mirroring backend DTOs
│   ├── utils/                      # formatters, risk-color mapping, date helpers
│   ├── constants/                  # API base URL, risk level enums, map defaults
│   ├── routes/                     # React Router route definitions
│   ├── App.tsx
│   └── main.tsx
├── public/
└── package.json
```

### Pages

1. **Dashboard** — active cyclone cards, main map, stats, risk overview, AI insight card, alerts summary.
2. **Live Map** — full-screen map: current location, historical path, predicted trajectory, risk zones, landfall areas, layer toggle controls.
3. **Cyclone Details** — info header, wind/pressure/category stats, satellite image panel, historical timeline, AI predictions summary.
4. **AI Analysis** — satellite image, detection result, classification badge + confidence, Grad-CAM overlay (Enhanced).
5. **Prediction Page** — trajectory forecast table/map for 6/12/24/48h, intensity forecast chart.
6. **Historical Similarity Page** — current cyclone card, top-3 similar cyclone cards, comparison chart, overlayed historical tracks on a mini-map.
7. **Alerts Page** — active alerts list, risk level badges, recommended action text, affected region names.

### Component Architecture (expanded)

```text
components/
├── layout/
│   ├── Navbar.tsx                 # top nav: logo + route links
│   ├── Sidebar.tsx                 # optional secondary nav (can be skipped for MVP — top nav is enough)
│   └── DashboardLayout.tsx         # wraps pages, holds shared layout state (none needed beyond routing)
├── dashboard/
│   ├── ActiveCyclonesCard.tsx      # props: cyclone\[] → renders list of CycloneSummaryCard
│   ├── CycloneSummaryCard.tsx      # props: single cyclone summary → name/category/wind/risk badge
│   ├── RiskOverview.tsx            # props: riskLevel, riskScore → big colored gauge/badge
│   └── AIInsightCard.tsx           # props: insightText, confidence → highlighted callout
├── map/
│   ├── CycloneMap.tsx              # owns Leaflet map instance; props: activeCycloneId, layers toggle state
│   ├── CycloneMarker.tsx           # props: lat, long, animated: boolean
│   ├── HistoricalTrack.tsx         # props: trackPoints\[] → Polyline
│   ├── PredictedTrack.tsx          # props: predictedPoints\[] → dashed Polyline + confidence Polygon
│   └── RiskZoneLayer.tsx           # props: riskZones\[] (GeoJSON) → colored Polygons
├── charts/
│   ├── WindSpeedChart.tsx          # props: timeSeries\[] → Recharts LineChart
│   ├── PressureChart.tsx           # props: timeSeries\[]
│   └── IntensityForecastChart.tsx  # props: forecastPoints\[] → stepped/area chart
└── cyclone/
    ├── CycloneDetailHeader.tsx     # props: cyclone → name/category/basin
    └── CycloneStatsPanel.tsx       # props: latestObservation
```

**Data flow:** pages call custom hooks (`useActiveCyclones()`, `useCyclonePredictions(id)`) built on **TanStack Query**, which call the `api/` functions (Axios). Components receive data purely via props — no component reaches into a global store directly. This keeps every component testable and reusable.

### State Management Recommendation

* **Server state** (cyclone data, predictions, risk, alerts): **TanStack Query**. Handles caching, refetch-on-interval (for the 30–60s dashboard refresh), loading/error states — eliminates most manual state management.
* **UI state** (selected cyclone id, active map layers, sidebar open/closed): local `useState`/`useReducer` in the relevant page component, or a tiny **Zustand** store if it needs to be shared across 2+ unrelated components (e.g., "selected cyclone" needed by both the map and the details panel).
* **Global state**: avoid Redux Toolkit entirely — it's unnecessary ceremony for this scope. Zustand (if needed at all) covers every real global-state need here. 🟢 Easy, low risk.

\---

## 6\. Backend Architecture

### Package Structure

```text
backend/
└── src/main/java/com/cyclovision/
    ├── config/              # CORS, WebClient bean, Swagger/OpenAPI config
    ├── controller/          # REST controllers, one per module
    ├── service/             # business logic, one per module
    ├── repository/          # Spring Data JPA repositories
    ├── entity/              # JPA entities (map 1:1 to DB tables)
    ├── dto/                 # request/response DTOs (never expose entities directly)
    ├── mapper/              # entity ↔ DTO conversion (MapStruct or manual)
    ├── client/              # FastAPI WebClient wrapper, external API clients (OpenWeather)
    ├── scheduler/           # @Scheduled ingestion jobs
    ├── exception/           # GlobalExceptionHandler, custom exceptions
    └── util/                # constants, risk-scoring helper functions
```

### Modules

|Module|Controller|Service|Repository|Key DTOs|Main APIs|
|-|-|-|-|-|-|
|**Cyclone**|`CycloneController`|`CycloneService`|`CycloneRepository`, `CycloneObservationRepository`|`CycloneDto`, `CycloneObservationDto`|`GET /api/cyclones`, `GET /api/cyclones/active`, `GET /api/cyclones/{id}`|
|**Prediction**|`PredictionController`|`PredictionService` (calls AI client)|`PredictionRepository`, `PredictedTrackPointRepository`|`PredictionRequestDto`, `PredictionResponseDto`|`POST /api/cyclones/{id}/predict`, `GET /api/cyclones/{id}/predictions`|
|**Satellite**|`SatelliteController`|`SatelliteAnalysisService`|`SatelliteImageRepository`|`SatelliteAnalysisRequestDto/ResponseDto`|`POST /api/satellite/analyze`, `GET /api/satellite/{id}`|
|**Risk**|`RiskController`|`RiskScoringService`|`RiskAssessmentRepository`, `AlertRepository`|`RiskDto`, `AlertDto`|`GET /api/cyclones/{id}/risk`, `GET /api/alerts`|
|**Historical**|`HistoricalController`|`SimilarityService` (calls AI client)|`HistoricalCycloneRepository`, `SimilarityResultRepository`|`SimilarCycloneDto`|`GET /api/cyclones/{id}/similar`|
|**AI Integration**|*(no controller — internal client)*|`AiServiceClient`|—|`AiRequestDto/AiResponseDto` (shared across modules)|internal only|
|**Data Ingestion**|*(no controller — scheduled)*|`DataIngestionService`, `HistoricalImportService`|uses all repositories above|—|internal only, one manual `POST /api/admin/ingest/run` trigger for demo control|

Each business module's service calls `AiServiceClient` (a thin `WebClient` wrapper) rather than every service building its own HTTP call — this centralizes timeout/retry/fallback logic in one place (see Part 13).

\---

## 7\. AI/ML Architecture

### FastAPI Folder Structure

```text
ai-service/
├── app/
│   ├── api/                # route definitions, one file per capability
│   │   ├── detection.py
│   │   ├── classification.py
│   │   ├── trajectory.py
│   │   ├── intensity.py
│   │   ├── similarity.py
│   │   └── report.py
│   ├── models/              # model loading + inference wrappers (not the weights themselves)
│   │   ├── vision\_model.py    # ResNet load + Grad-CAM
│   │   ├── trajectory\_model.py # Kalman + XGBoost
│   │   ├── intensity\_model.py  # XGBoost
│   │   └── similarity\_model.py # KNN over precomputed embeddings
│   ├── services/            # orchestration logic per endpoint (calls models/, assembles response)
│   ├── preprocessing/        # image resize/normalize, numeric feature engineering
│   ├── schemas/              # Pydantic request/response models
│   ├── utils/                 # explainability helpers (Grad-CAM overlay rendering)
│   └── main.py                # FastAPI app, model loading at startup
├── trained\_models/            # .pt / .pkl weight files, loaded once at boot
├── data/                      # precomputed IBTrACS embedding table for similarity engine
├── requirements.txt
└── README.md
```

Models are loaded **once at startup** (in `main.py`'s lifespan handler), not per-request — critical for demo latency.

\---

## 8\. Database Architecture

### Tables

**cyclones**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Unique identifier|
|name|VARCHAR||Cyclone name|
|basin|VARCHAR||e.g. Bay of Bengal|
|season\_year|INT||Year|
|status|VARCHAR||active / dissipated / historical|
|created\_at|TIMESTAMP||Record creation|

**cyclone\_observations**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Observation id|
|cyclone\_id|UUID|FK → cyclones.id|Parent cyclone|
|observed\_at|TIMESTAMP||Time of reading|
|location|GEOGRAPHY(POINT,4326)|*PostGIS*|Lat/long|
|wind\_speed\_kmh|FLOAT||Sustained wind|
|pressure\_hpa|FLOAT||Central pressure|
|movement\_direction\_deg|FLOAT||Bearing|
|movement\_speed\_kmh|FLOAT||Forward speed|
|intensity\_category|VARCHAR||Category at this point|

**satellite\_images**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Image id|
|cyclone\_id|UUID|FK → cyclones.id|Parent cyclone|
|captured\_at|TIMESTAMP||Capture time|
|image\_type|VARCHAR||visible / infrared / water\_vapor|
|storage\_path|TEXT||File path/URL|
|source|VARCHAR||NOAA / INSAT / demo|

**weather\_observations**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Record id|
|cyclone\_id|UUID|FK (nullable)|Optional cyclone link|
|location|GEOGRAPHY(POINT,4326)|*PostGIS*|Reading location|
|sea\_surface\_temp\_c|FLOAT||SST feature|
|recorded\_at|TIMESTAMP||Time|
|source|VARCHAR||OpenWeather / Copernicus / demo|

**predictions**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Prediction run id|
|cyclone\_id|UUID|FK → cyclones.id|Parent cyclone|
|generated\_at|TIMESTAMP||When run|
|model\_version|VARCHAR||e.g. "xgb\_v1"|
|predicted\_intensity\_trend|VARCHAR||intensify/weaken/stable|
|confidence\_score|FLOAT||0–1|

**predicted\_track\_points**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Point id|
|prediction\_id|UUID|FK → predictions.id|Parent prediction run|
|forecast\_hour|INT||6/12/24/48|
|predicted\_location|GEOGRAPHY(POINT,4326)|*PostGIS*|Forecast position|
|confidence\_radius\_km|FLOAT||Corridor width|

**historical\_cyclones**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Historical cyclone id|
|name|VARCHAR||e.g. "Cyclone Fani"|
|year|INT||Year|
|final\_intensity|VARCHAR||Peak category|
|final\_landfall\_location|GEOGRAPHY(POINT,4326)|*PostGIS*|Landfall point|
|impact\_summary|TEXT||Short outcome text|
|feature\_vector|JSONB||Precomputed embedding for similarity search|

**historical\_track\_points**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Track point id|
|historical\_cyclone\_id|UUID|FK → historical\_cyclones.id|Parent historical cyclone|
|observed\_at|TIMESTAMP||Time|
|location|GEOGRAPHY(POINT,4326)|*PostGIS*|Position|
|wind\_speed\_kmh|FLOAT||Wind at this point|
|pressure\_hpa|FLOAT||Pressure at this point|

**similarity\_results**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Result id|
|cyclone\_id|UUID|FK → cyclones.id|Query cyclone|
|historical\_cyclone\_id|UUID|FK → historical\_cyclones.id|Matched cyclone|
|similarity\_score|FLOAT||Cosine similarity|
|rank|INT||1 = closest match|
|computed\_at|TIMESTAMP||Time|

**risk\_assessments**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Assessment id|
|cyclone\_id|UUID|FK → cyclones.id|Parent cyclone|
|risk\_zone\_geometry|GEOGRAPHY(POLYGON,4326)|*PostGIS*|Risk zone shape|
|risk\_level|VARCHAR||Low/Moderate/High/Critical|
|risk\_score|FLOAT||0–1 numeric score|
|computed\_at|TIMESTAMP||Time|

**alerts**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Alert id|
|cyclone\_id|UUID|FK → cyclones.id|Parent cyclone|
|risk\_assessment\_id|UUID|FK → risk\_assessments.id|Related assessment|
|message|TEXT||Alert text|
|severity|VARCHAR||Info/Watch/Warning/Critical|
|issued\_at|TIMESTAMP||Time issued|

**ai\_analysis\_results**

|Column|Type|Key|Purpose|
|-|-|-|-|
|id|UUID|PK|Result id|
|cyclone\_id|UUID|FK → cyclones.id|Parent cyclone|
|model\_name|VARCHAR||e.g. "resnet\_vision\_v1"|
|result\_json|JSONB||Full structured output|
|confidence\_score|FLOAT||Confidence|
|explainability\_payload|JSONB||Grad-CAM path, feature importances|
|generated\_at|TIMESTAMP||Time|

### Indexes

* GiST index on every `GEOGRAPHY`/`GEOMETRY` column (PostGIS requires this for performant spatial queries): `CREATE INDEX ON cyclone\_observations USING GIST (location);` (repeat per geography column).
* B-tree index on all `cyclone\_id` foreign keys (fast joins for the dashboard's "get everything for this cyclone" queries).
* Composite index on `(cyclone\_id, observed\_at DESC)` on `cyclone\_observations` for "latest observation" lookups.

### ER Relationship Diagram (text)

```text
Cyclone
   │
   ├──── CycloneObservation (many)
   │
   ├──── SatelliteImage (many)
   │
   ├──── WeatherObservation (many, optional link)
   │
   ├──── Prediction (many)
   │        │
   │        └──── PredictedTrackPoint (many per prediction)
   │
   ├──── SimilarityResult (many) ──→ HistoricalCyclone
   │                                       │
   │                                       └──── HistoricalTrackPoint (many)
   │
   ├──── RiskAssessment (many)
   │        │
   │        └──── Alert (many)
   │
   └──── AiAnalysisResult (many)
```

\---

## 9\. API Design

### Cyclones

**`GET /api/cyclones`** → all cyclones (active + historical), no params.
**`GET /api/cyclones/active`** → active cyclones with latest observation embedded.

```json
\[{
  "id": "c1a2...", "name": "Cyclone Biparjoy", "basin": "Arabian Sea",
  "latestObservation": {"lat": 18.4, "long": 68.2, "windSpeedKmh": 140, "pressureHpa": 960, "intensityCategory": "Very Severe Cyclonic Storm"}
}]
```

**`GET /api/cyclones/{id}`** → full detail including recent observation history.
**`GET /api/cyclones/{id}/observations`** → time-series of observations (used by charts).

### Satellite

**`POST /api/satellite/analyze`**
Request:

```json
{"cycloneId": "c1a2...", "imageId": "img-88"}
```

Response:

```json
{
  "cycloneDetected": true, "eyeFormed": true, "structureScore": 0.87,
  "classification": "Very Severe Cyclonic Storm", "confidence": 0.91,
  "gradcamImageUrl": "/media/gradcam/img-88.png"
}
```

**`GET /api/satellite/{id}`** → stored analysis result by satellite image id.

### Predictions

**`POST /api/cyclones/{id}/predict`** → triggers full pipeline run (calls FastAPI internally). No body needed; uses latest stored observation.
**`GET /api/cyclones/{id}/predictions`**

```json
{
  "cycloneId": "c1a2...",
  "trajectory": \[
    {"forecastHour": 6, "lat": 18.6, "long": 68.5, "confidenceRadiusKm": 45},
    {"forecastHour": 24, "lat": 19.4, "long": 69.8, "confidenceRadiusKm": 140}
  ],
  "intensityTrend": {"prediction": "intensify", "confidence": 0.78,
    "explanation": "Sea surface temperature is above 29°C and pressure is dropping steadily."}
}
```

### Risk

**`GET /api/cyclones/{id}/risk`**

```json
{"riskLevel": "High", "riskScore": 0.74, "atRiskRegions": \["Kutch coast", "Saurashtra coast"], "landfallProbability48h": 0.62}
```

### Historical Similarity

**`GET /api/cyclones/{id}/similar`**

```json
\[{"name": "Cyclone Fani (2019)", "similarityScore": 0.91, "finalIntensity": "Extremely Severe Cyclonic Storm", "landfall": "Odisha, India", "impactSummary": "Category-4 equivalent landfall, \~1.2M evacuated."}]
```

### Alerts

**`GET /api/alerts`**

```json
\[{"cycloneName": "Cyclone Biparjoy", "severity": "Warning", "message": "High risk of landfall near Kutch coast within 48 hours."}]
```

\---

## 10\. Data Flow

### FLOW A — User Opens Dashboard

```
User opens app
 → React: GET /api/cyclones/active (via TanStack Query, on mount + 60s interval)
 → Spring Boot CycloneController → CycloneService → CycloneRepository
 → PostgreSQL returns active cyclones + latest observation (single JOIN query)
 → Spring Boot maps entities → CycloneDto → JSON response
 → React renders ActiveCyclonesCard grid + initializes CycloneMap with first cyclone's location
```

### FLOW B — Satellite Image Analysis

```
User selects a cyclone → clicks "Run AI Analysis" on a pre-loaded satellite image
 → React: POST /api/satellite/analyze  { cycloneId, imageId }
 → Spring Boot SatelliteController → SatelliteAnalysisService
     → fetches image storage\_path from PostgreSQL
     → AiServiceClient: POST http://ai-service/detect-classify  { imageUrl, cycloneId }
 → FastAPI: preprocessing.load\_and\_normalize(image)
     → vision\_model.detect(image) → structure score, eye/boundary flags
     → vision\_model.classify(embedding + numeric features) → category + confidence
     → utils.generate\_gradcam(image, model) → heatmap PNG saved to /media
     → returns JSON { cycloneDetected, eyeFormed, structureScore, classification, confidence, gradcamImageUrl }
 → Spring Boot persists result into ai\_analysis\_results (result\_json + explainability\_payload)
 → Spring Boot returns response to React
 → React renders classification badge, confidence, and Grad-CAM overlay image
```

**Storage strategy:** satellite images themselves live as static files (pre-loaded demo folder, served via a simple static path or a small object-storage bucket if deployed); only the `storage\_path`/URL is stored in Postgres — never store binary image blobs in the DB.

### FLOW C — Trajectory Prediction

```
User clicks "Predict" on Cyclone Details page
 → React: POST /api/cyclones/{id}/predict
 → Spring Boot PredictionController → PredictionService
     → fetches last N observations from cyclone\_observations (PostgreSQL)
     → AiServiceClient: POST http://ai-service/predict-trajectory { recentObservations\[] }
 → FastAPI: trajectory\_model.kalman\_filter(recentObservations) → 6h/12h estimate
            trajectory\_model.xgboost\_forecast(features) → 24h/48h estimate
            intensity\_model.predict(features) → intensify/weaken/stable + confidence
 → FastAPI returns { trajectory: \[...], intensityTrend: {...} }
 → Spring Boot: creates a `predictions` row + N `predicted\_track\_points` rows
 → Spring Boot returns response to React
 → React updates CycloneMap with PredictedTrack + confidence corridor polygon, and IntensityForecastChart
```

### FLOW D — Historical Similarity Analysis

```
Current cyclone's latest feature vector (built by Spring Boot from cyclone\_observations + latest ai\_analysis\_results)
 → Spring Boot: POST http://ai-service/similar-cyclones { featureVector }
 → FastAPI: similarity\_model.knn\_search(featureVector, precomputed\_ibtracs\_embeddings) → top 5 (lib: scikit-learn NearestNeighbors, precomputed at startup from /data)
 → FastAPI returns \[{ historicalCycloneId, similarityScore }, ...]
 → Spring Boot: joins against historical\_cyclones table for name/landfall/impact\_summary, persists into similarity\_results
 → Spring Boot returns enriched JSON to React
 → React renders similarity cards + overlays selected historical track on the map
```

**Simplest practical implementation:** precompute the historical embedding table **once** at AI service startup (or as a one-time offline script writing to `/data/historical\_embeddings.pkl`), then do a fast in-memory KNN lookup per request — no need to hit the database from FastAPI at all for this.

### FLOW E — Risk Calculation

**Recommendation: rule-based scoring for the MVP.** A weighted formula over already-computed factors is fast, fully explainable in a live demo ("here's exactly why it's High risk"), and requires no additional training data or model — a real ML risk model would need labeled historical outcome data mapped to a discrete risk scale, which doesn't cleanly exist in IBTrACS and isn't worth building given the time budget.

```
riskScore = 0.35 \* normalizedWindSpeed
          + 0.25 \* normalizedIntensityCategory
          + 0.25 \* (1 - normalizedDistanceToCoast)     # closer = higher risk
          + 0.15 \* predictionConfidence
riskLevel = Critical if riskScore > 0.8
          = High     if riskScore > 0.6
          = Moderate if riskScore > 0.35
          = Low      otherwise
```

`normalizedDistanceToCoast` comes from a single PostGIS `ST\_Distance` call between the predicted 48h track point and a coastline layer. This entire computation can live in `RiskScoringService` as a plain Java method — 🟢 easy, no ML needed.
**Hybrid approach (Enhanced, not MVP):** once the rule-based version works, optionally feed the same inputs into a simple logistic regression trained on IBTrACS "did this cyclone cause reported major damage" labels, and show both scores side by side as a "confidence-boosting" hybrid — good stretch goal, not required.

\---

## 11\. Data Ingestion

```
External Data Source (IBTrACS CSV / OpenWeather API)
        ↓
Data Fetcher (Spring @Scheduled job, or a one-time import CLI runner for IBTrACS)
        ↓
Data Validator (null checks, range checks: wind speed 0–350 km/h, valid lat/long)
        ↓
Data Transformer (unit conversion, mapping to entity fields)
        ↓
PostgreSQL (JPA repository save)
        ↓
Available to AI Pipeline via Spring Boot's feature-assembly step in PredictionService
```

* **Historical ingestion:** one-time import script/CLI runner reading the IBTrACS CSV and bulk-inserting into `historical\_cyclones` + `historical\_track\_points`. Run this once at project setup (Phase 0/1), not repeatedly.
* **Live ingestion:** `@Scheduled(fixedRate = 300000)` job polling OpenWeather for a small fixed set of demo coordinates (Bay of Bengal, Arabian Sea) every 5 minutes, writing into `weather\_observations`.
* **Satellite image ingestion:** manual — a curated folder of pre-downloaded images per demo cyclone scenario, referenced by `storage\_path`; no live satellite feed integration for MVP. 🟢 Easy, avoids a genuinely hard integration (satellite APIs are slow/rate-limited/require registration).
* **Demo fallback data:** a `demo-scenarios.json` bundled with the backend, loaded via a `POST /api/admin/ingest/run?mode=demo` trigger if live APIs are unreachable — this is the single most important reliability feature in the whole system; test it explicitly before the demo.

\---

## 12\. AI Models

|Feature|Production Model|Hackathon MVP Model|Input|Output|Training Data|Difficulty|Why|
|-|-|-|-|-|-|-|-|
|Cyclone detection|ViT / EfficientNet + localization head|**ResNet-18/34 (transfer learning)**|Satellite image|detected: bool, structure score|Small labeled satellite image set (NOAA/Kaggle)|🟡 Medium|Transfer learning gets strong accuracy fast with limited data/time|
|Cyclone classification|EfficientNet + attention fusion|**CNN embedding + numeric features → dense classifier**|Image + wind/pressure|1 of 6 IMD categories|Same image set + IBTrACS numeric pairing|🟡 Medium|Multi-modal beats either signal alone, still simple to implement|
|Trajectory prediction|LSTM/Transformer seq2seq ensemble|**Kalman Filter (6/12h) + XGBoost (24/48h)**|Recent observations (lag features)|Future lat/long per horizon|IBTrACS|🟢 Easy|No large training set or GPU needed, fully explainable|
|Intensity prediction|Multi-task deep net w/ reanalysis data|**XGBoost classifier**|Wind/pressure trend, SST, latitude|intensify/weaken/stable + confidence|IBTrACS + SST data|🟢 Easy|Tabular, fast, gives feature importance for free|
|Historical similarity|Learned embedding + FAISS ANN search|**KNN + cosine similarity (scikit-learn)**|Feature vector|Top-5 historical matches|Precomputed IBTrACS embeddings|🟢 Easy|Trivial to implement, very high demo impact|
|Explainable AI|SHAP + Grad-CAM + counterfactuals|**Confidence scores + XGBoost feature importance + Grad-CAM**|Model outputs|Explanation payload|N/A (post-hoc on trained models)|🟡 Medium (Grad-CAM setup)|Covers the highest-impact explainability for the effort required|

\---

## 13\. AI Agents

**Are agents necessary? Yes — minimally, for orchestration/reporting only, never for scientific prediction.** An LLM must never generate a wind speed, trajectory point, or risk score itself; it only narrates results that the ML models already computed.

|Agent|Necessary?|Input|Output|Tools|
|-|-|-|-|-|
|**Situation Report Agent**|✅ Yes — highest demo value per unit effort|Cyclone data, prediction data, risk level (all from Spring Boot's assembled JSON)|Human-readable paragraph report|One LLM API call, plain prompt template|
|**Data Intelligence Agent**|⚠️ Optional — cut unless ahead of schedule|Ingested data across sources|Data quality/anomaly summary|Could just be a rule-based validator (see Data Validator in Part 11) instead of an LLM — **recommend implementing this as plain code, not an "agent"**|
|**Decision Support Agent**|⚠️ Optional — mostly redundant with the rule-based Risk Engine|Predictions + risk assessment|Recommended warning level|The rule-based `RiskScoringService` (Part 10, Flow E) already does this — don't duplicate it with an LLM agent|

**Recommendation:** build exactly **one** agent — the Situation Report Agent — as a single, well-crafted prompt call inside FastAPI's `report.py`, fed the already-computed structured results. Skip the Data Intelligence and Decision Support agents entirely; their jobs are better (and more reliably) done as plain deterministic code, which is also faster to build and impossible to hallucinate.

**Framework: custom, no LangGraph/LangChain/CrewAI.** A single LLM call wrapped in a Python function has zero orchestration complexity — a framework would add setup and debugging risk for literally one call. 🟢 Easy, lowest risk, still demonstrates "real AI reasoning" to judges in the pitch.

\---

## 14\. Implementation Phases

**Phase 0 — Project Setup**

1. Create GitHub repo (`main` + `develop` branches, see Part Git Strategy).
2. Scaffold frontend (`npm create vite@latest -- --template react-ts`, install Tailwind, shadcn/ui, React Router, Axios, React Leaflet, Recharts, Lucide).
3. Scaffold backend (Spring Initializr: Web, Data JPA, Validation, PostgreSQL driver).
4. Scaffold AI service (`fastapi`, `uvicorn`, `torch`, `scikit-learn`, `xgboost`, `opencv-python`, `pandas`, `numpy`).
5. Provision PostgreSQL with PostGIS extension enabled (`CREATE EXTENSION postgis;`).
6. Set all environment variables (Part 19) in `.env` files, add to `.gitignore`.

**Phase 1 — Core Backend:** entities, repositories, services, controllers for the Cyclone module first (it's the foundation every other module reads from), then Prediction/Satellite/Risk/Historical module skeletons (even with stub responses) so the frontend team is unblocked.

**Phase 2 — Data Ingestion:** IBTrACS historical import script, demo active-cyclone JSON seeding, OpenWeather scheduled job.

**Phase 3 — Frontend Foundation:** layout, routing, Dashboard page wired to real `GET /api/cyclones/active`.

**Phase 4 — Interactive Map:** Leaflet integration, markers, historical/predicted tracks, risk zone layer (can use stub/mock geometry until Phase 7 risk engine is real).

**Phase 5 — AI/ML:** preprocessing, detection/classification model training+wrapping, trajectory model, similarity engine — all built and tested standalone via FastAPI's auto-generated `/docs` (Swagger UI) before wiring to Spring Boot.

**Phase 6 — AI Integration:** connect React → Spring Boot → FastAPI end-to-end for each of the three flows (B, C, D). Test with real demo data, not just unit stubs.

**Phase 7 — Risk \& Alert System:** implement `RiskScoringService` rule-based formula, alert generation, wire risk zones into the map.

**Phase 8 — WOW Features (only after core system works):** Grad-CAM, AI Situation Report, confidence corridor polish.

**Phase 9 — Testing:** run through every flow with network disabled to confirm demo-mode fallback actually works; test with at least 2 different demo cyclone scenarios.

**Phase 10 — Demo Preparation:** finalize the 2–3 demo scenarios, take backup screenshots of every screen (in case of live failure), rehearse the pitch script.

\---

## 15\. Team Task Distribution

**Team of 4.**

|Team Member|Responsible For|Depends On|Can Start Immediately?|
|-|-|-|-|
|**1 — Frontend**|React setup, layout/routing, Dashboard/Map/Details/Analysis/Prediction/Historical/Alerts pages, all charts|API contracts (Part 9) agreed at Hour 0 — otherwise works against mocked JSON|✅ Yes, with mocked data|
|**2 — Backend**|Spring Boot setup, DB schema + entities, all module controllers/services/repositories, AiServiceClient, scheduled ingestion, risk scoring|DB schema (self-owned), AI service's request/response contract (agree at Hour 0)|✅ Yes|
|**3 — AI/ML**|FastAPI setup, preprocessing, vision/trajectory/intensity/similarity models, Grad-CAM, situation report agent|Data availability (Team Member 4's IBTrACS + image prep)|⚠️ Needs data first — start on model *code* immediately using a tiny synthetic sample while waiting|
|**4 — Data/Integration**|Download \& clean IBTrACS, curate demo satellite images, build demo-scenario JSONs, OpenWeather integration testing, end-to-end integration testing across all three services|Nothing — start first|✅ Yes, start at Hour 0, this is the critical path|

### Parallel tasks

Frontend (mocked data) + Backend (schema/API skeleton) + Data prep can all run fully in parallel from Hour 0. AI/ML can start model architecture/code in parallel but is blocked on **real** training until Data delivers the cleaned dataset (target: by Hour 4).

### Dependencies

* Backend's `AiServiceClient` needs the FastAPI request/response shape agreed *before* either side writes code — lock this contract at Hour 0–1 (see Part 9's JSON examples as the starting contract).
* Frontend's map/charts need Backend's DTO shapes — same Hour 0–1 lock.
* AI/ML's models need Data's cleaned IBTrACS + images — target delivery Hour 4.

### Integration checkpoints

* **Hour 6:** Backend serves real (not mock) `GET /api/cyclones/active` from seeded demo data; Frontend switches from mocks to this real endpoint.
* **Hour 14:** First full round-trip of Flow B (satellite analysis) works end-to-end, even with a placeholder/undertrained model.
* **Hour 20:** All three flows (B, C, D) work end-to-end with real trained models and real demo data.

\---

## 16\. Git Strategy

```text
main        → always deployable/demo-ready
develop     → integration branch, merge target for all features
feature/frontend-dashboard
feature/frontend-map
feature/backend-cyclone-api
feature/backend-risk-engine
feature/ai-vision-model
feature/ai-trajectory-model
feature/data-ingestion
```

* All work happens on `feature/\*` branches off `develop`.
* Pull requests merge into `develop`; **only** merge `develop` → `main` right before demo checkpoints (Hour 6/14/20 above) and just before the final presentation.
* **Merge rule:** at least one other teammate reviews before merging (even a 2-minute glance) — catches integration-breaking changes before they hit `develop`.
* **Avoiding conflicts:** since each person owns a distinct folder (frontend/ vs backend/ vs ai-service/), true merge conflicts should be rare — the main risk is *contract drift* (DTO shape changes), which the Hour 0–1 contract lock and Hour 6/14/20 checkpoints are designed to catch early.

\---

## 17\. Environment Variables

**Frontend (`.env`):**

```text
VITE\_API\_BASE\_URL=http://localhost:8080
```

**Backend (`application.yml` / env):**

```text
SPRING\_DATASOURCE\_URL=jdbc:postgresql://localhost:5432/cyclovision
SPRING\_DATASOURCE\_USERNAME=postgres
SPRING\_DATASOURCE\_PASSWORD=changeme
AI\_SERVICE\_URL=http://localhost:8000
OPENWEATHER\_API\_KEY=your\_key\_here
DEMO\_MODE=false
```

**AI service (`.env`):**

```text
MODEL\_PATH=./trained\_models
DATA\_PATH=./data
LLM\_API\_KEY=your\_key\_here
```

`DEMO\_MODE` in the backend is the single flag that forces every external call (OpenWeather, AI service) to fall back to bundled demo data instead of failing — flip it to `true` right before the live demo as insurance.

\---

## 18\. Docker Strategy

**Is Docker necessary? Only for Postgres/PostGIS — optional for everything else.** Standing up PostGIS locally without Docker is the single most error-prone setup step (extension installation varies wildly by OS); everything else (Node, Java, Python) is fast to run natively and easier to debug/hot-reload without a container layer during active development.

**Minimum Docker setup (recommended):**

```yaml
# docker-compose.yml — Postgres/PostGIS only
services:
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES\_DB: cyclovision
      POSTGRES\_USER: postgres
      POSTGRES\_PASSWORD: changeme
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

Run `docker compose up -d postgres` once at Phase 0 and leave it running — everyone points their local backend at it.

**Optional Docker setup (only if deploying containerized, or if a teammate's machine has native install issues):** add `frontend`, `backend`, `ai-service` services to the same compose file, each with a simple `Dockerfile`. Don't build this unless native setup is actively failing for someone — it adds build-time overhead you don't need during rapid iteration.

\---

## 19\. Deployment

|Layer|Best Easy Option|Notes|
|-|-|-|
|Frontend|**Vercel**|Zero-config for Vite, instant preview URLs per push|
|Backend|**Render** (or Railway)|Both support Java/Spring Boot Docker deploys with minimal config|
|AI Service|**Render** (or Railway)|Python/FastAPI supported natively|
|Database|**Neon** or **Supabase**|Both offer managed Postgres **with PostGIS enabled** — confirm the extension is enabled in project settings before relying on it|

**Best easy deployment:** Vercel (frontend) + Render (backend + AI service, two separate Render web services) + Neon (Postgres with PostGIS). All four have generous free tiers sufficient for a hackathon demo.
**Backup deployment strategy:** if any cloud deploy breaks near the deadline, fall back immediately to running all four locally (`docker compose up` for Postgres, `mvn spring-boot:run`, `uvicorn app.main:app`, `npm run dev`) and demo from a laptop — judges care about the working product, not the URL.
**Local demo fallback:** always have this local setup tested and ready *before* the demo slot, regardless of whether cloud deployment succeeds — treat cloud deployment as a bonus, not a dependency.

\---

## 20\. Testing

|Layer|Minimum Hackathon Testing|
|-|-|
|Frontend|Manual click-through of every page + every button before demo; skip automated component tests unless far ahead of schedule|
|Backend|Manual Postman/Swagger testing of every endpoint with real and edge-case inputs (missing cyclone id, AI service down); a handful of `@SpringBootTest` service-layer tests only if time allows|
|AI|Test each model function directly in a Jupyter/script before wrapping in FastAPI; use FastAPI's `/docs` Swagger UI to manually test each endpoint in isolation|
|Integration|Full run-through of Flows A–E with `DEMO\_MODE=true` **and** `DEMO\_MODE=false`/network disabled — this single test matters more than any unit test suite|

🟢 Recommendation: skip formal test suites entirely for this timeframe; invest that time in manual end-to-end run-throughs instead — for a 24–36 hour hackathon, a live rehearsal catches more real bugs than unit tests will.

\---

## 21\. Hackathon Timeline

### 24-Hour Plan

|Hours|Frontend|Backend|AI/ML|Data|Integration|
|-|-|-|-|-|-|
|0–2|Scaffold app, install deps, lock API contract|Scaffold app, DB schema draft, lock API contract|Scaffold FastAPI, lock request/response contract|Start IBTrACS download + cleaning|Contract doc agreed by all 4|
|2–6|Dashboard UI with mocked data|Cyclone module (entities/repo/service/controller) real|Preprocessing pipeline + baseline ResNet training starts|Deliver cleaned IBTrACS + sample images|**Checkpoint:** Backend serves real active-cyclone data|
|6–12|Map integration, wire Dashboard to real API|Prediction/Satellite/Risk module skeletons + real Cyclone endpoints|Finish vision model, start trajectory (Kalman+XGBoost)|Build demo-scenario JSONs, precompute similarity embeddings|Frontend fully on real API for Dashboard+Map|
|12–18|Cyclone Details, AI Analysis, Prediction pages|Wire AiServiceClient, persist predictions/analysis results|Finish trajectory + intensity models, wrap in FastAPI endpoints|Support AI team with data format issues, start integration testing|**Checkpoint:** Flow B (satellite) works end-to-end|
|18–24|Historical Similarity + Alerts pages, polish/styling|Risk scoring, alert generation, error handling/fallbacks|Similarity engine, Grad-CAM if time allows|Full demo scenario rehearsal, screenshot backups|**Checkpoint:** All flows working, demo-mode tested|

### 36-Hour Plan

Same as the 24-hour plan through Hour 24, then:

|Hours|Focus|
|-|-|
|24–28|AI Situation Report agent (LLM call), Historical Time Machine map overlay|
|28–32|Grad-CAM polish (if not done), confidence corridor visual polish, charts (wind/pressure/intensity)|
|32–36|Full rehearsal, pitch deck, bug bash, buffer time for anything broken|

**Critical milestones (both plans):** Hour 6 (real dashboard data), Hour 14–18 (first full AI flow works), final hours (demo-mode fallback verified + rehearsal done).

\---

## 22\. Priority Matrix

|Feature|Priority|Difficulty|Demo Impact|
|-|-|-|-|
|Dashboard + active cyclone cards|P0|🟢 Easy|High|
|Interactive map (current + historical track)|P0|🟢 Easy|High|
|Satellite classification (no localization)|P0|🟡 Medium|High|
|Trajectory prediction (Kalman+XGBoost) + confidence corridor|P0|🟢 Easy|Very High|
|Rule-based risk scoring + color-coded levels|P0|🟢 Easy|High|
|Historical similarity engine (KNN)|P0|🟢 Easy|**Very High (biggest differentiator)**|
|Core REST API layer|P0|🟢 Easy|N/A (foundation)|
|Demo-mode fallback data|P0|🟢 Easy|Critical (invisible but demo-saving)|
|Grad-CAM explainability overlay|P1|🟡 Medium|Very High|
|AI Situation Report (LLM)|P1|🟢 Easy|High|
|Alerts page|P1|🟢 Easy|Medium|
|Charts (wind/pressure/intensity trend)|P1|🟢 Easy|Medium|
|Timeline scrubber on map|P2|🟡 Medium|Medium|
|What-If Simulation slider|P2|🟡 Medium|Medium-High|
|Cyclone eye/center localization (YOLO)|P3|🔴 Hard|Medium|
|Ensemble/physics-based forecasting|P3|🔴 Hard|Low (invisible to judges)|
|Live multi-satellite ingestion|P3|🔴 Hard|Low (not demo-visible)|

\---

## 23\. Risks and Mitigation

|Risk|Likelihood|Mitigation|
|-|-|-|
|Live external APIs fail during demo|Medium|`DEMO\_MODE` flag + bundled demo-scenario JSON tested well before presentation|
|AI service crashes mid-demo|Low-Medium|Spring Boot's `AiServiceClient` catches timeouts/errors and returns last cached prediction from Postgres instead of an error page|
|PostGIS setup issues (extension not enabled on managed DB)|Medium|Verify extension is enabled at Phase 0, before any schema work begins; keep local Docker Postgres as guaranteed fallback|
|Model training takes longer than expected / poor accuracy|Medium-High|Transfer learning (ResNet) + small curated dataset keeps training under an hour; a lower-accuracy-but-working model beats a perfect one that isn't ready|
|Team blocked waiting on data/contracts|Medium|Lock all API contracts at Hour 0–1; frontend/backend work against mocks until real data lands|
|Scope creep into non-MVP features|High|Priority Matrix (Part 22) is the enforced source of truth — no P1/P2 work starts until every P0 item works end-to-end|
|Deployment breaks near deadline|Low-Medium|Local demo fallback (Part 19) rehearsed and ready regardless of cloud deploy status|

\---

## 24\. Final MVP

**Core Feature 1 — Live Cyclone Dashboard \& Map:** real ingestion (IBTrACS + OpenWeather + demo fallback), an interactive Leaflet map with current position and historical track. Foundation everything else builds on.

**Core Feature 2 — Satellite Vision Classification:** ResNet-based structure detection + multi-modal (image + numeric) intensity classification — the clearest "real AI" signal for judges.

**Core Feature 3 — Trajectory \& Intensity Prediction:** Kalman+XGBoost trajectory with visual confidence corridor, XGBoost intensity trend with explanation text.

**Core Feature 4 — Rule-Based Risk Engine:** PostGIS-powered landfall proximity + weighted risk scoring, color-coded Low/Moderate/High/Critical.

**WOW Feature 1 — Historical Cyclone Similarity Engine:** KNN-based analog retrieval with side-by-side track comparison — the single most memorable, most scientifically grounded, and cheapest-to-build differentiator in the whole project.

**WOW Feature 2 — Grad-CAM Explainable AI + AI Situation Report:** visual proof the model is "looking at the right thing," paired with an auto-generated plain-language report — together they turn "we ran a model" into "we built an intelligence system judges can trust."

**Why these six:** every one of them is 🟢/🟡 (never 🔴), every one is visibly demoable in under 30 seconds, and together they cover every category judges evaluate — real ML, real data fusion, real geospatial engineering, and genuine (not decorative) AI reasoning — without a single component that risks not working live.

\---

## 25\. Next Steps — "START BUILDING NOW" Checklist

Do these in exact order, starting immediately:

1. **Create the GitHub repo** with `main` + `develop` branches and the folder layout `frontend/`, `backend/`, `ai-service/` at the root.
2. **All 4 teammates sit together for 30 minutes** and lock the API contract: the exact JSON shapes in Section 9 (Cyclones, Satellite, Predictions, Risk, Historical, Alerts). Write it into a shared `API\_CONTRACT.md` in the repo root. Do not skip this — it's the single highest-leverage 30 minutes of the whole hackathon.
3. **Data/Integration person starts downloading IBTrACS immediately** (it's the slowest single dependency and blocks the AI team).
4. **Spin up Postgres+PostGIS via Docker** (`docker compose up -d postgres` from Part 18) so the DB is available to everyone within the first 15 minutes.
5. **Backend dev scaffolds Spring Boot project** and runs `CREATE EXTENSION postgis;` against the running DB, then creates the `cyclones` and `cyclone\_observations` tables first (everything else depends on these existing).
6. **Frontend dev scaffolds the Vite+React+TS app**, installs Tailwind/shadcn/React Router/Axios/Leaflet/Recharts, and builds the Dashboard page against **mocked JSON matching the locked contract** — don't wait for the real backend.
7. **AI/ML dev scaffolds FastAPI** (`uvicorn app.main:app --reload`) with stub endpoints returning hardcoded JSON matching the locked contract, so Backend can start integrating immediately even before real models exist.
8. **Set all environment variables** from Part 17 in local `.env` files on every machine now, before anyone forgets.
9. **Schedule the Hour 6 checkpoint** on everyone's calendar right now: "Dashboard shows real data end-to-end." Treat it as non-negotiable.
10. From this point forward, **follow the Priority Matrix (Part 22)** — build every P0 item to a working state before touching a single P1 item.

