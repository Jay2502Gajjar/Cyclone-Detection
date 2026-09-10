from datetime import datetime, timedelta
import pytest
from pydantic import ValidationError

from app.schemas.common import Basin, IntensityCategory, RiskLevel, GeoPoint
from app.schemas.vision import SatelliteImageInput, SatelliteChannel, VisionAnalysisResult
from app.schemas.trajectory import (
    ObservationInput,
    EnvironmentalContext,
    TrajectoryForecastPoint,
    IntensityForecastResult,
)
from app.schemas.similarity import HistoricalAnalogueResult
from app.schemas.report import SituationReportResult
from app.schemas.full_pipeline import (
    RiskFeatureExtractionResult,
    ExplainabilityResult,
    FullPredictionRequest,
    FullPredictionResponse,
)


def test_geopoint_valid():
    pt = GeoPoint(latitude=18.5, longitude=72.8)
    assert pt.latitude == 18.5
    assert pt.longitude == 72.8


def test_geopoint_invalid():
    with pytest.raises(ValidationError):
        GeoPoint(latitude=95.0, longitude=72.8)  # lat > 90

    with pytest.raises(ValidationError):
        GeoPoint(latitude=18.5, longitude=185.0)  # lon > 180


def test_satellite_image_input_validation():
    # Valid with URL
    img = SatelliteImageInput(image_url="https://example.com/sat.jpg", channel=SatelliteChannel.IR1)
    assert img.image_url == "https://example.com/sat.jpg"

    # Valid with base64
    img_b64 = SatelliteImageInput(image_base64="aW1hZ2VkYXRhCg==", channel=SatelliteChannel.VIS)
    assert img_b64.image_base64 == "aW1hZ2VkYXRhCg=="

    # Invalid when both are missing
    with pytest.raises(ValidationError):
        SatelliteImageInput(image_id="img-01")


def test_observation_input_validation():
    now = datetime.utcnow()
    obs = ObservationInput(
        timestamp=now,
        latitude=15.5,
        longitude=65.2,
        max_sustained_wind_kts=75.0,
        central_pressure_hpa=975.0
    )
    assert obs.max_sustained_wind_kts == 75.0

    # Negative wind speed
    with pytest.raises(ValidationError):
        ObservationInput(
            timestamp=now,
            latitude=15.5,
            longitude=65.2,
            max_sustained_wind_kts=-5.0,
            central_pressure_hpa=975.0
        )

    # Out of bounds pressure
    with pytest.raises(ValidationError):
        ObservationInput(
            timestamp=now,
            latitude=15.5,
            longitude=65.2,
            max_sustained_wind_kts=75.0,
            central_pressure_hpa=500.0
        )


def test_full_prediction_request_chronological_validation():
    t0 = datetime.utcnow()
    t1 = t0 + timedelta(hours=6)
    t2 = t0 - timedelta(hours=6)  # Out of order!

    obs1 = ObservationInput(
        timestamp=t0,
        latitude=14.0,
        longitude=66.0,
        max_sustained_wind_kts=50.0,
        central_pressure_hpa=990.0
    )
    obs2 = ObservationInput(
        timestamp=t1,
        latitude=15.0,
        longitude=65.5,
        max_sustained_wind_kts=60.0,
        central_pressure_hpa=985.0
    )
    obs3 = ObservationInput(
        timestamp=t2,
        latitude=16.0,
        longitude=65.0,
        max_sustained_wind_kts=70.0,
        central_pressure_hpa=980.0
    )

    # Valid chronological order
    req_valid = FullPredictionRequest(
        cyclone_id="cyclone-001",
        observations=[obs1, obs2]
    )
    assert len(req_valid.observations) == 2

    # Invalid chronological order
    with pytest.raises(ValidationError) as excinfo:
        FullPredictionRequest(
            cyclone_id="cyclone-001",
            observations=[obs1, obs3]
        )
    assert "chronological order" in str(excinfo.value)


def test_forecast_horizons_validation():
    now = datetime.utcnow()
    obs = ObservationInput(
        timestamp=now,
        latitude=14.0,
        longitude=66.0,
        max_sustained_wind_kts=50.0,
        central_pressure_hpa=990.0
    )

    # Horizon with negative hours
    with pytest.raises(ValidationError):
        FullPredictionRequest(
            cyclone_id="cyclone-001",
            observations=[obs],
            forecast_horizons_hours=[6, -12, 24]
        )

    # Deduplication and sorting
    req = FullPredictionRequest(
        cyclone_id="cyclone-001",
        observations=[obs],
        forecast_horizons_hours=[24, 6, 12, 6]
    )
    assert req.forecast_horizons_hours == [6, 12, 24]
