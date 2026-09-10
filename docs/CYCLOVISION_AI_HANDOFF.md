# CycloVision AI-Service Handoff Specification

**Document Version:** 1.2.0  
**Target Subsystem:** `ai-service/`  
**Runtime Environment:** Python 3.10+, FastAPI, Pydantic v2, XGBoost 3.2+, Scikit-learn, PyTorch  
**Default Port:** 8000  
**Integration Status:** Foundation, Canonical Contract, and **First Real ML Model (XGBoost 24-Hour Intensity v1.0)** Implemented and Verified (30/30 Tests Passing).

---

## 1. Subsystem Architecture Overview

The `ai-service` is an autonomous, **100% stateless** microservice responsible for deep-learning vision inference, meteorological trajectory forecasting, satellite feature extraction (including Grad-CAM saliency heatmaps), historical similarity matching, and intelligent civil defense situation reporting.

### 1.1 Architectural Boundary & Stateless Guarantee

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AI Service (Port 8000)                          │
│                [100% Stateless - ZERO Database Access]                 │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 1. Satellite CNN  │ 2. Track / Wind   │ 3. Historical Similarity       │
│    & Grad-CAM     │    Forecasting    │    Matching Engine             │
│ (ResNet/Vision)   │   (Kalman/Physics)│    (KNN / Track Embedding)     │
├───────────────────┴───────────────────┴────────────────────────────────┤
│ 4. Multi-Modal Feature Fusion & Multi-Hazard Risk Assessment           │
├────────────────────────────────────────────────────────────────────────┤
│ 5. XAI Explainability & Meteorological Situation Report Engine         │
├────────────────────────────────────────────────────────────────────────┤
│ [NEW] Real ML Model: XGBoost 24h Intensity Predictor v1.0             │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP REST
                                    │ POST /predict/full
                                    │ POST /predict/full/multipart
                    ┌───────────────┴───────────────┐
                    │                               │
        ┌───────────┴───────────┐       ┌───────────┴───────────┐
        │  Spring Boot Backend  │       │   Data Integration    │
        │      (Port 8080)      │       │      (Port 8001)      │
        │ [Holder of DB Secret] │       │ [Data Pipelines/Demo] │
        └───────────▲───────────┘       └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Supabase PostgreSQL  │
        │    (PostGIS V4)       │
        └───────────────────────┘
```

> [!IMPORTANT]
> **Stateless Constraint**: The AI service contains **ZERO PostgreSQL credentials, ZERO Supabase credentials, and ZERO database connections**. Spring Boot queries Supabase/PostGIS for observations, ambient weather, and satellite references, and supplies all inference context to FastAPI via the canonical REST contract.

---

## 2. Canonical Multi-Modal Pipeline Contract (`POST /predict/full`)

### 2.1 Pipeline Flow
The full prediction pipeline orchestrates eight specialized processing stages:
```
1. Satellite Vision (Signed URL or Multipart Bytes)
   +
2. Numerical Cyclone Observations & Weather Context
   +
3. Trajectory Filtering & Kinematic Kinematics
   +
4. Historical Track Similarity Matching (IBTrACS Analogues)
   ↓
5. Multi-Modal Feature Fusion
   ↓
6. Trajectory & Intensity Prediction (Horizons: 6h, 12h, 24h, 48h, 72h)
      └─ Powered by: XGBoostIntensityPredictor (24h anchor)
   ↓
7. Multi-Hazard Risk Evaluation (Surge, Wind, Flood, Vulnerability)
   ↓
