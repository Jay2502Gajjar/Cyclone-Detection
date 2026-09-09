"""
Canonical data models for the CycloVision data integration layer.

All data flowing through the integration layer is represented by these
Pydantic models. They define the unified contract consumed by the
backend (Spring Boot) and AI service (FastAPI).
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ── Intensity Categories (IMD scale) ──────────────────────────────────

class IntensityCategory(str, enum.Enum):
    """India Meteorological Department tropical cyclone classification."""
    DEPRESSION = "Depression"
    DEEP_DEPRESSION = "Deep Depression"
    CYCLONIC_STORM = "Cyclonic Storm"
    SEVERE_CYCLONIC_STORM = "Severe Cyclonic Storm"
    VERY_SEVERE_CYCLONIC_STORM = "Very Severe Cyclonic Storm"
    EXTREMELY_SEVERE_CYCLONIC_STORM = "Extremely Severe Cyclonic Storm"
    SUPER_CYCLONIC_STORM = "Super Cyclonic Storm"
    UNKNOWN = "Unknown"


# ── Data Mode / Provenance ────────────────────────────────────────────

class DataMode(str, enum.Enum):
    """Indicates the provenance of a data record."""
    REAL = "real"
    CACHED = "cached"
    DEMO = "demo"
    SYNTHETIC = "synthetic"


# ── Core Models ───────────────────────────────────────────────────────

class Cyclone(BaseModel):
    """Metadata for a single tropical cyclone."""
    id: str = Field(..., description="Unique cyclone identifier (e.g. IBTrACS SID)")
    name: str = Field(default="UNNAMED", description="Assigned cyclone name")
    basin: str = Field(default="NI", description="Ocean basin code")
    season_year: int = Field(..., description="Year of the cyclone season")
    status: str = Field(default="historical", description="active | historical | demo")


class Observation(BaseModel):
    """A single point-in-time observation of a cyclone."""
    observed_at: datetime = Field(..., description="UTC timestamp of observation")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=360.0)
    wind_speed_kmh: Optional[float] = Field(default=None, ge=0)
    pressure_hpa: Optional[float] = Field(default=None, ge=800, le=1100)
    movement_direction_deg: Optional[float] = Field(default=None, ge=0, le=360)
    movement_speed_kmh: Optional[float] = Field(default=None, ge=0)
    intensity_category: IntensityCategory = Field(default=IntensityCategory.UNKNOWN)


class WeatherData(BaseModel):
    """Current weather conditions at a location."""
    latitude: float
    longitude: float
    wind_speed_kmh: Optional[float] = None
    pressure_hpa: Optional[float] = None
    temperature_c: Optional[float] = None
    sea_surface_temp_c: Optional[float] = None  # null unless genuinely available
    observed_at: Optional[datetime] = None
    source: str = Field(default="openweather")


class SatelliteImage(BaseModel):
    """Metadata for a satellite image."""
    image_id: str
    cyclone_id: Optional[str] = None
    captured_at: Optional[datetime] = None
    image_type: str = Field(default="infrared", description="visible | infrared | water_vapor")
    source: str = Field(default="demo")
    storage_path: str = Field(..., description="Relative path to the image file")
    is_cyclone: bool = Field(default=True, description="True if image shows a cyclone")


class SourceInfo(BaseModel):
    """Provenance tracking for a data record."""
    mode: DataMode = Field(default=DataMode.DEMO)
    provider: str = Field(default="demo")
    source_url: Optional[str] = None
    downloaded_at: Optional[datetime] = None
    processing_script: Optional[str] = None
    processing_version: Optional[str] = None
    original_filename: Optional[str] = None


# ── Composite Envelope ────────────────────────────────────────────────

class DataEnvelope(BaseModel):
    """
    The canonical data envelope returned by the integration layer.

    This is the top-level structure that any consumer (backend, AI service,
    frontend) should expect when requesting cyclone data.
    """
    cyclone: Cyclone
    observation: Observation
    weather: Optional[WeatherData] = None
    satellite: Optional[SatelliteImage] = None
    source: SourceInfo = Field(default_factory=SourceInfo)


# ── Demo Scenario ─────────────────────────────────────────────────────

class DemoScenario(BaseModel):
    """A self-contained demo scenario for offline operation."""
    scenario_id: str
    title: str
    description: str
    cyclone: Cyclone
    latest_observation: Observation
    historical_observations: List[Observation] = Field(default_factory=list)
    weather: Optional[WeatherData] = None
    satellite: Optional[SatelliteImage] = None
    source: SourceInfo = Field(default_factory=lambda: SourceInfo(mode=DataMode.DEMO, provider="demo"))
    created_at: datetime = Field(default_factory=datetime.utcnow)
