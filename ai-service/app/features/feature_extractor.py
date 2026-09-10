from datetime import datetime
import math
from typing import Any, Dict, List, Optional
import numpy as np

# Physical constant: Earth angular rotation rate in rad/s
EARTH_ANGULAR_VELOCITY = 7.2921159e-5

FEATURE_NAMES = [
    "latitude",
    "longitude",
    "current_wind_kts",
    "current_pressure_hpa",
    "pressure_available",
    "translation_speed_kmh",
    "translation_heading_deg",
    "coriolis_param",
    "lag_6h_wind_change_kts",
    "lag_6h_available",
    "lag_6h_lat_change",
    "lag_6h_lon_change",
    "lag_12h_wind_change_kts",
    "season_month",
]


def compute_coriolis_parameter(latitude_deg: float) -> float:
    """
    Calculates the Coriolis parameter (planetary vorticity) f = 2 * Omega * sin(phi).
    Units: s^-1
    """
    rad = math.radians(latitude_deg)
    return 2.0 * EARTH_ANGULAR_VELOCITY * math.sin(rad)


def extract_features_at_time_t(
    current_obs: Dict[str, Any],
    history_obs: List[Dict[str, Any]],
    current_time: datetime,
) -> Dict[str, float]:
    """
    Extracts a 14-feature vector strictly using information available at or before time t.

    Data Leakage Prevention:
    - history_obs MUST ONLY contain observations with observed_at < current_time.
    - No future observations are ever inspected or accessed.

    Args:
        current_obs: Observation dictionary at time t.
        history_obs: List of prior observation dictionaries for the same cyclone (chronological, observed_at < t).
        current_time: UTC datetime of current_obs.

    Returns:
        Dictionary mapping each feature name in FEATURE_NAMES to a float value.
    """
    lat = float(current_obs["latitude"])
    lon = float(current_obs["longitude"])

    # Current wind in knots (IBTrACS processed dataset stores wind_speed_kmh)
    raw_wind_kmh = current_obs.get("wind_speed_kmh")
    if raw_wind_kmh is None:
        raise ValueError(f"current_obs must have a non-null wind_speed_kmh at prediction time t: {current_obs}")
    current_wind_kts = round(float(raw_wind_kmh) / 1.852, 2)

    # Current pressure (if missing, impute with climatological neutral 1010.0 hPa and set flag to 0.0)
    raw_pres = current_obs.get("pressure_hpa")
    if raw_pres is not None:
        current_pres_hpa = float(raw_pres)
        pressure_avail = 1.0
    else:
        current_pres_hpa = 1010.0
        pressure_avail = 0.0

    # Translation velocity at time t (derived from previous step to t by data-integration)
    translation_speed = float(current_obs.get("movement_speed_kmh") or 0.0)
    translation_heading = float(current_obs.get("movement_direction_deg") or 0.0)

    # Planetary vorticity
    coriolis = compute_coriolis_parameter(lat)

    # 6-hour lag feature search in history (looking backward from t)
    lag_6h_wind_change = 0.0
    lag_6h_avail = 0.0
    lag_6h_dlat = 0.0
    lag_6h_dlon = 0.0

    # 12-hour lag feature search in history
    lag_12h_wind_change = 0.0

    if history_obs:
        # Search backwards for closest observation to 6h ago (window: 4.5h to 7.5h)
        best_6h_diff = float("inf")
        best_6h_obs = None
        for prev in reversed(history_obs):
            prev_t = prev["_parsed_time"]
            dt_hours = (current_time - prev_t).total_seconds() / 3600.0
            if dt_hours > 7.5:
                break
            if 4.5 <= dt_hours <= 7.5:
                diff = abs(dt_hours - 6.0)
                if diff < best_6h_diff and prev.get("wind_speed_kmh") is not None:
                    best_6h_diff = diff
                    best_6h_obs = prev

        if best_6h_obs is not None:
            prev_wind_kts = float(best_6h_obs["wind_speed_kmh"]) / 1.852
            lag_6h_wind_change = round(current_wind_kts - prev_wind_kts, 2)
            lag_6h_avail = 1.0
            lag_6h_dlat = round(lat - float(best_6h_obs["latitude"]), 2)
            lag_6h_dlon = round(lon - float(best_6h_obs["longitude"]), 2)

        # Search backwards for closest observation to 12h ago (window: 10.0h to 14.0h)
        best_12h_diff = float("inf")
        best_12h_obs = None
        for prev in reversed(history_obs):
            prev_t = prev["_parsed_time"]
            dt_hours = (current_time - prev_t).total_seconds() / 3600.0
            if dt_hours > 14.0:
                break
            if 10.0 <= dt_hours <= 14.0:
                diff = abs(dt_hours - 12.0)
                if diff < best_12h_diff and prev.get("wind_speed_kmh") is not None:
                    best_12h_diff = diff
                    best_12h_obs = prev

        if best_12h_obs is not None:
            prev_12_wind_kts = float(best_12h_obs["wind_speed_kmh"]) / 1.852
            lag_12h_wind_change = round(current_wind_kts - prev_12_wind_kts, 2)

    season_month = float(current_time.month)

    feature_dict = {
        "latitude": lat,
        "longitude": lon,
        "current_wind_kts": current_wind_kts,
        "current_pressure_hpa": current_pres_hpa,
        "pressure_available": pressure_avail,
        "translation_speed_kmh": translation_speed,
        "translation_heading_deg": translation_heading,
        "coriolis_param": coriolis,
        "lag_6h_wind_change_kts": lag_6h_wind_change,
        "lag_6h_available": lag_6h_avail,
        "lag_6h_lat_change": lag_6h_dlat,
        "lag_6h_lon_change": lag_6h_dlon,
        "lag_12h_wind_change_kts": lag_12h_wind_change,
        "season_month": season_month,
    }

    return feature_dict


def feature_dict_to_vector(feature_dict: Dict[str, float]) -> np.ndarray:
    """
    Converts feature dictionary into a 1D float32 numpy array matching FEATURE_NAMES order.
    """
    return np.array([feature_dict[name] for name in FEATURE_NAMES], dtype=np.float32)
