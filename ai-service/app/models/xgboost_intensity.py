from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import xgboost as xgb

from app.core.interfaces import IIntensityPredictor
from app.schemas.trajectory import (
    ObservationInput,
    EnvironmentalContext,
    IntensityForecastResult,
)
from app.schemas.vision import VisionAnalysisResult
from app.features.feature_extractor import (
    FEATURE_NAMES,
    extract_features_at_time_t,
    feature_dict_to_vector,
)

logger = logging.getLogger(__name__)

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"
DEFAULT_MODEL_PATH = DEFAULT_ARTIFACTS_DIR / "xgboost_intensity_v1.json"
DEFAULT_METADATA_PATH = DEFAULT_ARTIFACTS_DIR / "xgboost_intensity_v1_metadata.json"


def _wind_to_category(wind_kts: float) -> str:
    """Classifies wind speed in knots to IMD intensity category."""
    if wind_kts < 17:
        return "Low Pressure Area"
    elif wind_kts <= 27:
        return "Depression"
    elif wind_kts <= 33:
        return "Deep Depression"
    elif wind_kts <= 47:
        return "Cyclonic Storm"
    elif wind_kts <= 63:
        return "Severe Cyclonic Storm"
    elif wind_kts <= 89:
        return "Very Severe Cyclonic Storm"
    elif wind_kts <= 119:
        return "Extremely Severe Cyclonic Storm"
    else:
        return "Super Cyclonic Storm"


class XGBoostIntensityPredictor(IIntensityPredictor):
    """
    Concrete 24-Hour Tropical Cyclone Intensity Predictor using trained XGBoost regression.
    Implements the IIntensityPredictor interface.
    """
    def __init__(
        self,
        model_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
    ):
        self._model_path = model_path or DEFAULT_MODEL_PATH
        self._metadata_path = metadata_path or DEFAULT_METADATA_PATH

        if not self._model_path.exists():
            raise FileNotFoundError(f"Trained XGBoost model artifact not found at: {self._model_path}")

        # Load booster once during initialization
        self._booster = xgb.Booster()
        try:
            self._booster.load_model(str(self._model_path))
        except Exception as exc:
            raise RuntimeError(f"Failed to load XGBoost model from {self._model_path}: {exc}") from exc

        # Load and validate metadata if present
        self._metadata: Dict[str, Any] = {}
        if self._metadata_path.exists():
            with open(self._metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

            # Validate feature schema alignment
            meta_features = self._metadata.get("feature_names", [])
            if meta_features and meta_features != FEATURE_NAMES:
                raise ValueError(
                    f"Feature ordering mismatch in model metadata! Expected {FEATURE_NAMES}, got {meta_features}"
                )

        self._version = self._metadata.get("model_name", "XGBoost-Intensity-v1.0")
        logger.info("Successfully loaded %s from %s", self._version, self._model_path)

    @property
    def version(self) -> str:
        return self._version

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def predict_intensity(
        self,
        observations: List[ObservationInput],
        horizons: List[int],
        env: Optional[EnvironmentalContext] = None,
        vision_result: Optional[VisionAnalysisResult] = None,
    ) -> IntensityForecastResult:
        if not observations:
            raise ValueError("At least one ObservationInput is required for intensity prediction.")

        # Sort observations chronologically to guarantee temporal integrity
        sorted_obs = sorted(observations, key=lambda o: o.timestamp)
        latest = sorted_obs[-1]
        history = sorted_obs[:-1]
        cur_wind = latest.max_sustained_wind_kts

        # Convert ObservationInput objects to feature extraction dictionary format
        current_dict = {
            "latitude": latest.latitude,
            "longitude": latest.longitude,
            "wind_speed_kmh": latest.max_sustained_wind_kts * 1.852,
            "pressure_hpa": latest.central_pressure_hpa,
            "movement_speed_kmh": latest.forward_speed_kmh,
            "movement_direction_deg": latest.forward_heading_deg,
        }

        history_dicts = []
        for prev in history:
            history_dicts.append({
                "_parsed_time": prev.timestamp,
                "latitude": prev.latitude,
                "longitude": prev.longitude,
                "wind_speed_kmh": prev.max_sustained_wind_kts * 1.852,
                "pressure_hpa": prev.central_pressure_hpa,
                "movement_speed_kmh": prev.forward_speed_kmh,
                "movement_direction_deg": prev.forward_heading_deg,
            })

        # Extract 14-feature vector
        feat_dict = extract_features_at_time_t(current_dict, history_dicts, latest.timestamp)
        feat_vec = feature_dict_to_vector(feat_dict)

        # Predict using XGBoost booster
        dmatrix = xgb.DMatrix(feat_vec.reshape(1, -1))
        raw_pred_24h = float(self._booster.predict(dmatrix)[0])

        # Physical clamping (knots)
        pred_24h = round(max(10.0, min(250.0, raw_pred_24h)), 1)
        wind_delta_24h = pred_24h - cur_wind

        # Determine intensity trend & RI probability
        if wind_delta_24h >= 30.0:
            trend = "RAPID_INTENSIFICATION"
            ri_prob = 0.85
        elif wind_delta_24h >= 10.0:
            trend = "INTENSIFYING"
            ri_prob = min(0.60, max(0.15, round(wind_delta_24h / 50.0, 2)))
        elif wind_delta_24h <= -10.0:
            trend = "WEAKENING"
            ri_prob = 0.02
        else:
            trend = "STEADY"
            ri_prob = 0.08

        # Generate intensity forecast curve across requested horizons
        sorted_horizons = sorted(horizons)
        curve = []
        max_h = max(sorted_horizons) if sorted_horizons else 24

        for h in sorted_horizons:
            if h <= 24:
                # Linear progression toward the 24h predicted anchor
                h_wind = cur_wind + (pred_24h - cur_wind) * (h / 24.0)
            else:
                # Beyond 24h: conservative asymptotic trend decay
                decay_factor = (h - 24.0) / max(1.0, max_h - 24.0)
                h_wind = pred_24h + (wind_delta_24h * 0.35) * decay_factor

            h_wind_clamped = round(max(10.0, min(250.0, h_wind)), 1)
            curve.append({
                "forecast_hour": h,
                "projected_wind_kts": h_wind_clamped,
                "category": _wind_to_category(h_wind_clamped)
            })

        predicted_peak = max([pt["projected_wind_kts"] for pt in curve] + [cur_wind])

        return IntensityForecastResult(
            current_wind_kts=round(cur_wind, 1),
            predicted_peak_wind_kts=round(predicted_peak, 1),
            intensity_trend=trend,
            rapid_intensification_probability=round(ri_prob, 2),
            confidence_score=0.86,
            forecast_curve=curve
        )
