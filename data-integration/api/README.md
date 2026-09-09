# CycloVision Data Integration — API Server

> [!IMPORTANT]
> **API Isolation Disclaimer**:
> This FastAPI application is an **isolated development/testing server** for the data integration module.
> It does **NOT** modify or replace the existing `ai-service` (port 8000) or Spring Boot `backend` (port 8080).
> It runs on port **8001** by default.

## Purpose

The API server exposes standard REST endpoints for consuming cyclone tracks, weather observations, satellite metadata, and demo scenarios. It serves as both:
1. A reference implementation of how downstream consumers (Spring Boot / ai-service / React frontend) can consume normalized cyclone data.
2. A stand-alone microservice for local prototyping and offline demonstrations.

## Starting the Server

```bash
# From the repository root or data-integration/ directory:
cd data-integration
python api/server.py
# Or using uvicorn directly:
uvicorn api.server:app --host 0.0.0.0 --port 8001 --reload
```

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Healthcheck & system status (shows active `DEMO_MODE`) |
| `GET` | `/cyclones` | List all available cyclones (IBTrACS / Demo) |
| `GET` | `/cyclones/{cyclone_id}` | Detailed metadata for a specific cyclone |
| `GET` | `/cyclones/{cyclone_id}/observations` | Historical track observations for a cyclone |
| `GET` | `/cyclones/{cyclone_id}/envelope` | Full canonical `DataEnvelope` |
| `GET` | `/weather` | Fetch current weather by coordinates (`?lat=...&lon=...`) |
| `GET` | `/satellite/catalog` | Catalog of available satellite images |
| `GET` | `/demo/scenarios` | List all 5 bundled offline demo scenarios |
| `GET` | `/demo/scenarios/{scenario_id}` | Retrieve complete demo scenario by ID |
| `GET` | `/demo/envelope` | Return standard demo `DataEnvelope` fallback |
