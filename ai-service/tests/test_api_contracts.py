from datetime import datetime, timedelta
import io
import json
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "CycloVision AI Inference Service"
    assert data["stateless"] is True
    assert data["database_connected"] is False
    assert len(data["models_loaded"]) > 0


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert "subsystems" in data
    assert data["subsystems"]["vision"] == "ready"
    assert data["subsystems"]["trajectory"] == "ready"


def test_canonical_predict_full_complete_payload():
    t0 = datetime.utcnow() - timedelta(hours=6)
    t1 = datetime.utcnow()

    payload = {
        "cyclone_id": "2023145N04092",
        "name": "Cyclone Biparjoy",
        "basin": "NI",
        "current_intensity_kts": 85.0,
        "observations": [
            {
                "timestamp": t0.isoformat(),
                "latitude": 18.2,
                "longitude": 67.5,
                "max_sustained_wind_kts": 75.0,
                "central_pressure_hpa": 978.0,
                "forward_speed_kmh": 14.0,
                "forward_heading_deg": 345.0
            },
            {
                "timestamp": t1.isoformat(),
                "latitude": 19.1,
                "longitude": 67.2,
                "max_sustained_wind_kts": 85.0,
                "central_pressure_hpa": 970.0,
                "forward_speed_kmh": 16.0,
                "forward_heading_deg": 350.0
            }
        ],
        "environmental_context": {
            "sea_surface_temp_c": 29.8,
            "vertical_wind_shear_kts": 9.5,
            "ocean_heat_content_kj_cm2": 88.0,
            "mid_troposphere_humidity_pct": 75.0
        },
        "satellite_image": {
            "image_id": "sat-biparjoy-001",
            "image_url": "https://storage.cyclovision.internal/sat/biparjoy.jpg",
            "channel": "IR1",
            "resolution_km": 4.0
        },
        "historical_reference_limit": 3,
        "forecast_horizons_hours": [6, 12, 24, 48, 72]
    }

    response = client.post("/predict/full", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    # Core response metadata
    assert data["cyclone_id"] == "2023145N04092"
    assert data["prediction_id"].startswith("pred-2023145N04092-")
    assert "pipeline_version" in data
    assert "model_versions" in data

    # Subsystem outputs
    assert data["vision_analysis"] is not None
    assert data["vision_analysis"]["cyclone_detected"] is True
    assert data["vision_analysis"]["model_name"].startswith("ResNet34")

    # Trajectory points
    assert len(data["trajectory_forecast"]) == 5
    assert data["trajectory_forecast"][0]["forecast_hours"] == 6
    assert data["trajectory_forecast"][-1]["forecast_hours"] == 72
    for pt in data["trajectory_forecast"]:
        assert "latitude" in pt
        assert "longitude" in pt
        assert pt["uncertainty_radius_km"] > 0

    # Intensity forecast
    assert data["intensity_forecast"]["current_wind_kts"] == 85.0
    assert data["intensity_forecast"]["predicted_peak_wind_kts"] >= 85.0
    assert "intensity_trend" in data["intensity_forecast"]

    # Historical analogues
    assert len(data["historical_analogues"]) == 3
    assert data["historical_analogues"][0]["rank"] == 1
    assert data["historical_analogues"][0]["similarity_score"] > 0.8

    # Multi-hazard risk features
    assert "overall_risk_level" in data["risk_features"]
    assert 0.0 <= data["risk_features"]["storm_surge_risk_index"] <= 1.0
    assert 0.0 <= data["risk_features"]["wind_damage_risk_index"] <= 1.0

    # Explainability
    assert len(data["explainability"]["primary_driving_factors"]) > 0
    assert data["explainability"]["physics_consistency_valid"] is True
    assert len(data["explainability"]["reasoning_summary"]) > 0

    # Situation report
    assert data["situation_report"]["cyclone_id"] == "2023145N04092"
    assert len(data["situation_report"]["key_threats"]) > 0
    assert len(data["situation_report"]["recommended_actions"]) > 0


def test_canonical_predict_full_minimal_payload():
    now = datetime.utcnow()
    payload = {
        "cyclone_id": "min-001",
        "observations": [
            {
                "timestamp": now.isoformat(),
                "latitude": 12.0,
                "longitude": 84.0,
                "max_sustained_wind_kts": 45.0,
                "central_pressure_hpa": 995.0
            }
        ]
    }
    response = client.post("/predict/full", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["cyclone_id"] == "min-001"
    assert data["vision_analysis"] is None  # No satellite image provided
    assert len(data["trajectory_forecast"]) == 5  # Default [6, 12, 24, 48, 72]
    assert data["intensity_forecast"]["current_wind_kts"] == 45.0


def test_canonical_predict_full_base64_image():
    now = datetime.utcnow()
    payload = {
        "cyclone_id": "b64-001",
        "observations": [
            {
                "timestamp": now.isoformat(),
                "latitude": 14.0,
                "longitude": 85.0,
                "max_sustained_wind_kts": 55.0,
                "central_pressure_hpa": 990.0
            }
        ],
        "satellite_image": {
            "image_id": "img-b64",
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
            "channel": "VIS"
        }
    }
    response = client.post("/predict/full", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["vision_analysis"] is not None
    assert data["vision_analysis"]["features"]["input_source"] == "image_base64"


def test_canonical_predict_full_multipart_upload():
    now = datetime.utcnow()
    req_data = {
        "cyclone_id": "multipart-001",
        "name": "Cyclone Test",
        "observations": [
            {
                "timestamp": now.isoformat(),
                "latitude": 15.0,
                "longitude": 86.0,
                "max_sustained_wind_kts": 60.0,
                "central_pressure_hpa": 985.0
            }
        ]
    }
    fake_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"

    response = client.post(
        "/predict/full/multipart",
        data={"payload": json.dumps(req_data), "image_channel": "IR1"},
        files={"image_file": ("test_frame.png", io.BytesIO(fake_image_bytes), "image/png")}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["cyclone_id"] == "multipart-001"
    assert data["vision_analysis"] is not None
    assert data["vision_analysis"]["features"]["input_source"] == "multipart_bytes"


def test_predict_full_validation_errors():
    now = datetime.utcnow()

    # Case 1: Empty observations
    bad_payload_1 = {
        "cyclone_id": "bad-001",
        "observations": []
    }
    resp1 = client.post("/predict/full", json=bad_payload_1)
    assert resp1.status_code == 422

    # Case 2: Out of bounds latitude
    bad_payload_2 = {
        "cyclone_id": "bad-002",
        "observations": [
            {
                "timestamp": now.isoformat(),
                "latitude": 98.5,  # > 90.0
                "longitude": 80.0,
                "max_sustained_wind_kts": 50.0,
                "central_pressure_hpa": 990.0
            }
        ]
    }
    resp2 = client.post("/predict/full", json=bad_payload_2)
    assert resp2.status_code == 422

    # Case 3: Out of order timestamps
    bad_payload_3 = {
        "cyclone_id": "bad-003",
        "observations": [
            {
                "timestamp": now.isoformat(),
                "latitude": 15.0,
                "longitude": 80.0,
                "max_sustained_wind_kts": 50.0,
                "central_pressure_hpa": 990.0
            },
            {
                "timestamp": (now - timedelta(hours=3)).isoformat(),  # earlier!
                "latitude": 16.0,
                "longitude": 80.0,
                "max_sustained_wind_kts": 55.0,
                "central_pressure_hpa": 985.0
            }
        ]
    }
    resp3 = client.post("/predict/full", json=bad_payload_3)
    assert resp3.status_code == 422


def test_modular_satellite_analyze_endpoint():
    req = {
        "cyclone_id": "sat-001",
        "image_url": "https://example.com/sat.jpg",
        "channel": "IR1"
    }
    response = client.post("/api/v1/ai/satellite/analyze", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["cyclone_detected"] is True
    assert data["model_name"].startswith("ResNet34")


def test_modular_predict_track_endpoint():
    now = datetime.utcnow()
    req = {
        "cyclone_id": "track-001",
        "observations": [
            {
                "timestamp": now.isoformat(),
                "latitude": 16.0,
                "longitude": 88.0,
                "max_sustained_wind_kts": 65.0,
                "central_pressure_hpa": 980.0
            }
        ],
        "forecast_horizons_hours": [6, 12, 24]
    }
    response = client.post("/api/v1/ai/predict/track", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["cyclone_id"] == "track-001"
    assert len(data["forecast_points"]) == 3


def test_modular_similarity_match_endpoint():
    req = {
        "cyclone_id": "sim-001",
        "track_coordinates": [[15.0, 88.0], [16.0, 87.5]],
        "wind_intensity_history": [65.0, 75.0],
        "top_k": 2
    }
    response = client.post("/api/v1/ai/similarity/match", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["cyclone_id"] == "sim-001"
    assert len(data["matches"]) == 2


def test_modular_report_generate_endpoint():
    req = {
        "cyclone_id": "rep-001",
        "cyclone_name": "Mocha"
    }
    response = client.post("/api/v1/ai/report/generate", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["cyclone_id"] == "rep-001"
    assert data["cyclone_name"] == "Mocha"
    assert len(data["key_threats"]) > 0


def test_legacy_endpoints_compatibility():
    # 1. /analyze-vision
    res_vis = client.post("/analyze-vision", json={"cyclone_id": "leg-01"})
    assert res_vis.status_code == 200
    assert "cyclone_detected" in res_vis.json()

    # 2. /predict-trajectory
    res_traj = client.post("/predict-trajectory", json={"cyclone_id": "leg-02", "current_lat": 18.0, "current_long": 68.0, "wind_speed": 120.0})
    assert res_traj.status_code == 200
    assert "trajectory" in res_traj.json()

    # 3. /similar/{id}
    res_sim = client.get("/similar/leg-03")
    assert res_sim.status_code == 200
    assert len(res_sim.json()) > 0

    # 4. /report/{id}
    res_rep = client.get("/report/leg-04")
    assert res_rep.status_code == 200
    assert res_rep.json()["cyclone_id"] == "leg-04"
