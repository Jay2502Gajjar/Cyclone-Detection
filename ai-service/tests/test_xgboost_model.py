from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pytest

from app.core.interfaces import IIntensityPredictor
from app.models.xgboost_intensity import (
    XGBoostIntensityPredictor,
    DEFAULT_MODEL_PATH,
    DEFAULT_METADATA_PATH,
)
from app.schemas.trajectory import ObservationInput, IntensityForecastResult
from app.features.feature_extractor import FEATURE_NAMES


def test_model_artifact_exists():
    assert DEFAULT_MODEL_PATH.exists(), f"Expected model artifact at {DEFAULT_MODEL_PATH}"
    assert DEFAULT_METADATA_PATH.exists(), f"Expected model metadata at {DEFAULT_METADATA_PATH}"


def test_xgboost_provider_initialization():
    predictor = XGBoostIntensityPredictor()
    assert isinstance(predictor, IIntensityPredictor)
    assert predictor.version == "XGBoost-Intensity-v1.0"
    assert predictor.metadata["feature_names"] == FEATURE_NAMES


def test_xgboost_provider_missing_artifact_failure(tmp_path):
    missing_path = tmp_path / "non_existent_model.json"
    with pytest.raises(FileNotFoundError) as excinfo:
        XGBoostIntensityPredictor(model_path=missing_path)
    assert "not found" in str(excinfo.value)


def test_deterministic_inference():
    predictor = XGBoostIntensityPredictor()
    t0 = datetime(2023, 6, 10, 6, 0, 0)
    t1 = datetime(2023, 6, 10, 12, 0, 0)

    obs = [
        ObservationInput(
            timestamp=t0,
            latitude=18.0,
            longitude=68.5,
            max_sustained_wind_kts=70.0,
            central_pressure_hpa=980.0,
            forward_speed_kmh=14.0,
            forward_heading_deg=345.0,
        ),
        ObservationInput(
            timestamp=t1,
            latitude=19.0,
            longitude=68.0,
            max_sustained_wind_kts=80.0,
            central_pressure_hpa=972.0,
            forward_speed_kmh=16.0,
            forward_heading_deg=350.0,
        ),
    ]

    res1 = predictor.predict_intensity(obs, horizons=[6, 12, 24, 48, 72])
    res2 = predictor.predict_intensity(obs, horizons=[6, 12, 24, 48, 72])

    assert isinstance(res1, IntensityForecastResult)
    assert res1.current_wind_kts == 80.0
    assert res1.predicted_peak_wind_kts == res2.predicted_peak_wind_kts
    assert res1.intensity_trend == res2.intensity_trend
    assert len(res1.forecast_curve) == 5
    assert res1.forecast_curve[2]["forecast_hour"] == 24
    # Predictions must be identical
    for pt1, pt2 in zip(res1.forecast_curve, res2.forecast_curve):
        assert pt1["projected_wind_kts"] == pt2["projected_wind_kts"]


def test_valid_prediction_range_and_physical_clamping():
    predictor = XGBoostIntensityPredictor()
    now = datetime.utcnow()

    # Extreme low wind
    low_obs = [
        ObservationInput(
            timestamp=now,
            latitude=10.0,
            longitude=85.0,
            max_sustained_wind_kts=20.0,
            central_pressure_hpa=1005.0,
        )
    ]
    res_low = predictor.predict_intensity(low_obs, horizons=[24])
    assert 10.0 <= res_low.predicted_peak_wind_kts <= 250.0

    # Extreme high wind
    high_obs = [
        ObservationInput(
            timestamp=now,
            latitude=20.0,
            longitude=65.0,
            max_sustained_wind_kts=135.0,
            central_pressure_hpa=920.0,
        )
    ]
    res_high = predictor.predict_intensity(high_obs, horizons=[24])
    assert 10.0 <= res_high.predicted_peak_wind_kts <= 250.0


def test_malformed_input_handling():
    predictor = XGBoostIntensityPredictor()
    with pytest.raises(ValueError) as excinfo:
        predictor.predict_intensity([], horizons=[24])
    assert "At least one ObservationInput is required" in str(excinfo.value)