8. Explainability (XAI Attribution) & Operational Situation Report
```

### 2.2 Endpoint Details
- **Path:** `POST /predict/full` (or alias `POST /api/v1/ai/predict/full`)
- **Direct Binary Fallback:** `POST /predict/full/multipart` (supports `image_file: UploadFile` alongside form-encoded JSON `payload`)
- **Content-Type:** `application/json` (or `multipart/form-data`)

---

## 3. Real ML Component: XGBoost 24-Hour Intensity Model (v1.0)

### 3.1 Model Overview & Target Definition
- **Model Identifier:** `XGBoost-Intensity-v1.0`
- **Class Implementation:** `app.models.xgboost_intensity.XGBoostIntensityPredictor` implementing `IIntensityPredictor`.
- **Target ($y$):** Future maximum sustained surface wind speed in knots ($V_{t + 24\text{h}}$) observed for the **SAME** cyclone within a window of $24\text{h} \pm 3\text{h}$.
- **Artifact Path:** `ai-service/app/artifacts/xgboost_intensity_v1.json` (alongside `xgboost_intensity_v1_metadata.json`).

### 3.2 14-Feature Input Vector
Features are extracted strictly from information available at or before prediction time $t$:

| Index | Feature | Description | Missingness Strategy |
|---|---|---|---|
| 0 | `latitude` | Storm center latitude ($\phi_t \in [-90, 90]$) | Always present in observation |
| 1 | `longitude` | Storm center longitude ($\lambda_t \in [-180, 180]$) | Always present in observation |
| 2 | `current_wind_kts` | Maximum sustained surface wind at time $t$ | Required for inference |
| 3 | `current_pressure_hpa` | Central sea-level pressure in hPa | Default to 1010.0 if missing |
| 4 | `pressure_available` | Binary indicator ($1.0$ if observed, $0.0$ if imputed) | Clean flag |
| 5 | `translation_speed_kmh` | Forward storm translation speed in km/h | $0.0$ if first point in track |
| 6 | `translation_heading_deg` | Direction of motion from true North ($0.0 - 360.0$) | $0.0$ if first point in track |
| 7 | `coriolis_param` | Planetary vorticity $2\Omega \sin(\phi_t)$ in $\text{s}^{-1}$ | Deterministic physical formula |
| 8 | `lag_6h_wind_change_kts` | $V_t - V_{t-6\text{h}}$ rate of intensification | $0.0$ if storm age $< 6\text{h}$ |
| 9 | `lag_6h_available` | Binary indicator ($1.0$ if 6h prior obs exists) | Clean flag |
| 10 | `lag_6h_lat_change` | $\phi_t - \phi_{t-6\text{h}}$ meridional displacement | $0.0$ if storm age $< 6\text{h}$ |
| 11 | `lag_6h_lon_change` | $\lambda_t - \lambda_{t-6\text{h}}$ zonal displacement | $0.0$ if storm age $< 6\text{h}$ |
| 12 | `lag_12h_wind_change_kts` | $V_t - V_{t-12\text{h}}$ 12-hour intensity delta | $0.0$ if storm age $< 12\text{h}$ |
| 13 | `season_month` | Calendar month (1–12) capturing bimodal seasonality | From observation timestamp |

### 3.3 Cyclone-Identity-Aware Dataset Split
The dataset was partitioned strictly by storm seasons, guaranteeing zero cross-contamination of cyclone identities:
- **Training Set (Seasons $\le 2013$):** 3,539 samples across 274 unique cyclones.
- **Validation Set (Seasons $2014 - 2018$):** 949 samples across 50 unique cyclones.
- **Test Set (Seasons $\ge 2019$):** 1,428 samples across 77 unique modern cyclones (including Fani, Vayu, Tauktae, Biparjoy, Mocha).
- **Total Supervised Samples:** 5,916 across 401 cyclones.

### 3.4 Baseline Hyperparameter Configuration
```python
{
    "n_estimators": 250,
    "max_depth": 5,
    "learning_rate": 0.04,
    "subsample": 0.85,
    "colsample_bytree": 0.85,
    "min_child_weight": 4,
    "gamma": 0.5,
    "objective": "reg:squarederror",
    "random_state": 42,
    "early_stopping_rounds": 20
}
```
*Early stopping selected iteration 110 based on validation set RMSE.*

### 3.5 Evaluation Metrics

| Metric | Training Set | Validation Set | Test Set (Untouched Modern Era) |
|---|---|---|---|
| **MAE** | **7.03 kts** | **10.87 kts** | **10.29 kts** (~19.0 km/h) |
| **RMSE** | **9.89 kts** | **15.61 kts** | **13.94 kts** |
| **$R^2$** | **0.8267** | **0.4976** | **0.6903** |
| **Mean Bias** | **-0.01 kts** | **+0.56 kts** | **-0.08 kts** |

### 3.6 Performance by Intensity Regime (Test Set)

| Regime | Actual Range | Sample Count | Test MAE | Test RMSE | Mean Bias |
|---|---|---|---|---|---|
| **Depression** | $< 34$ kts | 648 | **7.96 kts** | 10.74 kts | $+7.32$ kts (slight overprediction of dissipating storms) |
| **Gale / Cyclonic Storm** | $34 - 63$ kts | 462 | **9.14 kts** | 11.74 kts | **-0.99 kts** (extremely accurate, near zero bias) |
| **Very Severe Cyclonic Storm** | $64 - 95$ kts | 243 | **14.13 kts** | 17.47 kts | $-10.45$ kts (underprediction of intense cores) |
| **Extremely Severe / Super** | $> 95$ kts | 75 | **25.04 kts** | 29.42 kts | $-24.84$ kts (underprediction of extreme peaks) |

### 3.7 Rapid Intensification (RI) Analysis
- **Events in Test Set ($\ge 30$ kt surge in 24h):** 82 events.
- **Actual Mean 24h Surge:** $+38.36$ kts.
- **Predicted Mean Surge:** $+8.54$ kts.
- **Underprediction Bias:** $-29.82$ kts.
- **Physical Rationale:** Pure historical track coordinates and barometric pressure alone cannot capture sudden convective core eyewall contractions or warm ocean eddy thermal anomalies without satellite imagery (ResNet) or gridded SST/shear data. This finding scientifically motivates the upcoming Vision and Multi-Modal Fusion phases.

### 3.8 Feature Importance (Model Gain Metric)
1. `current_wind_kts`: **24,612.08** (vortex persistence)
2. `lag_12h_wind_change_kts`: **5,526.54** (intensification momentum)
3. `current_pressure_hpa`: **4,024.92** (barometric core depth)
4. `longitude`: **3,549.99** (oceanic basin geography)
5. `lag_6h_wind_change_kts`: **3,346.74** (short-term momentum)
6. `coriolis_param`: **3,013.33** (rotational vorticity)
7. `latitude`: **2,385.48** (meridional position)
8. `season_month`: **2,030.88** (monsoon climatology)
9. `lag_6h_available`: **1,723.53**
10. `translation_heading_deg`: **1,580.76**
11. `pressure_available`: **1,361.07**
12. `lag_6h_lon_change`: **1,214.67**
13. `translation_speed_kmh`: **963.55**
14. `lag_6h_lat_change`: **2,275.32**

*(Note: Feature importance indicates tree split gain within the gradient boosting ensemble and does not constitute isolated physical causation).*

---

## 4. Software Architecture & Model Abstractions

| Interface | Concrete Implementation | Status |
|---|---|---|
| `IIntensityPredictor` | `app.models.xgboost_intensity.XGBoostIntensityPredictor` | ✅ **TRAINED & ACTIVE** (`xgboost_intensity_v1.json`) |
| `ITrajectoryForecaster` | `BaselineTrajectoryForecaster` | Foundation (Kalman / Kinematics) |
| `IVisionAnalyzer` | `BaselineVisionAnalyzer` | Foundation (Awaiting ResNet weights) |
| `ISimilarityMatcher` | `BaselineSimilarityMatcher` | Foundation (KNN Track Embeddings) |
| `IFusionEngine` | `BaselineFusionEngine` | Foundation (Cross-Attention Fusion) |
| `IRiskAssessor` | `BaselineRiskAssessor` | Foundation (Hazard Indexing) |
| `IExplainabilityEngine` | `BaselineExplainabilityEngine` | Foundation (Physics Attribution) |
| `ISituationReportGenerator` | `BaselineSituationReportGenerator` | Foundation (Civil Defense Reporting) |

---

## 5. Verification & Test Suite

Run full suite:
```bash
cd ai-service
pytest -v
```

### Verified Test Cases (30/30 Passing):
1. **API Contracts (`test_api_contracts.py`):** 12 tests covering `/predict/full`, multipart direct bytes, 422 validations, modular and legacy routes.
2. **Feature Engineering Pipeline (`test_feature_pipeline.py`):** 5 tests verifying Coriolis parameter math, 14-feature dimensionality, zero future leakage, missing value flags, and cyclone-identity isolation.
3. **Pydantic Schemas (`test_schemas.py`):** 6 tests verifying coordinate ranges, chronological observation ordering, and horizon deduplication.
4. **Stateless Boundary (`test_statelessness.py`):** 1 test scanning the entire application tree to guarantee zero database credentials or drivers exist.
5. **XGBoost Provider (`test_xgboost_model.py`):** 6 tests verifying artifact loading, deterministic inference, valid physical clamping, missing artifact failure handling, and malformed input rejection.
