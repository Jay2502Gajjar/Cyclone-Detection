# CycloVision — Data Integration Layer

The **Data Integration Layer** is a standalone, isolated module for the CycloVision / Tropical Cyclone Intelligence Platform. It provides end-to-end pipelines for downloading, normalizing, validating, and serving meteorological and remote sensing datasets.

---

## 🌟 Key Features

1. **Canonical Data Modeling & Normalization**:
   - Pydantic v2 schemas defining standard contracts for `Cyclone`, `Observation`, `WeatherData`, and `SatelliteImage`.
   - Complete normalization for wind speeds (knots/m/s/mph $\rightarrow$ km/h), barometric pressure (hPa), coordinates, timestamps, and forward motion calculations.
   - Official **India Meteorological Department (IMD)** intensity categorization (Depression through Super Cyclonic Storm).

2. **IBTrACS Pipeline**:
   - Automated downloader and parser for NOAA IBTrACS v04 North Indian Ocean cyclone database.
   - In-memory query store with sub-second spatial and chronological track retrieval.

3. **Remote Sensing & Satellite Catalog**:
   - Satellite cataloging structure (`cyclone/` and `non_cyclone/`).
   - Synthetic demo placeholders with clear visual watermarking (no confusion with real data).
   - Step-by-step instructions for acquiring real INSAT-3D/3DR (MOSDAC) and GOES imagery.

4. **Weather Integration**:
   - OpenWeather API client with strict timeouts (3s), zero-crash error handling, and unit normalization.

5. **Bulletproof Offline Demo Mode (`DEMO_MODE=true`)**:
   - 5 complete, curated cyclone scenarios (MAHA 2019, AMPHAN 2020, BIPARJOY 2023, MOCHA 2023, REMAL 2024).
   - Priority fallback hierarchy: `LIVE → CACHED → DEMO`.

6. **Isolated REST API & Schemas**:
   - FastAPI server running independently on port **8001** (does not conflict with backend or AI service).
   - Draft-07 JSON Schemas for inter-service validation.

---

## 📁 Directory Structure

```text
data-integration/
├── README.md                           # This overview and reproduction guide
├── requirements.txt                    # Python dependencies (pydantic, fastapi, requests, pytest)
├── .env.example                        # Environment variables template
│
├── config/
│   └── sources.yaml                    # Data source configurations & thresholds
│
├── data/
│   ├── raw/                            # Ingested raw datasets (IBTrACS, Weather)
│   ├── processed/                      # Cleaned and normalized datasets
│   └── demo/
│       ├── scenarios/                  # 5 complete offline demo scenarios
│       └── images/                     # Demo satellite placeholder images
│
├── scripts/
│   ├── download_ibtracs.py             # Download IBTrACS North Indian Ocean CSV
│   ├── process_ibtracs.py              # Clean, normalize, and extract cyclone tracks
│   ├── prepare_satellite_data.py       # Generate demo image catalog & instructions
│   ├── create_demo_scenarios.py        # Generate the 5 curated demo scenario folders
│   └── validate_data.py               # Data quality, coordinates & track validator
│
├── src/
│   ├── models.py                       # Pydantic data models & IMD intensity enum
│   ├── normalizers.py                  # Unit conversions & movement calculation
│   ├── ibtracs.py                      # IBTrACS store & search facade
│   ├── satellite.py                    # Satellite catalog manager
│   ├── weather.py                      # OpenWeather client with graceful fallback
│   ├── demo_mode.py                    # Demo manager & priority fallback logic
│   └── integration.py                  # Unified DataIntegrationProvider entrypoint
│
├── api/
│   ├── README.md                       # Isolation & API usage documentation
│   └── server.py                       # Standalone FastAPI REST server (port 8001)
│
├── schemas/
│   ├── cyclone.json                    # Cyclone JSON schema
│   ├── observation.json                # Observation JSON schema
│   ├── weather.json                    # Weather JSON schema
│   └── demo_scenario.json             # Demo scenario JSON schema
│
├── docs/
│   ├── DATA_DICTIONARY.md              # Detailed field definitions, units & ranges
│   ├── INTEGRATION_CONTRACT.md         # Consumer integration guide for Java/Python/TS
│   └── INTEGRATION_NOTES.md            # Future DB migrations, scheduled tasks & compose
│
└── tests/
    ├── test_models.py                  # Pydantic model validation tests
    ├── test_normalizers.py             # Unit conversion and math tests
    ├── test_ibtracs.py                 # IBTrACS store and track tests
    ├── test_weather.py                 # OpenWeather client mock tests
    ├── test_demo_mode.py               # Demo fallback tests
    ├── test_validation.py              # Dataset validation tests
    └── test_integration.py             # Unified provider integration tests
```

---

## 🚀 Quickstart & Reproduction Steps

### 1. Set Up Environment

```bash
cd data-integration
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Generate Demo Assets & Scenarios

```bash
# Generate the 5 offline demo scenarios
python scripts/create_demo_scenarios.py

# Generate demo satellite image placeholders & catalog
python scripts/prepare_satellite_data.py
```

### 3. (Optional) Ingest Real IBTrACS Data

```bash
# Download North Indian Ocean subset from NOAA (~5 MB)
python scripts/download_ibtracs.py

# Clean and normalize into processed JSON datasets
python scripts/process_ibtracs.py
```

### 4. Run Data Quality Validation

```bash
python scripts/validate_data.py --demo
```
The report is displayed on the console and saved to `docs/validation_report.txt`.

### 5. Run the Test Suite

```bash
python -m pytest tests/ -v
```

### 6. Start the API Server

```bash
python api/server.py
```
Open [http://localhost:8001/docs](http://localhost:8001/docs) in your browser to explore the interactive OpenAPI documentation.

---

## 🔒 Repository Isolation Guarantee

All files created for the Data Integration module are strictly isolated within the `data-integration/` directory. Zero modifications have been made to existing frontend, backend, or AI service codebases.
