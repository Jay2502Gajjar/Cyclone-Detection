from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ObservationInput(BaseModel):
    """
    Time-series observation point provided by Spring Boot / IBTrACS ingestion
    """
    timestamp: datetime = Field(..., description="UTC observation timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Center latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Center longitude (-180 to 180)")
    max_sustained_wind_kts: float = Field(..., ge=0.0, le=300.0, description="Maximum sustained surface wind in knots")
    central_pressure_hpa: float = Field(..., ge=800.0, le=1050.0, description="Estimated central sea level pressure in hPa")
    forward_speed_kmh: Optional[float] = Field(None, ge=0.0, le=150.0, description="Translation speed in km/h")
    forward_heading_deg: Optional[float] = Field(None, ge=0.0, le=360.0, description="Direction of movement in degrees from true North")


class EnvironmentalContext(BaseModel):
    """
    Ambient atmospheric and oceanic conditions surrounding the cyclone vortex
    """
    sea_surface_temp_c: Optional[float] = Field(None, ge=10.0, le=40.0, description="SST in degrees Celsius")
    vertical_wind_shear_kts: Optional[float] = Field(None, ge=0.0, le=150.0, description="200-850 hPa vertical wind shear in knots")
    ocean_heat_content_kj_cm2: Optional[float] = Field(None, ge=0.0, le=300.0, description="Ocean heat content in kJ/cm²")
    mid_troposphere_humidity_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="700-500 hPa relative humidity percentage")


class TrajectoryForecastPoint(BaseModel):
    """
    Spatiotemporal forecast point projected for specific future horizon
    """
    forecast_hours: int = Field(..., ge=1, le=168, description="Lead time in hours (e.g. 6, 12, 24, 48, 72)")
    valid_timestamp: datetime = Field(..., description="Projected target UTC timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Forecasted latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Forecasted longitude")
    uncertainty_radius_km: float = Field(..., ge=0.0, description="Cone of uncertainty radius in km (68% confidence contour)")
    predicted_wind_kts: float = Field(..., ge=0.0, description="Predicted maximum sustained wind in knots")
    predicted_pressure_hpa: float = Field(..., ge=800.0, le=1050.0, description="Predicted central pressure in hPa")
    intensity_category: str = Field(..., description="Projected IMD/WMO category")


class LandfallEstimate(BaseModel):
    """
    Forecasted coastal landfall event prediction
    """
    landfall_expected: bool = Field(..., description="Whether model predicts landfall within forecast horizon")
    estimated_landfall_time: Optional[datetime] = Field(None, description="Estimated UTC landfall timestamp")
    landfall_location: Optional[str] = Field(None, description="Descriptive coastal landmark or district")
    landfall_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Landfall point latitude")
    landfall_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Landfall point longitude")
    confidence_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Landfall location confidence percentage")


class IntensityForecastResult(BaseModel):
    """
    Multi-horizon cyclone intensity projection & rapid intensification probability
    """
    current_wind_kts: float = Field(..., ge=0.0, description="Current baseline intensity in knots")
    predicted_peak_wind_kts: float = Field(..., ge=0.0, description="Highest forecasted wind speed across all horizons")
    intensity_trend: str = Field(..., description="Trend designation: INTENSIFYING, STEADY, WEAKENING, or RAPID_INTENSIFICATION")
    rapid_intensification_probability: float = Field(..., ge=0.0, le=1.0, description="RI probability (>= 30 kts increase in 24 hours)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Statistical confidence score")
    forecast_curve: List[Dict[str, Any]] = Field(default_factory=list, description="Intensity trajectory curve points")
