"""
Unit tests for OpenWeatherClient and OfflineWeatherStore in src/weather.py.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import requests

from src.weather import OpenWeatherClient, OfflineWeatherStore
from src.models import WeatherData


# ── Live Client Tests ──────────────────────────────────────────────────

def test_openweather_no_api_key():
    client = OpenWeatherClient(api_key="")
    assert client.has_api_key is False
    result = client.fetch_current(15.0, 85.0)
    assert result is None


def test_openweather_successful_fetch():
    mock_payload = {
        "dt": 1589781600,
        "main": {
            "temp": 301.15,  # 28.0 °C
            "pressure": 998,
        },
        "wind": {
            "speed": 15.0,  # 15 m/s -> 54.0 km/h
        },
    }

    client = OpenWeatherClient(api_key="mock_key")
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_get.return_value = mock_resp

        weather = client.fetch_current(15.0, 85.0)
        assert weather is not None
        assert weather.latitude == 15.0
        assert weather.longitude == 85.0
        assert weather.temperature_c == 28.0
        assert weather.wind_speed_kmh == 54.0
        assert weather.pressure_hpa == 998.0
        assert weather.sea_surface_temp_c is None
        assert weather.source == "openweather"


def test_openweather_missing_fields_in_payload():
    """Verify missing wind or main objects parse gracefully without crash."""
    mock_payload = {
        "dt": 1589781600,
        # missing main and wind
    }
    client = OpenWeatherClient(api_key="mock_key")
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_get.return_value = mock_resp

        weather = client.fetch_current(15.0, 85.0)
        assert weather is not None
        assert weather.wind_speed_kmh is None
        assert weather.pressure_hpa is None
        assert weather.temperature_c is None
        assert weather.sea_surface_temp_c is None


def test_openweather_timeout_handling():
    client = OpenWeatherClient(api_key="mock_key")
    with patch("requests.get", side_effect=requests.exceptions.Timeout("Timeout")):
        weather = client.fetch_current(15.0, 85.0)
        assert weather is None


def test_openweather_connection_error_handling():
    client = OpenWeatherClient(api_key="mock_key")
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Offline")):
        weather = client.fetch_current(15.0, 85.0)
        assert weather is None


def test_openweather_http_error_handling():
    client = OpenWeatherClient(api_key="mock_key")
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_resp

        weather = client.fetch_current(15.0, 85.0)
        assert weather is None


def test_openweather_malformed_json_handling():
    client = OpenWeatherClient(api_key="mock_key")
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.side_effect = ValueError("Malformed JSON")
        mock_get.return_value = mock_resp

        weather = client.fetch_current(15.0, 85.0)
        assert weather is None


# ── Offline Store Tests ────────────────────────────────────────────────

def test_offline_weather_store_load():
    store = OfflineWeatherStore()
    assert store.load() is True
    assert store.is_loaded is True
    records = store.list_records()
    assert len(records) >= 5

    # Verify all records have null SST and valid source
    for rec in records:
        assert rec.sea_surface_temp_c is None
        assert rec.source == "demo"
        assert rec.latitude is not None
        assert rec.longitude is not None


def test_offline_weather_store_get_nearest():
    store = OfflineWeatherStore()
    store.load()

    # Query coordinate near Chennai (13.08, 80.27)
    weather = store.get_nearest(13.0, 80.0)
    assert weather is not None
    assert 12.0 <= weather.latitude <= 14.0
    assert 79.0 <= weather.longitude <= 81.5


def test_offline_weather_store_missing_file(tmp_path: Path):
    store = OfflineWeatherStore(samples_path=tmp_path / "non_existent.json")
    assert store.load() is False
    assert store.is_loaded is False
    assert store.get_nearest(10.0, 70.0) is None
