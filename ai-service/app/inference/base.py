"""Model interfaces.

Every model in CycloVision sits behind one of these protocols. That is what lets Phase 0
ship a runnable system with placeholders, and Phase 2 swap in trained models without
touching the pipeline, the API contract, or the frontend.

The ``is_trained`` attribute is not decorative. The registry reads it to decide what a
component may claim, so a model that forgets to set it truthfully gets downgraded to
``DEMO_DATA`` rather than being taken at its word.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np

from app.schemas.analogue import AnalogueBlock
from app.schemas.common import ShapFactor
from app.schemas.forecast import HistoryPoint, TrackPoint


@runtime_checkable
class FrameModel(Protocol):
    """Estimates intensity from a storm-centred brightness-temperature field."""

    key: str
    version: str
    is_trained: bool

    def estimate(self, bt: np.ndarray, km_per_pixel: float) -> "VisionEstimate":
        """Return an intensity estimate for one frame."""
        ...


@runtime_checkable
class IntensityChangeModel(Protocol):
    """Predicts 24-hour intensity change and rapid-intensification probability."""

    key: str
    version: str
    is_trained: bool

    def predict(self, features: np.ndarray) -> "IntensityChangeEstimate":
        ...

    def explain(self, features: np.ndarray) -> list[ShapFactor]:
        """Per-feature attributions for the most recent prediction."""
        ...


@runtime_checkable
class TrackModel(Protocol):
    """Predicts future positions from recent track history."""

    key: str
    version: str
    is_trained: bool

    def forecast(self, history: list[HistoryPoint]) -> list[TrackPoint]:
        ...

    def cone_radii(self, lead_hours: int) -> tuple[float | None, float | None]:
        """Empirical (p67, p90) error radii in km for this lead time.

        Returns ``(None, None)`` until calibrated — an uncalibrated cone must be absent,
        not invented, because its width is the product's entire visual statement about
        uncertainty.
        """
        ...


@runtime_checkable
class AnalogueIndex(Protocol):
    """Retrieves historical storms whose recent evolution resembles the query."""

    key: str
    version: str
    is_trained: bool

    def query(
        self,
        window: np.ndarray,
        *,
        k: int,
        exclude_sid: str,
        exclude_season: int | None,
    ) -> AnalogueBlock:
        ...


class VisionEstimate:
    """Result of a frame-level intensity estimate."""

    def __init__(
        self,
        vmax_kt: float | None = None,
        category: str | None = None,
        confidence: float | None = None,
        embedding: np.ndarray | None = None,
    ) -> None:
        self.vmax_kt = vmax_kt
        self.category = category
        self.confidence = confidence
        self.embedding = embedding


class IntensityChangeEstimate:
    """Result of a 24-hour intensity-change prediction."""

    def __init__(
        self,
        delta_vmax_24h_kt: float | None = None,
        ri_probability: float | None = None,
        confidence: float | None = None,
    ) -> None:
        self.delta_vmax_24h_kt = delta_vmax_24h_kt
        self.ri_probability = ri_probability
        self.confidence = confidence
