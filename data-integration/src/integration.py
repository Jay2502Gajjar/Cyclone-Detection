"""
Unified data provider facade for the CycloVision integration layer.

This is the single entry point that other parts of the system should use
to obtain cyclone data. It orchestrates:
  1. IBTrACS historical data
  2. OpenWeather live weather client
  3. Offline cached weather store
  4. Satellite image catalog
  5. Demo mode fallback orchestrator

Priority chain:
  LIVE → CACHED / OFFLINE → DEMO
"""

from __future__ import annotations

import logging
from typing import List, Optional

from .models import (
    Cyclone, Observation, WeatherData, SatelliteImage,
    DataEnvelope, DemoScenario, SourceInfo, DataMode,
)
from .ibtracs import IBTrACSStore
from .satellite import SatelliteCatalog
from .weather import OpenWeatherClient, OfflineWeatherStore
from .demo_mode import DemoModeManager

logger = logging.getLogger(__name__)


class DataIntegrationProvider:
    """
    Facade that unifies all data sources behind a single interface.

    Usage:
        provider = DataIntegrationProvider()
        provider.initialize()
        envelope = provider.get_cyclone_data("2020136N10088")
    """

    def __init__(self):
        self.ibtracs = IBTrACSStore()
        self.satellite = SatelliteCatalog()
        self.weather_client = OpenWeatherClient()
        self.offline_weather = OfflineWeatherStore()
        self.demo = DemoModeManager()
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize all data sources.

        This loads processed data from disk and prepares the demo fallback.
        Call this once at startup.
        """
        self.ibtracs.load()
        self.satellite.load()
        self.offline_weather.load()
        self.demo.load_scenarios()
        self._initialized = True
        logger.info(
            "DataIntegrationProvider initialized — "
            "ibtracs=%s, satellite=%s, offline_weather=%s, demo=%s, demo_mode=%s",
            self.ibtracs.is_loaded,
            self.satellite.is_loaded,
            self.offline_weather.is_loaded,
            self.demo.is_loaded,
            DemoModeManager.is_demo_mode(),
        )

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ── Primary Data Access ───────────────────────────────────────────

    def get_cyclone_data(self, cyclone_id: str) -> Optional[DataEnvelope]:
        """
        Get a complete DataEnvelope for a cyclone.

        Attempts real data first (IBTrACS + weather + satellite),
        falling back to demo if anything fails or is unavailable.
        """
        # Attempt real data from IBTrACS if loaded
        if self.ibtracs.is_loaded:
            cyclone = self.ibtracs.get_cyclone(cyclone_id)
            if cyclone:
                latest_obs = self.ibtracs.get_latest_observation(cyclone_id)
                if latest_obs:
                    weather = self.get_weather(latest_obs.latitude, latest_obs.longitude)
                    sat_images = self.satellite.get_images_for_cyclone(cyclone_id)
                    satellite = sat_images[0] if sat_images else None
                    return DataEnvelope(
                        cyclone=cyclone,
                        observation=latest_obs,
                        weather=weather,
                        satellite=satellite,
                        source=SourceInfo(
                            mode=DataMode.REAL,
                            provider="ibtracs+openweather",
                        ),
                    )

        # Fallback to demo scenarios
        return self.demo.get_fallback_envelope(cyclone_id)

    def _try_live_weather(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Attempt to fetch live weather, returning None on failure."""
        try:
            return self.weather_client.fetch_current(lat, lon)
        except Exception as exc:
            logger.warning("Weather fetch failed: %s — continuing without", exc)
            return None

    # ── Listing / Search ──────────────────────────────────────────────

    def list_cyclones(
        self,
        basin: Optional[str] = None,
        season_year: Optional[int] = None,
        limit: int = 100,
    ) -> List[Cyclone]:
        """List cyclones from IBTrACS, or demo scenarios if unavailable."""
        if self.ibtracs.is_loaded:
            cyclones = self.ibtracs.list_cyclones(basin, season_year, limit)
            if cyclones:
                return cyclones

        # Fallback: return cyclones from demo scenarios
        return [s.cyclone for s in self.demo.list_scenarios()[:limit]]

    def get_observations(self, cyclone_id: str) -> List[Observation]:
        """Get observations for a cyclone."""
        if self.ibtracs.is_loaded:
            obs = self.ibtracs.get_observations(cyclone_id)
            if obs:
                return obs

        # Fallback: return from demo scenario
        scenario = self.demo.get_scenario(cyclone_id)
        if scenario:
            return [scenario.latest_observation] + scenario.historical_observations
        for s in self.demo.list_scenarios():
            if s.cyclone.id == cyclone_id:
                return [s.latest_observation] + s.historical_observations
        return []

    def get_weather(self, lat: float, lon: float) -> Optional[WeatherData]:
        """
        Get weather for a location with 3-tier fallback:
          1. LIVE: OpenWeather API (if DEMO_MODE=false and key exists)
          2. CACHED / OFFLINE: Local weather samples database
          3. DEMO: Default demo scenario weather
        """
        if not DemoModeManager.is_demo_mode():
            live_weather = self._try_live_weather(lat, lon)
            if live_weather:
                return live_weather

        # Tier 2: Cached / Offline store
        if self.offline_weather.is_loaded:
            cached_weather = self.offline_weather.get_nearest(lat, lon)
            if cached_weather:
                return cached_weather

        # Tier 3: Fallback to default demo scenario weather
        default = self.demo.get_default_scenario()
        return default.weather if default else None

    def list_demo_scenarios(self) -> List[DemoScenario]:
        """List all available demo scenarios."""
        return self.demo.list_scenarios()

    def get_demo_scenario(self, scenario_id: str) -> Optional[DemoScenario]:
        """Get a specific demo scenario."""
        return self.demo.get_scenario(scenario_id)
