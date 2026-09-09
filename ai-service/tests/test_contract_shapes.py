"""The AI service's responses must match API_CONTRACT.md exactly.

Three services are written against one contract, in three languages. Nothing catches
drift automatically, so this test pins the shapes that Spring Boot's records and the
frontend's TypeScript types are written against, and it exercises the real endpoint
rather than the schema in isolation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

AS_OF = datetime(2019, 5, 2, 6, 0, tzinfo=timezone.utc)
SID = "2019114N06084"

# Blocks that must carry a provenance stamp, and the field it lives in.
STAMPED_BLOCKS = {
    "current": ["source"],
    "structure": ["metricsSource", "regimeSource"],
    "vision": ["source"],
    "intensityForecast": ["source"],
    "trackForecast": ["source", "coneSource"],
    "analogues": ["source"],
    "risk": ["source"],
    "report": ["source"],
}


def history(hours_before: list[float]) -> list[dict]:
    return [
        {
            "t": (AS_OF - timedelta(hours=h)).isoformat(),
            "lat": 17.0 + h * 0.01,
            "lon": 85.0 + h * 0.01,
            "vmaxKt": 120.0,
            "pressureHpa": 950.0,
            "translationSpeedKt": 9.0,
            "headingDeg": 15.0,
            "distToCoastKm": 310.0,
        }
        for h in hours_before
    ]


def infer_full(client: TestClient, **overrides):
    payload = {"sid": SID, "asOf": AS_OF.isoformat(), "history": history([24, 12, 6, 0])}
    payload.update(overrides)
    return client.post("/infer/full", json=payload)


class TestInferFullShape:
    def test_returns_every_top_level_block(self):
        with TestClient(app) as client:
            response = infer_full(client)

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {
            "sid",
            "issuedFor",
            "modelBundleVersion",
            "current",
            "structure",
            "vision",
            "intensityForecast",
            "trackForecast",
            "analogues",
            "risk",
            "report",
        }

    def test_every_analysis_block_carries_a_provenance_stamp(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        for block, stamps in STAMPED_BLOCKS.items():
            for stamp in stamps:
                assert body[block][stamp] is not None, f"{block}.{stamp} is unstamped"
                assert "provenance" in body[block][stamp]

    def test_no_verification_field_is_returned(self):
        # Invariant I2: ground truth is the backend's to attach, from the database.
        with TestClient(app) as client:
            body = infer_full(client).json()

        assert "verification" not in body
        assert "degraded" not in body
        assert "servedFrom" not in body

    def test_observed_state_is_echoed_as_observed(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        assert body["current"]["source"]["provenance"] == "OBSERVED"
        assert body["current"]["vmaxKt"] == 120.0

    def test_untrained_blocks_are_stamped_demo_data(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        assert body["vision"]["source"]["provenance"] == "DEMO_DATA"
        assert body["intensityForecast"]["source"]["provenance"] == "DEMO_DATA"
        assert body["trackForecast"]["source"]["provenance"] == "DEMO_DATA"
        assert body["analogues"]["source"]["provenance"] == "DEMO_DATA"

    def test_untrained_models_return_absent_values_not_invented_ones(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        assert body["vision"]["vmaxKt"] is None
        assert body["intensityForecast"]["deltaVmax24hKt"] is None
        assert body["intensityForecast"]["riProbability"] is None
        assert body["risk"]["score"] is None

    def test_uncalibrated_cone_has_no_radii_but_explains_why(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        for point in body["trackForecast"]["points"]:
            assert point["coneRadiusP67Km"] is None
            assert point["coneRadiusP90Km"] is None
        assert "Not yet calibrated" in body["trackForecast"]["coneBasis"]

    def test_risk_returns_its_formula_even_when_it_cannot_score(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        assert body["risk"]["formula"]
        # The terms we do have are reported; the score is withheld.
        assert "vmaxNorm" in body["risk"]["terms"]

    def test_report_states_that_no_trained_model_contributed(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        assert "not yet trained" in body["report"]["text"]

    def test_structure_is_absent_without_imagery(self):
        with TestClient(app) as client:
            body = infer_full(client).json()

        assert body["structure"]["regime"] is None
        assert body["structure"]["axisymmetry"] is None
        assert body["structure"]["metricsSource"]["provenance"] == "DEMO_DATA"


class TestInferFullValidation:
    def test_future_history_is_rejected_with_422(self):
        with TestClient(app) as client:
            response = client.post(
                "/infer/full",
                json={
                    "sid": SID,
                    "asOf": AS_OF.isoformat(),
                    "history": history([6, 0]) + [
                        {
                            "t": (AS_OF + timedelta(hours=24)).isoformat(),
                            "lat": 19.6,
                            "lon": 85.8,
                            "vmaxKt": 135.0,
                        }
                    ],
                },
            )

        assert response.status_code == 422
        assert "temporal mask violation" in response.text

    def test_empty_history_is_rejected(self):
        with TestClient(app) as client:
            response = infer_full(client, history=[])
        assert response.status_code == 422


class TestAnalogueEndpoint:
    def test_returns_an_empty_stamped_block_before_the_index_exists(self):
        with TestClient(app) as client:
            response = client.post("/infer/analogues", json={"sid": SID, "k": 20})

        assert response.status_code == 200
        body = response.json()
        assert body["matches"] == []
        assert body["source"]["provenance"] == "DEMO_DATA"
        assert set(body["exclusions"]) == {"same-storm", "same-season"}


class TestFrameEndpoint:
    def test_analyses_a_frame_with_no_imagery_without_inventing_metrics(self):
        with TestClient(app) as client:
            response = client.post(
                "/infer/frame", json={"sid": SID, "t": AS_OF.isoformat()}
            )

        assert response.status_code == 200
        body = response.json()
        assert body["structure"]["eyePresent"] is None
        assert body["vision"]["vmaxKt"] is None
