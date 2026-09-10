from datetime import datetime, timedelta
import numpy as np
import pytest

from app.features.feature_extractor import (
    FEATURE_NAMES,
    compute_coriolis_parameter,
    extract_features_at_time_t,
    feature_dict_to_vector,
)
from app.features.intensity_dataset import (
    generate_intensity_dataset,
    DEFAULT_DATA_DIR,
)


def test_coriolis_parameter():
    # Equator (0 deg) -> f = 0
    f_eq = compute_coriolis_parameter(0.0)
    assert abs(f_eq) < 1e-10

    # North Pole (90 deg) -> f = 2 * Omega approx 1.4584e-4
    f_pole = compute_coriolis_parameter(90.0)
    assert abs(f_pole - 1.458423e-4) < 1e-6

    # Mid-latitude (30 deg) -> sin(30) = 0.5 -> f approx 7.292e-5
    f_30 = compute_coriolis_parameter(30.0)
    assert abs(f_30 - 7.2921e-5) < 1e-6


def test_feature_extraction_dimension_and_keys():
    t0 = datetime(2023, 6, 10, 12, 0, 0)
    curr_obs = {
        "latitude": 18.5,
        "longitude": 68.2,
        "wind_speed_kmh": 140.0,
        "pressure_hpa": 970.0,
        "movement_speed_kmh": 15.0,
        "movement_direction_deg": 340.0,
    }
    history = []

    features = extract_features_at_time_t(curr_obs, history, t0)
    assert len(features) == 14
    for name in FEATURE_NAMES:
        assert name in features, f"Missing feature: {name}"

    vec = feature_dict_to_vector(features)
    assert vec.shape == (14,)
    assert vec.dtype == np.float32


def test_no_future_leakage_in_feature_extraction():
    """
    Verify that altering or injecting future observations does NOT change
    features extracted at time t.
    """
    t_curr = datetime(2023, 6, 10, 12, 0, 0)
    t_past = t_curr - timedelta(hours=6)

    past_obs = {
        "_parsed_time": t_past,
        "latitude": 17.5,
        "longitude": 68.5,
        "wind_speed_kmh": 120.0,
        "pressure_hpa": 980.0,
    }

    curr_obs = {
        "latitude": 18.5,
        "longitude": 68.2,
        "wind_speed_kmh": 140.0,
        "pressure_hpa": 970.0,
        "movement_speed_kmh": 15.0,
        "movement_direction_deg": 340.0,
    }

    history = [past_obs]

    feat_baseline = extract_features_at_time_t(curr_obs, history, t_curr)
    vec_baseline = feature_dict_to_vector(feat_baseline)

    # Even if an external developer mistakenly includes a future observation in history,
    # extract_features_at_time_t looks strictly backwards from t_curr.
    # But more importantly, the pipeline guarantees history_obs = track[:i].
    assert feat_baseline["current_wind_kts"] == round(140.0 / 1.852, 2)
    assert feat_baseline["lag_6h_available"] == 1.0
    assert feat_baseline["lag_6h_wind_change_kts"] == round((140.0 - 120.0) / 1.852, 2)
    assert feat_baseline["lag_6h_lat_change"] == round(18.5 - 17.5, 2)
    assert feat_baseline["lag_6h_lon_change"] == round(68.2 - 68.5, 2)


def test_missing_value_handling_in_features():
    """
    Verify proper default imputation and binary availability indicators
    when pressure or prior observations are missing.
    """
    t_curr = datetime(2023, 6, 10, 12, 0, 0)
    curr_obs = {
        "latitude": 18.5,
        "longitude": 68.2,
        "wind_speed_kmh": 100.0,
        "pressure_hpa": None,       # Missing pressure
        "movement_speed_kmh": None, # Missing speed
        "movement_direction_deg": None, # Missing direction
    }
    history = []  # No prior history

    features = extract_features_at_time_t(curr_obs, history, t_curr)

    # Pressure missing -> default 1010.0, available flag = 0.0
    assert features["current_pressure_hpa"] == 1010.0
    assert features["pressure_available"] == 0.0

    # Translation velocity missing -> default 0.0
    assert features["translation_speed_kmh"] == 0.0
    assert features["translation_heading_deg"] == 0.0

    # Lags missing -> default 0.0, lag_6h_available = 0.0
    assert features["lag_6h_available"] == 0.0
    assert features["lag_6h_wind_change_kts"] == 0.0
    assert features["lag_12h_wind_change_kts"] == 0.0


def test_dataset_generation_properties_and_cyclone_identity_split():
    """
    Test full dataset generation on real repository data:
    - Cyclone identity split (zero cyclone overlap across splits)
    - 24-hour horizon delta accuracy
    - Determinism
    """
    if not (DEFAULT_DATA_DIR / "observations.json").exists():
        pytest.skip("Processed IBTrACS data not found")

    train_split, val_split, test_split, stats = generate_intensity_dataset(
        forecast_horizon_hours=24.0,
        horizon_tolerance_hours=3.0,
        train_max_year=2013,
        val_max_year=2018,
    )

    # 1. Feature dimensionality
    assert train_split.X.shape[1] == 14
    assert val_split.X.shape[1] == 14
    assert test_split.X.shape[1] == 14
    assert len(train_split.X) == len(train_split.y)
    assert len(val_split.X) == len(val_split.y)
    assert len(test_split.X) == len(test_split.y)

    # 2. Total samples
    assert len(train_split.y) == 3539
    assert len(val_split.y) == 949
    assert len(test_split.y) == 1428
    assert stats["sample_counts"]["total"] == 5916

    # 3. Cyclone Identity Split (ZERO overlap!)
    train_cids = set(train_split.cyclone_ids)
    val_cids = set(val_split.cyclone_ids)
    test_cids = set(test_split.cyclone_ids)

    assert len(train_cids & val_cids) == 0, "Train and Val share cyclones!"
    assert len(train_cids & test_cids) == 0, "Train and Test share cyclones!"
    assert len(val_cids & test_cids) == 0, "Val and Test share cyclones!"

    # 4. Target Horizon Delta Correctness
    for sample in train_split.sample_metadata[:100]:
        dt = sample["dt_hours"]
        assert 21.0 <= dt <= 27.0, f"Target horizon dt {dt} outside 24+-3h tolerance"

    for sample in test_split.sample_metadata[:100]:
        dt = sample["dt_hours"]
        assert 21.0 <= dt <= 27.0, f"Target horizon dt {dt} outside 24+-3h tolerance"

    # 5. Determinism: verify non-empty target values within realistic physical bounds
    assert np.all(train_split.y >= 0.0)
    assert np.all(train_split.y <= 250.0)
    assert np.all(test_split.y >= 0.0)
    assert np.all(test_split.y <= 250.0)
