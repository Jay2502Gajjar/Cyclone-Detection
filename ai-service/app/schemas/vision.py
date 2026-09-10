from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


class SatelliteChannel(str, Enum):
    IR1 = "IR1"               # Infrared Thermal (10.8 µm)
    IR2 = "IR2"               # Infrared Thermal (12.0 µm)
    VIS = "VIS"               # Visible Spectrum
    WV = "WV"                 # Water Vapor (6.7 µm)
    SWIR = "SWIR"             # Shortwave Infrared (3.9 µm)
    ENHANCED_IR = "ENHANCED_IR"


class SatelliteImageInput(BaseModel):
    """
    Satellite imagery input supporting dual-channel ingestion:
    1. Direct signed/secure storage URL (e.g. Supabase Storage / S3)
    2. Base64 encoded raw image bytes
    """
    image_id: Optional[str] = Field(None, description="Unique identifier for the satellite image frame")
    image_url: Optional[str] = Field(None, description="Secure, pre-signed URL to satellite imagery")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image string (fallback)")
    channel: SatelliteChannel = Field(default=SatelliteChannel.IR1, description="Satellite sensor channel")
    capture_time: Optional[datetime] = Field(None, description="UTC timestamp of satellite frame capture")
    resolution_km: Optional[float] = Field(default=4.0, ge=0.5, le=50.0, description="Spatial resolution in km per pixel")

    @model_validator(mode="after")
    def check_at_least_one_source(self) -> "SatelliteImageInput":
        if not self.image_url and not self.image_base64:
            raise ValueError("At least one of 'image_url' or 'image_base64' must be provided in SatelliteImageInput.")
        return self


class VisionAnalysisResult(BaseModel):
    """
    Structured deep vision output produced by satellite feature extraction backbone
    """
    model_config = ConfigDict(protected_namespaces=())

    model_name: str = Field(default="ResNet34-GradCAM-v1", description="Identifier of vision backbone")
    cyclone_detected: bool = Field(..., description="Whether cyclone vortex pattern is positively identified")
    eye_detected: bool = Field(..., description="Whether a closed central eye feature is present")
    eye_radius_km: Optional[float] = Field(None, ge=0.0, description="Estimated eye radius in kilometers")
    cloud_top_temp_min_c: Optional[float] = Field(None, le=50.0, ge=-100.0, description="Minimum cloud top temperature in Celsius")
    convective_organization_score: float = Field(..., ge=0.0, le=1.0, description="Organization index (0.0=diffuse, 1.0=highly symmetric)")
    estimated_wind_kts: Optional[float] = Field(None, ge=0.0, description="Visual Dvorak/CNN wind estimation in knots")
    classification: Optional[str] = Field(None, description="IMD/WMO visual category classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Inference confidence score")
    gradcam_heatmap_url: Optional[str] = Field(None, description="URL to rendered Grad-CAM attention heatmap overlay")
    gradcam_base64: Optional[str] = Field(None, description="Base64 encoded Grad-CAM PNG overlay")
    features: Dict[str, Any] = Field(default_factory=dict, description="Additional structural and physical metrics")
