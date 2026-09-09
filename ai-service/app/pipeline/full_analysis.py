"""The full inference pipeline: compose every component, stamp every result.

This is the only place the individual models are wired together, and it is the last step
before a response leaves the service. The ordering mirrors the documented pipeline in
the specification: structure, vision, fusion, intensity change, track, analogues, risk,
report, stamp.

Two things it will not do. It never sees data later than ``asOf`` — the request schema
rejects that before this code runs. And it never produces a verification block; ground
truth belongs to Spring Boot, which reads it from the database after this returns.
"""

from __future__ import annotations

import numpy as np
from loguru import logger

from app.io.bt_loader import FrameNotAvailable, load_bt
from app.registry import ModelRegistry
from app.report.template import build_report
from app.risk.rules import score_risk
from app.schemas.common import ObservedBlock
from app.schemas.forecast import (
    InferFullRequest,
    InferFullResponse,
    IntensityForecast,
    ReportBlock,
    RiskBlock,
    TrackForecast,
)
from app.schemas.frame import StructureBlock, VisionBlock
from app.structure.metrics import compute_metrics
from app.structure.regime_rules import classify

# HURSAT-B1 IRWIN is roughly 8 km per pixel. INSAT-3D differs, which is why this travels
# with the frame rather than being a constant.
DEFAULT_KM_PER_PIXEL = 8.0

CONE_BASIS_UNCALIBRATED = (
    "Not yet calibrated. From Phase 2 the radii are the 67th and 90th percentiles of "
    "this model's own held-out track error at each lead time."
)


def run_full_analysis(
    request: InferFullRequest, registry: ModelRegistry, frames_dir, bundle_version: str
) -> InferFullResponse:
    """Run every step and return the composite analysis."""
    latest = request.latest()

    # --- 1. Structure: deterministic measurement over the raw BT field ---------------
    bt = _load_frame(request, frames_dir)
    structure = _analyse_structure(bt, registry)

    # --- 2. Vision: the trained CNN's read of the same frame -------------------------
    vision = _estimate_intensity(bt, registry)

    # --- 3-4. Fusion and intensity change -------------------------------------------
    intensity = _forecast_intensity(registry)

    # --- 5. Track ---------------------------------------------------------------------
    track = _forecast_track(request, registry)

    # --- 6. Analogue ensemble: an independent second opinion -------------------------
    analogues = _query_analogues(request, registry)

    # --- 7. Risk ----------------------------------------------------------------------
    risk = _score_risk(latest, intensity, registry)

    # --- 8. Report --------------------------------------------------------------------
    report = ReportBlock(
        text=build_report(
            name=request.sid,
            vmax_kt=latest.vmaxKt,
            category=None,
            structure=structure,
            intensity=intensity,
            analogues=analogues,
            risk=risk,
        ),
        source=registry.stamp("report_template"),
    )

    current = ObservedBlock(
        lat=latest.lat,
        lon=latest.lon,
        vmaxKt=latest.vmaxKt,
        pressureHpa=latest.pressureHpa,
        category=None,
        distToCoastKm=latest.distToCoastKm,
        # OBSERVED is the one provenance the AI service may assert without the registry:
        # it is simply echoing back the input it was handed, not producing anything.
        source=_observed_source(),
    )

    return InferFullResponse(
        sid=request.sid,
        issuedFor=request.asOf,
        modelBundleVersion=bundle_version,
        current=current,
        structure=structure,
        vision=vision,
        intensityForecast=intensity,
        trackForecast=track,
        analogues=analogues,
        risk=risk,
        report=report,
    )


def _observed_source():
    from app.schemas.common import Provenance, Source

    return Source(provenance=Provenance.OBSERVED)


def _load_frame(request: InferFullRequest, frames_dir) -> np.ndarray | None:
    if request.frameRef is None:
        return None
    try:
        return load_bt(frames_dir, request.frameRef.btPath)
    except FrameNotAvailable as exc:
        logger.warning("frame unavailable for {}: {}", request.sid, exc)
        return None


