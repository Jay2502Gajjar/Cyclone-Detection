"""
Tests for Data Integration API compatibility with the Spring Boot backend contract.

Verifies:
1. End-to-end HTTP endpoint responses using FastAPI TestClient.
2. Field-level serialization compatibility with Spring Boot ExternalCycloneDto, ExternalObservationDto, and DataEnvelope.
3. Representative cyclones: AMPHAN, FANI, BIPARJOY, MOCHA, and REMAL.
4. Ordering, timestamps (ISO-8601 UTC), unit formats (km/h, hPa, degrees).
5. Error handling and 404 responses for invalid IDs.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from api.server import app, provider
from src.models import (
    Cyclone,
    Observation,
    WeatherData,
    SatelliteImage,
    DataEnvelope,
    IntensityCategory,
)


@pytest.fixture(scope="module")
def client():
    """Create test client with initialized data integration provider."""
    provider.initialize()
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_endpoint(client):
    """Verify /health response structure and provider status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cyclovision-data-integration"
    assert "sources" in data
    assert data["sources"]["ibtracs_loaded"] is True
    assert data["sources"]["ibtracs_cyclones_count"] > 0


def test_list_cyclones_backend_compatibility(client):
    """Verify /cyclones response is deserializable into Spring Boot ExternalCycloneDto."""
    response = client.get("/cyclones?limit=50")
    assert response.status_code == 200
    cyclones = response.json()
    assert isinstance(cyclones, list)
    assert len(cyclones) > 0

    for c in cyclones:
        # Expected fields in backend contract
        assert "id" in c and isinstance(c["id"], str) and len(c["id"]) > 0
        assert "name" in c and isinstance(c["name"], str)
        assert "basin" in c and isinstance(c["basin"], str)
        assert "season_year" in c and isinstance(c["season_year"], int)
        assert "status" in c and isinstance(c["status"], str)


@pytest.mark.parametrize(
    "cyclone_name,expected_sid,expected_min_year",
    [
        ("AMPHAN", "2020136N10088", 2020),
        ("FANI", "2019116N02090", 2019),
        ("BIPARJOY", "2023156N10067", 2023),
        ("MOCHA", "2023129N08091", 2023),
        ("REMAL", "2024145N14087", 2024),
    ],
)
def test_representative_cyclone_metadata_endpoints(
    client, cyclone_name, expected_sid, expected_min_year
):
    """Verify metadata endpoints for representative storms."""
    response = client.get(f"/cyclones/{expected_sid}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == expected_sid
    assert data["name"] == cyclone_name
    assert data["basin"] == "NI"
    assert data["season_year"] == expected_min_year


@pytest.mark.parametrize(
    "cyclone_name,expected_sid,min_obs_count",
    [
        ("AMPHAN", "2020136N10088", 50),
        ("FANI", "2019116N02090", 70),
        ("BIPARJOY", "2023156N10067", 100),
        ("MOCHA", "2023129N08091", 50),
        ("REMAL", "2024145N14087", 40),
    ],
)
def test_representative_cyclone_observations_backend_mapping(
    client, cyclone_name, expected_sid, min_obs_count
):
    """Verify observations response fields, ordering, and data types for backend ingestion."""
    response = client.get(f"/cyclones/{expected_sid}/observations")
    assert response.status_code == 200
    observations = response.json()
    assert isinstance(observations, list)
    assert len(observations) >= min_obs_count

    prev_dt = None
    for obs in observations:
        # Timestamp verification (ISO-8601 parseable)
        assert "observed_at" in obs
        dt = datetime.fromisoformat(obs["observed_at"].replace("Z", "+00:00"))
        if prev_dt:
            assert dt >= prev_dt, "Observations must be chronologically sorted"
        prev_dt = dt

        # Coordinates
        assert -90.0 <= obs["latitude"] <= 90.0
        assert -180.0 <= obs["longitude"] <= 180.0

        # Meteorological fields
        if obs["wind_speed_kmh"] is not None:
            assert obs["wind_speed_kmh"] >= 0.0
        if obs["pressure_hpa"] is not None:
            assert 800.0 <= obs["pressure_hpa"] <= 1100.0
        if obs["movement_direction_deg"] is not None:
            assert 0.0 <= obs["movement_direction_deg"] <= 360.0
        if obs["movement_speed_kmh"] is not None:
            assert obs["movement_speed_kmh"] >= 0.0

        assert "intensity_category" in obs


def test_data_envelope_structure_and_completeness(client):
    """Verify DataEnvelope response contains all composite entities."""
    response = client.get("/cyclones/2020136N10088/envelope")
    assert response.status_code == 200
    envelope = response.json()

    # Top-level keys
    assert "cyclone" in envelope
    assert "observation" in envelope
    assert "weather" in envelope
    assert "satellite" in envelope
    assert "source" in envelope

    # Nested Cyclone
    assert envelope["cyclone"]["name"] == "AMPHAN"
    assert envelope["cyclone"]["id"] == "2020136N10088"

    # Nested Observation
    assert "observed_at" in envelope["observation"]
    assert "wind_speed_kmh" in envelope["observation"]

    # Source Provenance
    assert "ibtracs" in envelope["source"]["provider"]
    assert envelope["source"]["mode"] == "real"


def test_demo_envelope_fallback(client):
    """Verify /demo/envelope endpoint returns valid complete envelope."""
    response = client.get("/demo/envelope")
    assert response.status_code == 200
    envelope = response.json()
    assert envelope["cyclone"]["id"] is not None
    assert envelope["observation"]["latitude"] is not None
    assert envelope["weather"] is not None
    assert envelope["satellite"] is not None


def test_nonexistent_cyclone_404_error_handling(client):
    """Verify 404 response for non-existent cyclone ID."""
    response = client.get("/cyclones/NONEXISTENT_SID_99999")
    assert response.status_code == 404
    assert "detail" in response.json()

    obs_response = client.get("/cyclones/NONEXISTENT_SID_99999/observations")
    assert obs_response.status_code == 404
    assert "detail" in obs_response.json()
