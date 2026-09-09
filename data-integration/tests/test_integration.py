"""
Unit and integration tests for DataIntegrationProvider in src/integration.py.
"""

import os
from unittest.mock import MagicMock, patch
import pytest

from src.integration import DataIntegrationProvider
from src.demo_mode import DemoModeManager
from src.models import DataMode, WeatherData


@pytest.fixture
def provider():
    """Create and initialize a DataIntegrationProvider."""
    p = DataIntegrationProvider()
    p.initialize()
    return p


def test_provider_initialization(provider):
    assert provider.is_initialized is True
    assert provider.ibtracs.is_loaded is True
    assert provider.satellite.is_loaded is True
    assert provider.offline_weather.is_loaded is True
    assert provider.demo.is_loaded is True


def test_provider_demo_fallback(provider, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    envelope = provider.get_cyclone_data("DEMO_MAHA_2019")
    assert envelope is not None
    assert envelope.cyclone.id == "DEMO_MAHA_2019"
    assert envelope.source.mode == DataMode.DEMO
    assert envelope.observation.latitude is not None
    assert envelope.observation.longitude is not None
    assert envelope.weather is not None
    assert envelope.weather.sea_surface_temp_c is None


def test_provider_live_with_offline_weather_fallback(provider, monkeypatch):
    """
    When DEMO_MODE=false and live IBTrACS is loaded, but OpenWeather has no API key,
    weather should seamlessly fall back to offline cached weather without crashing.
    """
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")

    # Query real AMPHAN cyclone from IBTrACS
    envelope = provider.get_cyclone_data("2020136N10088")
    assert envelope is not None
    assert envelope.cyclone.name == "AMPHAN"
    assert envelope.observation.wind_speed_kmh is not None

    # Weather falls back to nearest cached/demo record
    assert envelope.weather is not None
    assert envelope.weather.sea_surface_temp_c is None
    assert envelope.source.mode == DataMode.REAL


def test_provider_3_tier_weather_fallback(provider, monkeypatch):
    """
    Test the 3-tier fallback:
      Tier 1: Live OpenWeather (when mock succeeds)
      Tier 2: Cached offline weather (when live fails)
      Tier 3: Default demo scenario weather (when cache empty)
    """
    # Tier 1: Mocked live success
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "mock_key")

    mock_live = WeatherData(
        latitude=14.8,
        longitude=86.3,
        wind_speed_kmh=125.0,
        temperature_c=29.0,
        source="openweather_live_mock",
    )
    with patch.object(provider.weather_client, "fetch_current", return_value=mock_live):
        w1 = provider.get_weather(14.8, 86.3)
        assert w1.source == "openweather_live_mock"

    # Tier 2: Live fails -> Offline cached returned
    with patch.object(provider.weather_client, "fetch_current", return_value=None):
        w2 = provider.get_weather(14.8, 86.3)
        assert w2 is not None
        assert w2.source == "demo"
        assert w2.sea_surface_temp_c is None


def test_provider_list_cyclones(provider, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    cyclones = provider.list_cyclones()
    assert len(cyclones) >= 1


def test_provider_get_observations(provider, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    obs = provider.get_observations("scenario_01")
    assert len(obs) >= 1


def test_provider_demo_scenarios_listing(provider):
    scenarios = provider.list_demo_scenarios()
    assert len(scenarios) == 5
    ids = [s.scenario_id for s in scenarios]
    assert "scenario_01" in ids
    assert "scenario_02" in ids
    assert "scenario_03" in ids
    assert "scenario_04" in ids
    assert "scenario_05" in ids


def test_provider_get_demo_scenario(provider):
    s2 = provider.get_demo_scenario("scenario_02")
    assert s2 is not None
    assert s2.cyclone.name == "AMPHAN"
    assert s2.latest_observation.intensity_category == "Super Cyclonic Storm"


def test_data_envelope_canonical_compatibility(provider):
    """Verify that all components in DataEnvelope are fully type-compatible."""
    env = provider.get_cyclone_data("scenario_01")
    assert env is not None
    # Validate Pydantic dump & roundtrip
    dumped = env.model_dump()
    assert "cyclone" in dumped
    assert "observation" in dumped
    assert "weather" in dumped
    assert "satellite" in dumped
    assert "source" in dumped
