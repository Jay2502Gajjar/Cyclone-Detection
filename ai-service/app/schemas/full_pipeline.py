from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.common import Basin, RiskLevel
from app.schemas.vision import SatelliteImageInput, VisionAnalysisResult
from app.schemas.trajectory import (
    ObservationInput,
    EnvironmentalContext,
    TrajectoryForecastPoint,
    LandfallEstimate,
    IntensityForecastResult,
)
from app.schemas.similarity import HistoricalAnalogueResult
from app.schemas.report import SituationReportResult


class RiskFeatureExtractionResult(BaseModel):
    """
    Multi-dimensional natural disaster risk evaluation scores
    """
    overall_risk_level: RiskLevel = Field(..., description="Categorical risk assessment: LOW, MODERATE, HIGH, SEVERE, EXTREME")
    storm_surge_risk_index: float = Field(..., ge=0.0, le=1.0, description="Estimated coastal surge hazard index (0.0 to 1.0)")
    wind_damage_risk_index: float = Field(..., ge=0.0, le=1.0, description="Wind damage severity hazard index (0.0 to 1.0)")
    inland_flooding_risk_index: float = Field(..., ge=0.0, le=1.0, description="Precipitation/flooding hazard index (0.0 to 1.0)")
    coastal_vulnerability_score: float = Field(..., ge=0.0, le=1.0, description="Combined shoreline exposure and vulnerability index")
    primary_concerns: List[str] = Field(default_factory=list, description="Explicit bulleted operational hazards")


class ExplainabilityResult(BaseModel):
    """
    Model interpretability and physics consistency breakdown
    """
    primary_driving_factors: List[str] = Field(
        default_factory=list,
        description="Top meteorological features driving this forecast (e.g. low shear, high SST)"
    )
    feature_importance: Dict[str, float] = Field(
        default_factory=dict,
        description="Relative importance weights normalized across input feature domain"
    )
    physics_consistency_valid: bool = Field(
        ...,
        description="Whether trajectory/intensity projections obey physical constraints (e.g. pressure-wind relationships)"
    )
    reasoning_summary: str = Field(
        ...,
        description="Clear English narrative explaining the physical logic of the predictions"
    )


class FullPredictionRequest(BaseModel):
    """
    Canonical request payload sent by Spring Boot to FastAPI for full-pipeline inference.
    Spring Boot supplies all context from database/ingestion; AI service is 100% stateless.
    """
    cyclone_id: str = Field(..., description="Unique cyclone identifier (e.g., IBTrACS ID or UUID)")
    name: Optional[str] = Field(default="Unnamed Cyclone", description="Storm name if named")
    basin: Basin = Field(default=Basin.NI, description="Oceanic basin (default NI = North Indian Ocean)")
    current_intensity_kts: Optional[float] = Field(None, ge=0.0, le=300.0, description="Current known maximum sustained wind speed in knots")
    observations: List[ObservationInput] = Field(
        ...,
        min_length=1,
        description="Chronological time series of historical storm observations (at least 1 required)"
    )
    environmental_context: Optional[EnvironmentalContext] = Field(
        None,
        description="Ambient atmospheric and ocean context (SST, shear, heat content)"
    )
    satellite_image: Optional[SatelliteImageInput] = Field(
        None,
        description="Optional satellite imagery frame for deep vision feature extraction"
    )
    historical_reference_limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of historical analog storms to retrieve"
    )
    forecast_horizons_hours: List[int] = Field(
        default=[6, 12, 24, 48, 72],
        min_length=1,
        description="Forecast lead times in hours (e.g. [6, 12, 24, 48, 72])"
    )

    @field_validator("observations")
    def validate_chronological_order(cls, v: List[ObservationInput]) -> List[ObservationInput]:
        if len(v) > 1:
            for i in range(1, len(v)):
                if v[i].timestamp < v[i-1].timestamp:
                    raise ValueError(f"Observations must be in chronological order: index {i} has timestamp {v[i].timestamp} earlier than index {i-1} ({v[i-1].timestamp})")
        return v

    @field_validator("forecast_horizons_hours")
    def validate_positive_horizons(cls, v: List[int]) -> List[int]:
        for h in v:
            if h <= 0:
                raise ValueError(f"Forecast horizon hours must be strictly positive integers; got {h}")
        return sorted(list(set(v)))


class FullPredictionResponse(BaseModel):
    """
    Canonical response payload returned to Spring Boot containing complete multi-modal intelligence.
    """
    model_config = ConfigDict(protected_namespaces=())

    prediction_id: str = Field(..., description="Unique generated prediction identifier")
    cyclone_id: str = Field(..., description="Target cyclone identifier")
    generated_at: datetime = Field(..., description="UTC generation timestamp")
    pipeline_version: str = Field(default="CycloVision-Full-Pipeline-v1.0", description="Pipeline framework version")
    model_versions: Dict[str, str] = Field(..., description="Inventory of component model versions used")
    vision_analysis: Optional[VisionAnalysisResult] = Field(None, description="Extracted satellite vision analysis (if image provided)")
    trajectory_forecast: List[TrajectoryForecastPoint] = Field(..., description="Multi-horizon trajectory coordinates and cones")
    landfall_estimate: Optional[LandfallEstimate] = Field(None, description="Landfall timing and coastal point estimate")
    intensity_forecast: IntensityForecastResult = Field(..., description="Intensity trajectory and rapid intensification metrics")
    historical_analogues: List[HistoricalAnalogueResult] = Field(..., description="Top matching historical storm analogues")
    risk_features: RiskFeatureExtractionResult = Field(..., description="Synthesized multi-hazard risk indices")
    explainability: ExplainabilityResult = Field(..., description="Explainability narrative and feature importance breakdown")
    situation_report: SituationReportResult = Field(..., description="Complete civil defense situation report")
