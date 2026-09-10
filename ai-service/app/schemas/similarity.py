from typing import List, Optional
from pydantic import BaseModel, Field


class HistoricalAnalogueResult(BaseModel):
    """
    Historical analogue storm retrieved via high-dimensional track/intensity similarity
    """
    rank: int = Field(..., ge=1, description="Analogue similarity ranking (1 = highest match)")
    historical_cyclone_id: str = Field(..., description="Unique IBTrACS or archive identifier")
    name: str = Field(..., description="Official storm name and season")
    season_year: int = Field(..., ge=1850, le=2100, description="Season year")
    basin: str = Field(default="NI", description="Basin code")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Normalized similarity metric (0.0 to 1.0)")
    peak_wind_kts: Optional[float] = Field(None, ge=0.0, description="Historical peak sustained wind in knots")
    min_pressure_hpa: Optional[float] = Field(None, ge=800.0, le=1050.0, description="Historical minimum central pressure in hPa")
    landfall_location: Optional[str] = Field(None, description="Recorded historical landfall area")
    analogous_traits: List[str] = Field(default_factory=list, description="Key dynamical traits shared with target storm")


class SimilarityMatchRequest(BaseModel):
    """
    Request model for standalone similarity matching
    """
    cyclone_id: str = Field(..., description="Identifier of target cyclone")
    track_coordinates: List[List[float]] = Field(
        ...,
        description="Chronological series of [latitude, longitude] pairs",
        min_length=1
    )
    wind_intensity_history: Optional[List[float]] = Field(
        None,
        description="Chronological series of observed max sustained wind speeds"
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Number of top analogues to return")


class SimilarityMatchResponse(BaseModel):
    """
    Response model for standalone similarity matching
    """
    cyclone_id: str
    matches: List[HistoricalAnalogueResult]
