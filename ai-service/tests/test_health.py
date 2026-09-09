"""Health and root endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

EXPECTED_COMPONENTS = {
    "ir_intensity",
    "dvmax_ri",
    "track_cliper",
    "track_cone",
    "analogue",
    "structure",
    "regime_rules",
    "risk_rules",
    "report_template",
}


def test_health_reports_degraded_with_no_trained_models():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    # DEGRADED is the correct Phase 0 answer, not a failure: nothing is trained yet.
    assert body["status"] == "DEGRADED"
    assert all(model["isTrained"] is False for model in body["models"])


def test_health_lists_every_registered_component():
    with TestClient(app) as client:
        body = client.get("/health").json()

    assert {model["key"] for model in body["models"]} == EXPECTED_COMPONENTS


def test_root_points_at_the_docs():
    with TestClient(app) as client:
        body = client.get("/").json()

    assert body["service"] == "cyclovision-ai"
    assert body["docs"] == "/docs"
