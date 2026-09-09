"""
Unit tests for IBTrACSStore in src/ibtracs.py.
"""

import json
from pathlib import Path
import pytest
from src.ibtracs import IBTrACSStore
from src.models import IntensityCategory, DataMode


@pytest.fixture
def mock_ibtracs_data(tmp_path: Path):
    """Create a temporary directory with mock processed IBTrACS data."""
    cyclones = [
        {
            "id": "2020139N11086",
            "name": "AMPHAN",
            "basin": "NI",
            "season_year": 2020,
            "status": "historical",
        },
        {
            "id": "2019304N10074",
            "name": "MAHA",
            "basin": "NI",
            "season_year": 2019,
            "status": "historical",
        },
    ]

    observations = [
        {
            "cyclone_id": "2020139N11086",
            "observed_at": "2020-05-16T00:00:00+00:00",
            "latitude": 11.5,
            "longitude": 87.0,
            "wind_speed_kmh": 85.0,
            "pressure_hpa": 990.0,
            "movement_direction_deg": 340.0,
            "movement_speed_kmh": 10.0,
            "intensity_category": "Cyclonic Storm",
        },
        {
            "cyclone_id": "2020139N11086",
            "observed_at": "2020-05-18T06:00:00+00:00",
            "latitude": 14.8,
            "longitude": 86.3,
            "wind_speed_kmh": 240.0,
            "pressure_hpa": 920.0,
            "movement_direction_deg": 350.0,
            "movement_speed_kmh": 14.0,
            "intensity_category": "Super Cyclonic Storm",
        },
    ]

    with open(tmp_path / "cyclones.json", "w", encoding="utf-8") as f:
        json.dump(cyclones, f)

    with open(tmp_path / "observations.json", "w", encoding="utf-8") as f:
        json.dump(observations, f)

    return tmp_path


def test_ibtracs_store_load(mock_ibtracs_data: Path):
    store = IBTrACSStore(processed_dir=mock_ibtracs_data)
    assert store.load() is True
    assert store.is_loaded is True

    # Check cyclone fetch
    c = store.get_cyclone("2020139N11086")
    assert c is not None
    assert c.name == "AMPHAN"

    # Check search
    results = store.search_by_name("amph")
    assert len(results) == 1
    assert results[0].id == "2020139N11086"

    # Check observations & track
    obs = store.get_observations("2020139N11086")
    assert len(obs) == 2
    latest = store.get_latest_observation("2020139N11086")
    assert latest is not None
    assert latest.wind_speed_kmh == 240.0

    track = store.get_track("2020139N11086")
    assert len(track) == 2
    assert track[1]["category"] == "Super Cyclonic Storm"


def test_ibtracs_store_missing_file(tmp_path: Path):
    store = IBTrACSStore(processed_dir=tmp_path)
    assert store.load() is False
    assert store.is_loaded is False
    assert store.get_cyclone("non_existent") is None


def test_ibtracs_source_info(mock_ibtracs_data: Path):
    store = IBTrACSStore(processed_dir=mock_ibtracs_data)
    source_info = store.get_source_info()
    assert source_info.mode == DataMode.REAL
    assert "NOAA" in source_info.provider
