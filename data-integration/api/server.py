"""
FastAPI Server for CycloVision Data Integration.

Isolated stand-alone REST API for querying normalized cyclone datasets,
real-time weather observations, satellite catalog metadata, and demo scenarios.

Runs on port 8001 by default to avoid conflicting with existing services:
  - Spring Boot backend: 8080
  - AI Service: 8000
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Ensure data-integration root is on sys.path
_MODULE_ROOT = Path(__file__).parent.parent
if str(_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULE_ROOT))

from src.models import (
    Cyclone,
    Observation,
    WeatherData,
    SatelliteImage,
    DataEnvelope,
    DemoScenario,
    DataMode,
)
from src.integration import DataIntegrationProvider
from src.demo_mode import DemoModeManager

from contextlib import asynccontextmanager

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cyclovision.data_integration.api")

# Shared provider instance
provider = DataIntegrationProvider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize data sources and demo manager on startup."""
    logger.info("Initializing DataIntegrationProvider...")
    provider.initialize()
    logger.info(
        "Data Integration Server ready. DEMO_MODE=%s",
        DemoModeManager.is_demo_mode(),
    )
    yield


# Initialize FastAPI App
app = FastAPI(
    title="CycloVision Data Integration API",
    version="1.0.0",
    description=(
        "Standardized data integration layer for CycloVision. "
        "Provides access to IBTrACS records, weather feeds, satellite catalog, "
        "and offline demo scenarios."
    ),
    lifespan=lifespan,
)

# Enable CORS for development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Healthcheck ────────────────────────────────────────────────────────

@app.get("/health", summary="Health check and service status")
def health_check():
    """Return service status, data provider states, and demo mode indicator."""
    return {
        "status": "healthy",
        "service": "cyclovision-data-integration",
        "version": "1.0.0",
        "demo_mode": DemoModeManager.is_demo_mode(),
        "sources": {
            "ibtracs_loaded": provider.ibtracs.is_loaded,
            "ibtracs_cyclones_count": len(provider.ibtracs._cyclones) if provider.ibtracs.is_loaded else 0,
            "satellite_catalog_loaded": provider.satellite.is_loaded,
            "demo_scenarios_count": len(provider.demo.list_scenarios()),
        },
    }


# ── Cyclone Endpoints ──────────────────────────────────────────────────

@app.get(
    "/cyclones",
    response_model=List[Cyclone],
    summary="List cyclones",
    description="Retrieve a list of cyclones matching optional basin and season filters.",
)
def list_cyclones(
    basin: Optional[str] = Query(None, description="Basin code (e.g. NI)"),
    season_year: Optional[int] = Query(None, description="Season year (e.g. 2023)"),
    limit: int = Query(100, ge=1, le=500, description="Max items to return"),
):
    return provider.list_cyclones(basin=basin, season_year=season_year, limit=limit)


@app.get(
    "/cyclones/{cyclone_id}",
    response_model=Cyclone,
    summary="Get cyclone metadata",
    description="Fetch metadata for a single cyclone by ID.",
)
def get_cyclone(cyclone_id: str):
    if provider.ibtracs.is_loaded:
        c = provider.ibtracs.get_cyclone(cyclone_id)
        if c:
            return c

    # Fallback to demo scenarios
    scenario = provider.demo.get_scenario(cyclone_id)
    if scenario:
        return scenario.cyclone

    for s in provider.demo.list_scenarios():
        if s.cyclone.id == cyclone_id:
            return s.cyclone

    raise HTTPException(status_code=404, detail=f"Cyclone '{cyclone_id}' not found")


@app.get(
    "/cyclones/{cyclone_id}/observations",
    response_model=List[Observation],
    summary="Get cyclone track observations",
    description="Retrieve chronological observation track for a cyclone.",
)
def get_cyclone_observations(cyclone_id: str):
    obs = provider.get_observations(cyclone_id)
    if not obs:
        # Check if cyclone exists in demo
        scenario = provider.demo.get_scenario(cyclone_id)
        if scenario:
            return [scenario.latest_observation] + scenario.historical_observations
        for s in provider.demo.list_scenarios():
            if s.cyclone.id == cyclone_id:
                return [s.latest_observation] + s.historical_observations

        raise HTTPException(
            status_code=404,
            detail=f"No observations found for cyclone '{cyclone_id}'",
        )
    return obs


@app.get(
    "/cyclones/{cyclone_id}/envelope",
    response_model=DataEnvelope,
    summary="Get full cyclone DataEnvelope",
    description="Get the full canonical data envelope containing cyclone metadata, latest observation, weather, and satellite data.",
)
def get_cyclone_envelope(cyclone_id: str):
    envelope = provider.get_cyclone_data(cyclone_id)
    if not envelope:
        raise HTTPException(
            status_code=404,
            detail=f"Could not construct data envelope for '{cyclone_id}'",
        )
    return envelope


# ── Weather Endpoint ───────────────────────────────────────────────────

@app.get(
    "/weather",
    response_model=WeatherData,
    summary="Get weather at coordinate",
    description="Fetch weather at coordinate via OpenWeather API or demo fallback.",
)
def get_weather(
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(..., ge=-180.0, le=360.0, description="Longitude"),
):
    weather = provider.get_weather(lat, lon)
    if not weather:
        raise HTTPException(
            status_code=503,
            detail="Weather service unavailable and no demo data present",
        )
    return weather


# ── Satellite Catalog ──────────────────────────────────────────────────

@app.get(
    "/satellite/catalog",
    response_model=List[SatelliteImage],
    summary="List satellite imagery",
    description="List all cataloged satellite images.",
)
def list_satellite_images(
    cyclone_id: Optional[str] = Query(None, description="Filter by cyclone ID"),
):
    if cyclone_id:
        return provider.satellite.get_images_for_cyclone(cyclone_id)
    return provider.satellite.list_images()


# ── Demo Scenarios Endpoints ───────────────────────────────────────────

@app.get(
    "/demo/scenarios",
    response_model=List[DemoScenario],
    summary="List demo scenarios",
    description="Retrieve all 5 curated demo scenarios for offline demonstration.",
)
def list_demo_scenarios():
    return provider.list_demo_scenarios()


@app.get(
    "/demo/scenarios/{scenario_id}",
    response_model=DemoScenario,
    summary="Get demo scenario by ID",
    description="Retrieve a specific demo scenario by its scenario ID (e.g. scenario_01).",
)
def get_demo_scenario(scenario_id: str):
    scenario = provider.get_demo_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Demo scenario '{scenario_id}' not found",
        )
    return scenario


@app.get(
    "/demo/envelope",
    response_model=DataEnvelope,
    summary="Get default demo envelope",
    description="Retrieve a complete DataEnvelope from the default demo scenario.",
)
def get_demo_envelope():
    default_scenario = provider.demo.get_default_scenario()
    if not default_scenario:
        raise HTTPException(
            status_code=404,
            detail="No demo scenarios loaded",
        )
    return provider.demo.scenario_to_envelope(default_scenario)


def run_server(host: str = "0.0.0.0", port: int = 8001):
    """Run the API server with uvicorn."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    port = int(os.environ.get("DATA_API_PORT", "8001"))
    host = os.environ.get("DATA_API_HOST", "0.0.0.0")
    run_server(host=host, port=port)
