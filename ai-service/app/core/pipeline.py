from datetime import datetime
import uuid
from typing import Optional

from app.schemas.full_pipeline import (
    FullPredictionRequest,
    FullPredictionResponse,
)
from app.schemas.vision import VisionAnalysisResult, SatelliteChannel
from app.core.interfaces import (
    IVisionAnalyzer,
    ITrajectoryForecaster,
    IIntensityPredictor,
    ISimilarityMatcher,
    IFusionEngine,
    IRiskAssessor,
    IExplainabilityEngine,
    ISituationReportGenerator,
)
from app.core.providers import (
    BaselineVisionAnalyzer,
    BaselineTrajectoryForecaster,
    BaselineIntensityPredictor,
    BaselineSimilarityMatcher,
    BaselineFusionEngine,
    BaselineRiskAssessor,
    BaselineExplainabilityEngine,
    BaselineSituationReportGenerator,
)


class FullPredictionPipelineOrchestrator:
    """
    Stateless End-to-End Prediction Pipeline Orchestrator.
    Executes the canonical inference workflow:
    Vision -> Trajectory -> Intensity -> Similarity -> Fusion -> Risk -> Explainability -> Report
    """
    def __init__(
        self,
        vision_analyzer: Optional[IVisionAnalyzer] = None,
        trajectory_forecaster: Optional[ITrajectoryForecaster] = None,
        intensity_predictor: Optional[IIntensityPredictor] = None,
        similarity_matcher: Optional[ISimilarityMatcher] = None,
        fusion_engine: Optional[IFusionEngine] = None,
        risk_assessor: Optional[IRiskAssessor] = None,
        explainability_engine: Optional[IExplainabilityEngine] = None,
        report_generator: Optional[ISituationReportGenerator] = None,
    ):
        self.vision_analyzer = vision_analyzer or BaselineVisionAnalyzer()
        self.trajectory_forecaster = trajectory_forecaster or BaselineTrajectoryForecaster()

        if intensity_predictor is not None:
            self.intensity_predictor = intensity_predictor
        else:
            try:
                from app.models.xgboost_intensity import XGBoostIntensityPredictor, DEFAULT_MODEL_PATH
                if DEFAULT_MODEL_PATH.exists():
                    self.intensity_predictor = XGBoostIntensityPredictor()
                else:
                    self.intensity_predictor = BaselineIntensityPredictor()
            except Exception:
                self.intensity_predictor = BaselineIntensityPredictor()

        self.similarity_matcher = similarity_matcher or BaselineSimilarityMatcher()
        self.fusion_engine = fusion_engine or BaselineFusionEngine()
        self.risk_assessor = risk_assessor or BaselineRiskAssessor()
        self.explainability_engine = explainability_engine or BaselineExplainabilityEngine()
        self.report_generator = report_generator or BaselineSituationReportGenerator()

    def run_pipeline(
        self,
        request: FullPredictionRequest,
        raw_image_bytes: Optional[bytes] = None,
        raw_image_channel: SatelliteChannel = SatelliteChannel.IR1
    ) -> FullPredictionResponse:
        prediction_id = f"pred-{request.cyclone_id}-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:6]}"
        now = datetime.utcnow()

        # Step 1: Vision analysis (if image bytes or image input supplied)
        vision_result: Optional[VisionAnalysisResult] = None
        if raw_image_bytes:
            vision_result = self.vision_analyzer.analyze_bytes(raw_image_bytes, raw_image_channel)
        elif request.satellite_image:
            vision_result = self.vision_analyzer.analyze(request.satellite_image)

        # Step 2: Trajectory forecasting
        trajectory_points = self.trajectory_forecaster.forecast_trajectory(
            observations=request.observations,
            horizons=request.forecast_horizons_hours,
            env=request.environmental_context
        )
        landfall_est = self.trajectory_forecaster.estimate_landfall(
            observations=request.observations,
            forecast_points=trajectory_points
        )

        # Step 3: Intensity forecasting
        intensity_result = self.intensity_predictor.predict_intensity(
            observations=request.observations,
            horizons=request.forecast_horizons_hours,
            env=request.environmental_context,
            vision_result=vision_result
        )

        # Step 4: Historical similarity matching
        analogues = self.similarity_matcher.match_analogues(
            observations=request.observations,
            basin=request.basin,
            limit=request.historical_reference_limit
        )

        # Step 5: Multi-modal fusion
        fused = self.fusion_engine.fuse(
            observations=request.observations,
            env=request.environmental_context,
            vision_result=vision_result,
            intensity_result=intensity_result
        )

        # Step 6: Multi-hazard risk assessment
        risk_result = self.risk_assessor.assess_risk(
            observations=request.observations,
            trajectory=trajectory_points,
            intensity=intensity_result,
            env=request.environmental_context,
            fused_features=fused
        )

        # Step 7: Explainability and physics attribution
        xai_result = self.explainability_engine.explain(
            observations=request.observations,
            env=request.environmental_context,
            trajectory=trajectory_points,
            intensity=intensity_result,
            vision_result=vision_result
        )

        # Step 8: Situation report synthesis
        report_result = self.report_generator.generate_report(
            cyclone_id=request.cyclone_id,
            cyclone_name=request.name or "Cyclone",
            observations=request.observations,
            trajectory=trajectory_points,
            intensity=intensity_result,
            risk=risk_result,
            explainability=xai_result
        )

        model_versions_dict = {
            "vision": self.vision_analyzer.version,
            "trajectory": self.trajectory_forecaster.version,
            "intensity": self.intensity_predictor.version,
            "similarity": self.similarity_matcher.version,
            "fusion": self.fusion_engine.version,
            "risk": self.risk_assessor.version,
            "explainability": self.explainability_engine.version,
            "report": self.report_generator.version,
        }

        return FullPredictionResponse(
            prediction_id=prediction_id,
            cyclone_id=request.cyclone_id,
            generated_at=now,
            pipeline_version="CycloVision-Full-Pipeline-v1.0",
            model_versions=model_versions_dict,
            vision_analysis=vision_result,
            trajectory_forecast=trajectory_points,
            landfall_estimate=landfall_est,
            intensity_forecast=intensity_result,
            historical_analogues=analogues,
            risk_features=risk_result,
            explainability=xai_result,
            situation_report=report_result
        )
