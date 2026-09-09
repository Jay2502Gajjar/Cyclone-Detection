"""
Unit tests for DemoModeManager in src/demo_mode.py.
"""

import json
from pathlib import Path
import pytest
from src.demo_mode import DemoModeManager
from src.models import DataMode


@pytest.fixture
def mock_scenarios_dir(tmp_path: Path):
    """Create temporary scenario folders with valid scenario.json."""
    scenario_01_dir = tmp_path / "scenario_01"
    scenario_01_dir.mkdir()

    scenario_01_data = {
        "scenario_id": "scenario_01",
        "title": "Developing Cyclone — MAHA (2019)",
        "description": "Cyclone MAHA in Arabian Sea",
        "cyclone": {
            "id": "DEMO_MAHA_2019",
            "name": "MAHA",
            "basin": "NI",
            "season_year": 2019,
            "status": "demo",
        },
        "latest_observation": {
            "observed_at": "2019-10-31T12:00:00Z",
            "latitude": 10.5,
            "longitude": 73.2,
            "wind_speed_kmh": 75.0,
            "pressure_hpa": 994.0,
            "movement_direction_deg": 310.0,
            "movement_speed_kmh": 12.0,
            "intensity_category": "Cyclonic Storm",
        },
        "historical_observations": [],
        "weather": {
            "latitude": 10.5,
            "longitude": 73.2,
            "wind_speed_kmh": 75.0,
            "pressure_hpa": 994.0,
            "temperature_c": 28.2,
            "source": "demo",
        },
        "satellite": None,
        "source": {
            "mode": "demo",
            "provider": "demo",
        },
    }

    with open(scenario_01_dir / "scenario.json", "w", encoding="utf-8") as f:
        json.dump(scenario_01_data, f)

    return tmp_path


def test_demo_mode_manager_load(mock_scenarios_dir: Path):
    dm = DemoModeManager(scenarios_dir=mock_scenarios_dir)
    assert dm.load_scenarios() is True
    assert dm.is_loaded is True

    scenarios = dm.list_scenarios()
    assert len(scenarios) == 1
    assert scenarios[0].scenario_id == "scenario_01"

    s1 = dm.get_scenario("scenario_01")
    assert s1 is not None
    assert s1.cyclone.name == "MAHA"

    # Test conversion to envelope
    env = dm.scenario_to_envelope(s1)
    assert env.cyclone.id == "DEMO_MAHA_2019"
    assert env.observation.wind_speed_kmh == 75.0
    assert env.source.mode == DataMode.DEMO


def test_demo_mode_manager_fallback(mock_scenarios_dir: Path):
    dm = DemoModeManager(scenarios_dir=mock_scenarios_dir)
    dm.load_scenarios()

    # Exact match
    env_match = dm.get_fallback_envelope("DEMO_MAHA_2019")
    assert env_match is not None
    assert env_match.cyclone.id == "DEMO_MAHA_2019"

    # Unknown ID falls back to default scenario
    env_default = dm.get_fallback_envelope("UNKNOWN_ID")
    assert env_default is not None
    assert env_default.cyclone.id == "DEMO_MAHA_2019"


def test_demo_mode_env_flag(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    assert DemoModeManager.is_demo_mode() is True

    monkeypatch.setenv("DEMO_MODE", "false")
    assert DemoModeManager.is_demo_mode() is False

    monkeypatch.setenv("DEMO_MODE", "1")
    assert DemoModeManager.is_demo_mode() is True

    monkeypatch.setenv("DEMO_MODE", "0")
    assert DemoModeManager.is_demo_mode() is False
