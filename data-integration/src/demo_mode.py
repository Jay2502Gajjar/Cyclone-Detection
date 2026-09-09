"""
DEMO_MODE fallback orchestrator.

Implements the data-source priority chain:
  1. Live / source data (IBTrACS, OpenWeather, satellite)
  2. Cached data
  3. Bundled demo scenario

When DEMO_MODE=true (env var), live sources are skipped entirely and
demo scenarios are served directly. When DEMO_MODE=false, the system
attempts live data first and falls back to demo on any failure.

A live demo MUST continue functioning when the network is disabled.
"""

from __future__ import annotations

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    Cyclone, Observation, WeatherData, SatelliteImage,
    DataEnvelope, DemoScenario, SourceInfo, DataMode,
)

logger = logging.getLogger(__name__)

_DEFAULT_SCENARIOS_DIR = Path(__file__).parent.parent / "data" / "demo" / "scenarios"


class DemoModeManager:
    """
    Manages demo scenarios and provides the fallback mechanism.

    Usage:
        dm = DemoModeManager()
        dm.load_scenarios()
        scenario = dm.get_scenario("scenario_01")
        envelope = dm.scenario_to_envelope(scenario)
    """

    def __init__(self, scenarios_dir: Optional[Path] = None):
        self._scenarios_dir = scenarios_dir or _DEFAULT_SCENARIOS_DIR
        self._scenarios: Dict[str, DemoScenario] = {}
        self._loaded = False

    @staticmethod
    def is_demo_mode() -> bool:
        """Check whether DEMO_MODE is enabled via environment variable."""
        return os.environ.get("DEMO_MODE", "true").lower() in ("true", "1", "yes")

    def load_scenarios(self) -> bool:
        """
        Load all demo scenarios from disk.

        Each scenario is a directory containing a scenario.json file.
        Returns True if at least one scenario was loaded.
        """
        if not self._scenarios_dir.exists():
            logger.warning("Demo scenarios directory not found: %s", self._scenarios_dir)
            return False

        loaded_count = 0
        for scenario_dir in sorted(self._scenarios_dir.iterdir()):
            if not scenario_dir.is_dir():
                continue
            scenario_file = scenario_dir / "scenario.json"
            if not scenario_file.exists():
                logger.debug("No scenario.json in %s — skipping", scenario_dir.name)
                continue

            try:
                with open(scenario_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                scenario = DemoScenario(**raw)
                self._scenarios[scenario.scenario_id] = scenario
                loaded_count += 1
                logger.debug("Loaded demo scenario: %s", scenario.scenario_id)
            except Exception as exc:
                logger.warning("Failed to load scenario %s: %s", scenario_dir.name, exc)

        self._loaded = loaded_count > 0
        logger.info("Loaded %d demo scenarios", loaded_count)
        return self._loaded

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Queries ───────────────────────────────────────────────────────

    def list_scenarios(self) -> List[DemoScenario]:
        """List all loaded demo scenarios."""
        return list(self._scenarios.values())

    def get_scenario(self, scenario_id: str) -> Optional[DemoScenario]:
        """Get a specific demo scenario by ID."""
        return self._scenarios.get(scenario_id)

    def get_default_scenario(self) -> Optional[DemoScenario]:
        """Get the first available scenario as a default."""
        if not self._scenarios:
            return None
        return next(iter(self._scenarios.values()))

    # ── Conversion ────────────────────────────────────────────────────

    def scenario_to_envelope(self, scenario: DemoScenario) -> DataEnvelope:
        """Convert a DemoScenario into a canonical DataEnvelope."""
        return DataEnvelope(
            cyclone=scenario.cyclone,
            observation=scenario.latest_observation,
            weather=scenario.weather,
            satellite=scenario.satellite,
            source=SourceInfo(
                mode=DataMode.DEMO,
                provider="demo",
                processing_script="scripts/create_demo_scenarios.py",
                processing_version="0.1.0",
            ),
        )

    # ── Fallback Logic ────────────────────────────────────────────────

    def get_fallback_envelope(
        self, cyclone_id: Optional[str] = None
    ) -> Optional[DataEnvelope]:
        """
        Get a DataEnvelope from demo data.

        If cyclone_id matches a scenario's cyclone ID, returns that scenario.
        Otherwise returns the default scenario.
        """
        if cyclone_id:
            for scenario in self._scenarios.values():
                if scenario.cyclone.id == cyclone_id:
                    return self.scenario_to_envelope(scenario)

        default = self.get_default_scenario()
        if default:
            return self.scenario_to_envelope(default)

        logger.error("No demo scenarios available for fallback")
        return None
