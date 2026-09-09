"""
Unit tests for canonical Pydantic models in src/models.py.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from src.models import (
    Cyclone,
    Observation,
    WeatherData,
    SatelliteImage,
    SourceInfo,
    DataEnvelope,
    DemoScenario,
    IntensityCategory,
    DataMode,
)


def test_cyclone_model_valid():
    c = Cyclone(
        id="2020139N11086",
        name="AMPHAN",
        basin="NI",
        season_year=2020,
        status="historical",
    )
    assert c.id == "2020139N11086"
    assert c.name == "AMPHAN"
    assert c.basin == "NI"
    assert c.season_year == 2020
    assert c.status == "historical"


def test_cyclone_model_missing_id():
    with pytest.raises(ValidationError):
        Cyclone(name="AMPHAN", season_year=2020)


def test_observation_model_valid():
    obs = Observation(
        observed_at=datetime(2020, 5, 18, 12, 0, tzinfo=timezone.utc),
        latitude=13.5,
        longitude=86.5,
        wind_speed_kmh=185.0,
        pressure_hpa=940.0,
        movement_direction_deg=348.0,
        movement_speed_kmh=13.0,
        intensity_category=IntensityCategory.EXTREMELY_SEVERE_CYCLONIC_STORM,
    )
    assert obs.latitude == 13.5
    assert obs.longitude == 86.5
    assert obs.wind_speed_kmh == 185.0
    assert obs.intensity_category == IntensityCategory.EXTREMELY_SEVERE_CYCLONIC_STORM


def test_observation_invalid_coordinates():
    with pytest.raises(ValidationError):
        Observation(
            observed_at=datetime.now(timezone.utc),
            latitude=95.0,  # Invalid > 90
            longitude=80.0,
        )


def test_weather_data_model_defaults():
    w = WeatherData(
        latitude=15.0,
        longitude=85.0,
        wind_speed_kmh=45.0,
        pressure_hpa=1005.0,
        temperature_c=28.5,
    )
    assert w.sea_surface_temp_c is None
    assert w.source == "openweather"


def test_satellite_image_model():
    sat = SatelliteImage(
        image_id="demo_ir_01",
        cyclone_id="DEMO_AMPHAN_2020",
        storage_path="data/demo/images/cyclone/demo_ir_01.png",
        image_type="infrared",
        is_cyclone=True,
    )
    assert sat.image_id == "demo_ir_01"
    assert sat.is_cyclone is True
    assert sat.source == "demo"


def test_data_envelope():
    c = Cyclone(id="DEMO_01", season_year=2023)
    obs = Observation(
        observed_at=datetime.now(timezone.utc),
        latitude=12.0,
        longitude=70.0,
    )
    env = DataEnvelope(cyclone=c, observation=obs)
    assert env.cyclone.id == "DEMO_01"
    assert env.source.mode == DataMode.DEMO
    assert env.weather is None
    assert env.satellite is None


def test_demo_scenario_serialization():
    c = Cyclone(id="DEMO_SCENARIO", season_year=2024)
    obs = Observation(
        observed_at=datetime.now(timezone.utc),
        latitude=18.0,
        longitude=88.0,
        wind_speed_kmh=110.0,
    )
    scenario = DemoScenario(
        scenario_id="scenario_01",
        title="Test Scenario",
        description="A test scenario",
        cyclone=c,
        latest_observation=obs,
    )
    data = scenario.model_dump()
    assert data["scenario_id"] == "scenario_01"
    assert data["cyclone"]["id"] == "DEMO_SCENARIO"
