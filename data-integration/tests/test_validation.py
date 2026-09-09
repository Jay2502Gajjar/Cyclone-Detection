"""
Unit tests for data validation logic in scripts/validate_data.py.
"""

import json
from pathlib import Path
import pytest
from scripts.validate_data import (
    validate_observations,
    validate_tracks,
    validate_demo_scenarios,
    run_validation,
)


def test_validate_observations_clean():
    obs = [
        {
            "cyclone_id": "CYC_01",
            "observed_at": "2020-05-18T00:00:00Z",
            "latitude": 15.0,
            "longitude": 85.0,
            "wind_speed_kmh": 120.0,
            "pressure_hpa": 980.0,
        },
        {
            "cyclone_id": "CYC_01",
            "observed_at": "2020-05-18T06:00:00Z",
            "latitude": 15.5,
            "longitude": 85.2,
            "wind_speed_kmh": 140.0,
            "pressure_hpa": 970.0,
        },
    ]
    stats = validate_observations(obs)
    assert stats["total"] == 2
    assert stats["valid"] == 2
    assert stats["invalid_coordinates"] == 0
    assert stats["duplicate_observations"] == 0


def test_validate_observations_with_issues():
    obs = [
        {
            "cyclone_id": "CYC_01",
            "observed_at": "2020-05-18T00:00:00Z",
            "latitude": 95.0,  # Invalid
            "longitude": 85.0,
            "wind_speed_kmh": 600.0,  # Unreasonable
        },
        {
            "cyclone_id": "CYC_01",
            "observed_at": "2020-05-18T00:00:00Z",  # Duplicate key
            "latitude": 15.0,
            "longitude": 85.0,
        },
    ]
    stats = validate_observations(obs)
    assert stats["invalid_coordinates"] == 1
    assert stats["duplicate_observations"] == 1
    assert len(stats["issues"]) >= 2


def test_validate_tracks():
    obs = [
        {
            "cyclone_id": "CYC_01",
            "observed_at": "2020-05-18T00:00:00Z",
            "latitude": 15.0,
            "longitude": 85.0,
        },
        {
            "cyclone_id": "CYC_01",
            "observed_at": "2020-05-18T06:00:00Z",
            "latitude": 15.5,
            "longitude": 85.2,
        },
    ]
    stats = validate_tracks(obs)
    assert stats["total_tracks"] == 1
    assert stats["valid_tracks"] == 1
    assert stats["tracks_with_issues"] == 0


def test_validate_demo_scenarios(tmp_path: Path):
    scenario_dir = tmp_path / "scenario_test"
    scenario_dir.mkdir()
    valid_scenario = {
        "scenario_id": "scenario_test",
        "title": "Test Title",
        "cyclone": {"id": "TEST_01", "name": "TEST"},
        "latest_observation": {
            "observed_at": "2020-01-01T00:00:00Z",
            "latitude": 10.0,
            "longitude": 70.0,
        },
        "source": {"mode": "demo"},
    }
    with open(scenario_dir / "scenario.json", "w", encoding="utf-8") as f:
        json.dump(valid_scenario, f)

    stats = validate_demo_scenarios(tmp_path)
    assert stats["total_scenarios"] == 1
    assert stats["valid_scenarios"] == 1
    assert len(stats["issues"]) == 0
