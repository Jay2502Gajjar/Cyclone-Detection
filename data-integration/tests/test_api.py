"""
Unit tests for the isolated FastAPI server in api/server.py.
"""

import pytest
from fastapi.testclient import TestClient
from api.server import app, provider


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_api_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cyclovision-data-integration"
    assert "demo_mode" in data


def test_api_list_demo_scenarios(client):
    response = client.get("/demo/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) == 5
    ids = [s["scenario_id"] for s in scenarios]
    assert "scenario_01" in ids
    assert "scenario_02" in ids


def test_api_get_single_demo_scenario(client):
    response = client.get("/demo/scenarios/scenario_01")
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == "scenario_01"
    assert data["cyclone"]["name"] == "MAHA"


def test_api_get_demo_scenario_404(client):
    response = client.get("/demo/scenarios/non_existent_scenario")
    assert response.status_code == 404


def test_api_get_demo_envelope(client):
    response = client.get("/demo/envelope")
    assert response.status_code == 200
    envelope = response.json()
    assert "cyclone" in envelope
    assert "observation" in envelope
    assert "source" in envelope
    assert envelope["source"]["mode"] == "demo"


def test_api_list_cyclones(client):
    response = client.get("/cyclones")
    assert response.status_code == 200
    cyclones = response.json()
    assert len(cyclones) >= 1


def test_api_get_cyclone_metadata(client):
    response = client.get("/cyclones/DEMO_AMPHAN_2020")
    assert response.status_code == 200
    cyc = response.json()
    assert cyc["name"] == "AMPHAN"


def test_api_get_cyclone_observations(client):
    response = client.get("/cyclones/scenario_01/observations")
    assert response.status_code == 200
    obs = response.json()
    assert len(obs) >= 1


def test_api_get_cyclone_envelope(client):
    response = client.get("/cyclones/DEMO_MAHA_2019/envelope")
    assert response.status_code == 200
    env = response.json()
    assert env["cyclone"]["id"] == "DEMO_MAHA_2019"


def test_api_get_weather(client):
    response = client.get("/weather?lat=10.5&lon=73.2")
    assert response.status_code == 200
    weather = response.json()
    assert "temperature_c" in weather
    assert "wind_speed_kmh" in weather


def test_api_satellite_catalog(client):
    response = client.get("/satellite/catalog")
    assert response.status_code == 200
    catalog = response.json()
    assert len(catalog) >= 1
