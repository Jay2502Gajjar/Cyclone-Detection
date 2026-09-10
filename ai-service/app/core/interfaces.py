from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.schemas.common import Basin
from app.schemas.vision import SatelliteImageInput, SatelliteChannel, VisionAnalysisResult
from app.schemas.trajectory import (
    ObservationInput,
    EnvironmentalContext,
    TrajectoryForecastPoint,
    IntensityForecastResult,
    LandfallEstimate,
)
from app.schemas.similarity import HistoricalAnalogueResult
from app.schemas.report import SituationReportResult
from app.schemas.full_pipeline import RiskFeatureExtractionResult, ExplainabilityResult


class IVisionAnalyzer(ABC):
    """
    Abstract contract for Satellite Vision feature extraction (e.g. ResNet34 / ConvNeXt / Grad-CAM)
    """
    @property
    @abstractmethod
    def version(self) -> str:
        """Return model/provider version identifier"""
        pass

    @abstractmethod
    def analyze(self, image_input: SatelliteImageInput) -> VisionAnalysisResult:
        """Extract visual features from satellite image URL or base64"""
        pass

    @abstractmethod
    def analyze_bytes(self, image_bytes: bytes, channel: SatelliteChannel = SatelliteChannel.IR1) -> VisionAnalysisResult:
        """Extract visual features directly from raw image bytes (multipart upload)"""
        pass


class ITrajectoryForecaster(ABC):
    """
    Abstract contract for Track & Spatiotemporal Trajectory Forecasting (e.g. Kalman Filter + Physics / LSTM)
    """
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def forecast_trajectory(
        self,
        observations: List[ObservationInput],
        horizons: List[int],
        env: Optional[EnvironmentalContext] = None
    ) -> List[TrajectoryForecastPoint]:
        """Project coordinates and uncertainty cones across horizons"""
        pass

    @abstractmethod
    def estimate_landfall(
        self,
        observations: List[ObservationInput],
        forecast_points: List[TrajectoryForecastPoint]
    ) -> Optional[LandfallEstimate]:
        """Estimate landfall timing and coordinates if track intersects land"""
        pass


class IIntensityPredictor(ABC):
    """
    Abstract contract for Cyclone Intensity & Rapid Intensification prediction (e.g. XGBoost Regressor)
    """
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def predict_intensity(
        self,
        observations: List[ObservationInput],
        horizons: List[int],
        env: Optional[EnvironmentalContext] = None,
        vision_result: Optional[VisionAnalysisResult] = None
    ) -> IntensityForecastResult:
        """Predict wind intensity curve, trend, and rapid intensification probability"""
        pass


class ISimilarityMatcher(ABC):
    """
    Abstract contract for Historical Storm Track & Pattern Matching (e.g. KNN / DTW on IBTrACS)
    """
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def match_analogues(
        self,
        observations: List[ObservationInput],
        basin: Basin = Basin.NI,
        limit: int = 3
    ) -> List[HistoricalAnalogueResult]:
        """Find closest meteorological analogues from historical dataset"""
        pass


class IFusionEngine(ABC):
    """
    Abstract contract for Multi-Modal Feature Fusion
    Combines satellite vision features + numerical trajectory + ambient ocean/weather telemetry
    """
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def fuse(
        self,
        observations: List[ObservationInput],
        env: Optional[EnvironmentalContext],
        vision_result: Optional[VisionAnalysisResult],
        intensity_result: IntensityForecastResult
    ) -> Dict[str, Any]:
        """Produce fused representation vector and diagnostic indicators"""
        pass


class IRiskAssessor(ABC):
    """
    Abstract contract for Natural Disaster Risk Assessment & Hazard Indexing
    """
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def assess_risk(
        self,
        observations: List[ObservationInput],
        trajectory: List[TrajectoryForecastPoint],
        intensity: IntensityForecastResult,
        env: Optional[EnvironmentalContext],
        fused_features: Dict[str, Any]
    ) -> RiskFeatureExtractionResult:
        """Calculate storm surge, wind damage, and flooding risk scores"""
        pass


class IExplainabilityEngine(ABC):
    """
    Abstract contract for Model Interpretability & Explainable AI (XAI)
    """
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def explain(
        self,
        observations: List[ObservationInput],
        env: Optional[EnvironmentalContext],
        trajectory: List[TrajectoryForecastPoint],
        intensity: IntensityForecastResult,
        vision_result: Optional[VisionAnalysisResult]
    ) -> ExplainabilityResult:
        """Generate feature importance attribution and physics-consistency checks"""
        pass


class ISituationReportGenerator(ABC):
    """
    Abstract contract for Operational Meteorological Situation Report Synthesis
    """
    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def generate_report(
        self,
        cyclone_id: str,
        cyclone_name: str,
        observations: List[ObservationInput],
        trajectory: List[TrajectoryForecastPoint],
        intensity: IntensityForecastResult,
        risk: RiskFeatureExtractionResult,
        explainability: ExplainabilityResult
    ) -> SituationReportResult:
        """Synthesize operational situation report for emergency managers"""
        pass