def _analyse_structure(bt: np.ndarray | None, registry: ModelRegistry) -> StructureBlock:
    """Measure the frame, then label the regime. Absent data yields absent metrics."""
    if bt is None:
        # No imagery for this instant. That is normal — not every best-track point has a
        # matched satellite observation — so we report nothing rather than nothing-shaped
        # zeros.
        return StructureBlock(
            rulesApplied=[],
            metricsSource=registry.stamp("structure", available=False),
            regimeSource=registry.stamp("regime_rules", available=False),
        )

    try:
        metrics = compute_metrics(bt, DEFAULT_KM_PER_PIXEL)
    except ValueError as exc:
        logger.warning("structural metrics failed: {}", exc)
        return StructureBlock(
            rulesApplied=[],
            metricsSource=registry.stamp("structure", available=False),
            regimeSource=registry.stamp("regime_rules", available=False),
        )

    regime = classify(metrics)

    return StructureBlock(
        regime=regime.regime,
        regimeLabel=regime.label,
        eyePresent=metrics.eye_present,
        eyeRadiusKm=metrics.eye_radius_km,
        eyeRingBtContrastK=metrics.eye_ring_bt_contrast_k,
        minBtK=metrics.min_bt_k,
        cdoFraction100km=metrics.cdo_fraction_100km,
        axisymmetry=metrics.axisymmetry,
        convectiveRingRadiusKm=metrics.convective_ring_radius_km,
        coldCloudOffsetKm=metrics.cold_cloud_offset_km,
        rulesApplied=regime.rules_applied,
        metricsSource=registry.stamp("structure"),
        regimeSource=registry.stamp("regime_rules"),
    )


def _estimate_intensity(bt: np.ndarray | None, registry: ModelRegistry) -> VisionBlock:
    stamp = registry.stamp("ir_intensity", available=bt is not None)
    if bt is None or not registry.is_usable("ir_intensity"):
        return VisionBlock(source=stamp)

    estimate = registry.impl("ir_intensity").estimate(bt, DEFAULT_KM_PER_PIXEL)
    return VisionBlock(
        vmaxKt=estimate.vmax_kt,
        category=estimate.category,
        confidence=estimate.confidence,
        source=stamp,
    )


def _forecast_intensity(registry: ModelRegistry) -> IntensityForecast:
    stamp = registry.stamp("dvmax_ri")
    if not registry.is_usable("dvmax_ri"):
        return IntensityForecast(source=stamp)

    features = np.zeros(1)  # Phase 2 supplies the fused 33-d vector here.
    estimate = registry.impl("dvmax_ri").predict(features)
    factors = registry.impl("dvmax_ri").explain(features)

    trend = None
    if estimate.delta_vmax_24h_kt is not None:
        if estimate.delta_vmax_24h_kt > 5:
            trend = "INTENSIFYING"
        elif estimate.delta_vmax_24h_kt < -5:
            trend = "WEAKENING"
        else:
            trend = "STEADY"

    return IntensityForecast(
        deltaVmax24hKt=estimate.delta_vmax_24h_kt,
        trend=trend,
        confidence=estimate.confidence,
        riProbability=estimate.ri_probability,
        topFactors=factors,
        source=stamp,
    )


def _forecast_track(request: InferFullRequest, registry: ModelRegistry) -> TrackForecast:
    model = registry.impl("track_cliper")
    points = model.forecast(request.history) if model is not None else []

    return TrackForecast(
        points=points,
        source=registry.stamp("track_cliper"),
        coneSource=registry.stamp("track_cone"),
        coneBasis=CONE_BASIS_UNCALIBRATED,
    )


def _query_analogues(request: InferFullRequest, registry: ModelRegistry):
    from app.schemas.analogue import AnalogueBlock, AnalogueOutcome

    stamp = registry.stamp("analogue")
    if not registry.is_usable("analogue"):
        return AnalogueBlock(
            k=0,
            outcome=AnalogueOutcome(),
            matches=[],
            exclusions=["same-storm", "same-season"],
            source=stamp,
        )

    window = np.zeros(1)  # Phase 2 supplies the 24h evolution feature window.
    block = registry.impl("analogue").query(
        window, k=request.options.analogueK, exclude_sid=request.sid, exclude_season=None
    )
    return block.model_copy(update={"source": stamp})


def _score_risk(latest, intensity: IntensityForecast, registry: ModelRegistry) -> RiskBlock:
    result = score_risk(
        vmax_kt=latest.vmaxKt,
        ri_probability=intensity.riProbability,
        dist_to_coast_km=latest.distToCoastKm,
        category=None,
    )
    return RiskBlock(
        score=result.score,
        level=result.level,
        formula=result.formula,
        terms=result.terms,
        source=registry.stamp("risk_rules", available=result.score is not None),
    )
