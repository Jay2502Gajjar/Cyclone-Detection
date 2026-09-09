"""Forecast contract types, including the temporal-mask validator.

This module carries invariant I1 on the Python side. Spring Boot filters history before
sending it; :class:`InferFullRequest` refuses it again on arrival. Two independent
filters mean two independent mistakes would be required to leak the future into a
hindcast — and a leak here would not look like a bug, it would look like an unusually
accurate model, which is precisely why it needs a hard guard rather than a convention.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.analogue import AnalogueBlock
from app.schemas.common import ObservedBlock, ShapFactor, Source
from app.schemas.frame import FrameRef, StructureBlock, VisionBlock


class HistoryPoint(BaseModel):
    """One observed track point. Only points at or before ``asOf`` may appear."""

    model_config = ConfigDict(populate_by_name=True)

    t: datetime
    lat: float
    lon: float
    vmaxKt: float | None = None
    pressureHpa: float | None = None
    translationSpeedKt: float | None = None
    headingDeg: float | None = None
    distToCoastKm: float | None = None


class InferOptions(BaseModel):
    analogueK: int = 20
    wantGradcam: bool = True
    wantShap: bool = True


class InferFullRequest(BaseModel):
    """The one request Spring Boot makes in normal operation.

    There is no field here capable of carrying a future observation or a ground-truth
    outcome. That is a design constraint, not an oversight: verification is assembled by
    Spring Boot from the database after inference has already returned.
    """

    model_config = ConfigDict(populate_by_name=True)

    sid: str
    asOf: datetime
    history: list[HistoryPoint] = Field(min_length=1)
    frameRef: FrameRef | None = None
    options: InferOptions = InferOptions()

    @model_validator(mode="after")
    def enforce_temporal_mask(self) -> "InferFullRequest":
        """Reject any history point later than ``asOf`` (invariant I1).

        Returning 422 rather than silently dropping the offending points is intentional:
        a caller that sends the future has a bug worth surfacing, and quietly repairing
        it would hide the very failure this guard exists to catch.
        """
        offenders = [p.t for p in self.history if p.t > self.asOf]
        if offenders:
            raise ValueError(
                f"temporal mask violation: {len(offenders)} observation(s) after asOf="
                f"{self.asOf.isoformat()} (earliest offender {min(offenders).isoformat()}). "
                f"A forecast issued for a past time may only see data from at or before "
                f"that time."
            )
        return self

    def latest(self) -> HistoryPoint:
        """The most recent observable point — the storm's state at ``asOf``."""
        return max(self.history, key=lambda p: p.t)


class TrackPoint(BaseModel):
    """A predicted position with its empirical uncertainty radii."""

    model_config = ConfigDict(populate_by_name=True)

    leadHours: Literal[12, 24, 48]
    lat: float
    lon: float
    coneRadiusP67Km: float | None = None
    coneRadiusP90Km: float | None = None
    predictedVmaxKt: float | None = None


class TrackForecast(BaseModel):
    """Predicted track, with the cone stamped separately from the prediction.

    The cone is not a model output — it is a percentile of the model's own held-out
    error — so it carries ``STATISTICAL_BASELINE`` rather than ``TRAINED_MODEL``.
    """

    model_config = ConfigDict(populate_by_name=True)

    points: list[TrackPoint]
    source: Source
    coneSource: Source
    coneBasis: str


class IntensityForecast(BaseModel):
    """24-hour intensity change and rapid-intensification probability.

    ``riBaseRate`` travels with ``riProbability`` on purpose: a 34% RI probability is
    meaningless until you know the climatological base rate it should be read against.
    """

    model_config = ConfigDict(populate_by_name=True)

    deltaVmax24hKt: float | None = None
    predictedVmax24hKt: float | None = None
    trend: Literal["INTENSIFYING", "WEAKENING", "STEADY"] | None = None
    confidence: float | None = None
    riProbability: float | None = None
    riBaseRate: float | None = None
    topFactors: list[ShapFactor] = []
    source: Source


class RiskBlock(BaseModel):
    """Risk score with the formula and every term that produced it, always shown."""

    model_config = ConfigDict(populate_by_name=True)

    score: float | None = None
    level: Literal["LOW", "MODERATE", "HIGH", "CRITICAL"] | None = None
    formula: str | None = None
    terms: dict[str, float] = {}
    nearestCoast: str | None = None
    landfallWindowHours: float | None = None
    source: Source


class ReportBlock(BaseModel):
    """Narrative summary. Interpolates computed values; never originates a number."""

    text: str
    source: Source


class InferFullResponse(BaseModel):
    """The AI service's answer.

    Invariant I2: there is no ``verification``, ``degraded`` or ``servedFrom`` field
    here. Ground truth is Spring Boot's to attach, from the database, after this
    response has already been produced.
    """

    model_config = ConfigDict(populate_by_name=True)

    sid: str
    issuedFor: datetime
    modelBundleVersion: str
    current: ObservedBlock
    structure: StructureBlock
    vision: VisionBlock
    intensityForecast: IntensityForecast
    trackForecast: TrackForecast
    analogues: AnalogueBlock
    risk: RiskBlock
    report: ReportBlock
