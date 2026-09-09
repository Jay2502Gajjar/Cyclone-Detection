"""
Weather client and offline store with normalization and graceful failure handling.

Components:
  1. OpenWeatherClient: Fetches live weather for lat/lon, normalizes to canonical
     WeatherData model, and handles every failure mode (missing API key, timeout,
     HTTP error, malformed response, missing fields) gracefully.
  2. OfflineWeatherStore: Provides cached and demo weather records for offline operation
     (DEMO_MODE=true or when network/API key is unavailable).

Implements the priority chain:
  LIVE → CACHED / OFFLINE → DEMO
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import requests

from .models import WeatherData
from .normalizers import (
    haversine_km,
    kelvin_to_celsius,
    ms_to_kmh,
    normalize_pressure,
    parse_timestamp,
)

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://api.openweathermap.org/data/2.5"
_DEFAULT_TIMEOUT = 3  # seconds
_DEFAULT_WEATHER_SAMPLES_PATH = (
    Path(__file__).parent.parent / "data" / "demo" / "weather" / "samples.json"
)


# ── Live OpenWeather Client ───────────────────────────────────────────

class OpenWeatherClient:
    """
    Client for the OpenWeather Current Weather API.

    Configuration is read from environment variables:
      - OPENWEATHER_API_KEY: API key (required for live calls)
      - OPENWEATHER_BASE_URL: Base URL (optional, has default)
      - REQUEST_TIMEOUT_SECONDS: Request timeout (optional, default 3)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self._api_key = api_key or os.environ.get("OPENWEATHER_API_KEY", "")
        self._base_url = (
            base_url
            or os.environ.get("OPENWEATHER_BASE_URL", _DEFAULT_BASE_URL)
        ).rstrip("/")
        self._timeout = timeout or int(
            os.environ.get("REQUEST_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT))
        )

    @property
    def has_api_key(self) -> bool:
        """Check whether an API key is configured."""
        return bool(self._api_key and self._api_key.strip())

    def fetch_current(self, lat: float, lon: float) -> Optional[WeatherData]:
        """
        Fetch current weather for a location.

        Returns a normalized WeatherData object, or None on any failure.
        Failures are logged but never raised — the caller should fall back
        to offline/demo data when None is returned.
        """
        if not self.has_api_key:
            logger.info("OpenWeather API key not configured — skipping live fetch")
            return None

        url = f"{self._base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self._api_key,
            "units": "standard",  # Kelvin, m/s — we normalize ourselves
        }

        try:
            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data, lat, lon)

        except requests.exceptions.Timeout:
            logger.warning("OpenWeather request timed out after %ds", self._timeout)
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("OpenWeather connection failed (network unreachable?)")
            return None
        except requests.exceptions.HTTPError as exc:
            logger.warning("OpenWeather HTTP error: %s", exc)
            return None
        except requests.exceptions.RequestException as exc:
            logger.warning("OpenWeather request failed: %s", exc)
            return None
        except (ValueError, KeyError, TypeError) as exc:
            logger.warning("Failed to parse OpenWeather response: %s", exc)
            return None

    def _parse_response(
        self, data: dict, lat: float, lon: float
    ) -> Optional[WeatherData]:
        """Parse and normalize the OpenWeather JSON response."""
        try:
            wind = data.get("wind", {}) if isinstance(data.get("wind"), dict) else {}
            main = data.get("main", {}) if isinstance(data.get("main"), dict) else {}

            wind_speed_ms = wind.get("speed")
            pressure_raw = main.get("pressure")
            temp_kelvin = main.get("temp")
            timestamp = data.get("dt")

            observed_at = None
            if timestamp:
                observed_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)

            return WeatherData(
                latitude=lat,
                longitude=lon,
                wind_speed_kmh=ms_to_kmh(wind_speed_ms),
                pressure_hpa=normalize_pressure(pressure_raw),
                temperature_c=kelvin_to_celsius(temp_kelvin),
                sea_surface_temp_c=None,  # OpenWeather does NOT provide SST
                observed_at=observed_at,
                source="openweather",
            )
        except Exception as exc:
            logger.warning("Failed to parse weather response: %s", exc)
            return None


# ── Offline / Cached Weather Store ─────────────────────────────────────

class OfflineWeatherStore:
    """
    Offline in-memory store of cached and demo weather records.

    Allows the weather layer to operate entirely offline without network access.
    """

    def __init__(self, samples_path: Optional[Path] = None):
        self._samples_path = samples_path or _DEFAULT_WEATHER_SAMPLES_PATH
        self._records: List[WeatherData] = []
        self._loaded = False

    def load(self) -> bool:
        """Load offline weather records from JSON file."""
        if not self._samples_path.exists():
            logger.warning("Weather samples file not found: %s", self._samples_path)
            return False

        try:
            with open(self._samples_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            self._records = []
            for item in raw_data:
                obs_time = parse_timestamp(item.get("observed_at"))
                record = WeatherData(
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    wind_speed_kmh=item.get("wind_speed_kmh"),
                    pressure_hpa=item.get("pressure_hpa"),
                    temperature_c=item.get("temperature_c"),
                    sea_surface_temp_c=None,  # Explicitly null
                    observed_at=obs_time,
                    source=item.get("source", "demo"),
                )
                self._records.append(record)

            self._loaded = len(self._records) > 0
            logger.info("Loaded %d offline weather records", len(self._records))
            return self._loaded

        except Exception as exc:
            logger.error("Failed to load offline weather records: %s", exc)
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def list_records(self) -> List[WeatherData]:
        """List all loaded offline weather records."""
        return list(self._records)

    def get_nearest(
        self, lat: float, lon: float, max_dist_km: float = 1000.0
    ) -> Optional[WeatherData]:
        """
        Find the nearest cached/demo weather record by coordinates.

        Returns closest record if within max_dist_km, or closest overall record.
        """
        if not self._records:
            return None

        best_record = None
        min_dist = float("inf")

        for rec in self._records:
            dist = haversine_km(lat, lon, rec.latitude, rec.longitude)
            if dist < min_dist:
                min_dist = dist
                best_record = rec

        if best_record and min_dist <= max_dist_km:
            return best_record

        # Return closest overall record if none within threshold
        return best_record
