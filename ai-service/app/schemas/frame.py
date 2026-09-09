"""Per-frame analysis contract types."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import ObservedBlock, Source


class StructureBlock(BaseModel):
    """The seven structural measurements plus the regime built on top of them.

    Two provenance stamps, deliberately. ``metricsSource`` covers the measurements,
    which are deterministic physics over the raw brightness-temperature field.
    ``regimeSource`` covers the label, which is a rule engine's interpretation of them.
    Collapsing the two would let a hand-written threshold borrow the credibility of a
    measurement.
    """

    model_config = ConfigDict(populate_by_name=True)

    regime: str | None = None
    regimeLabel: str | None = None
    eyePresent: bool | None = None
    eyeRadiusKm: float | None = None
    eyeRingBtContrastK: float | None = None
    minBtK: float | None = None
    cdoFraction100km: float | None = None
    axisymmetry: float | None = None
    convectiveRingRadiusKm: float | None = None
    coldCloudOffsetKm: float | None = None
    rulesApplied: list[str] = []
    metricsSource: Source
    regimeSource: Source


class VisionBlock(BaseModel):
    """The trained CNN's read of the satellite frame."""

    model_config = ConfigDict(populate_by_name=True)

    vmaxKt: float | None = None
    category: str | None = None
    confidence: float | None = None
    gradcamUrl: str | None = None
    source: Source


class FrameAnalysis(BaseModel):
    """Everything known about one instant of a storm."""

    model_config = ConfigDict(populate_by_name=True)

    sid: str
    t: datetime
    observed: ObservedBlock
    imageUrl: str | None = None
    imageTime: datetime | None = None
    imageSource: str | None = None
    structure: StructureBlock
    vision: VisionBlock
    analysisVersion: str | None = None


class FrameRef(BaseModel):
    """Reference to a satellite frame. Paths resolve under FRAMES_DIR only."""

    model_config = ConfigDict(populate_by_name=True)

    btPath: str | None = None
    imageUrl: str | None = None
    imageTime: datetime | None = None
    imageSource: str | None = None


class InferFrameRequest(BaseModel):
    """Analyse a single frame: structural metrics, regime, vision estimate, Grad-CAM."""

    model_config = ConfigDict(populate_by_name=True)

    sid: str
    t: datetime
    frameRef: FrameRef | None = None
    kmPerPixel: float = 8.0
    wantGradcam: bool = True
