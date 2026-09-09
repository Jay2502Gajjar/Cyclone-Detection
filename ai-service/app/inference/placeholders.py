"""Phase 0 placeholders.

These exist so the architecture is runnable end to end before any model is trained. They
are registered with ``available=False``, so every value they produce is stamped
``DEMO_DATA`` and the frontend shows a banner saying so. They cannot be mistaken for
trained output, by construction.

One deliberate design choice: where a placeholder must return a number, it returns a
**transparent extrapolation of the observed input** — persistence — rather than a random
or hardcoded value. Two reasons. Random numbers make a demo look alive when it is not,
which is the specific dishonesty the provenance system exists to prevent. And
persistence is the baseline the real models will have to beat in Phase 2, so wiring it
in now means the comparison is already plumbed when there is something to compare.

Nothing here is presented as a prediction. It is scaffolding with an honest label.
"""

from __future__ import annotations

import math

import numpy as np

from app.inference.base import IntensityChangeEstimate, VisionEstimate
from app.schemas.analogue import AnalogueBlock, AnalogueOutcome
from app.schemas.common import ShapFactor, Source
from app.schemas.common import Provenance
from app.schemas.forecast import HistoryPoint, TrackPoint

EARTH_RADIUS_KM = 6371.0088


class PlaceholderIntensityEstimator:
    """Stands in for the EfficientNet-B0 intensity model until Phase 2.

    It reports no estimate at all rather than a fabricated one. A CNN that has not been
    trained has genuinely nothing to say about an image, and saying nothing is the
    accurate representation of that.
    """

    key = "ir_intensity"
    version = "phase0"
    is_trained = False

    def estimate(self, bt: np.ndarray, km_per_pixel: float) -> VisionEstimate:
        return VisionEstimate(vmax_kt=None, category=None, confidence=None, embedding=None)


class PlaceholderIntensityChangeModel:
    """Stands in for the XGBoost intensity-change and RI model until Phase 2."""

    key = "dvmax_ri"
    version = "phase0"
    is_trained = False

    def predict(self, features: np.ndarray) -> IntensityChangeEstimate:
        return IntensityChangeEstimate(
            delta_vmax_24h_kt=None, ri_probability=None, confidence=None
        )

    def explain(self, features: np.ndarray) -> list[ShapFactor]:
        return []


class PersistenceTrackModel:
    """Pure persistence: extrapolate the storm's current motion in a straight line.

    This is not the track model. It is the *baseline the track model must beat*, wired
    in early so Phase 2 has something to measure against from day one. It is registered
    as unavailable, so its output is stamped ``DEMO_DATA``.

    It returns no cone radii. The cone is meant to be percentiles of a model's measured
    held-out error, and persistence has no such measurement yet — an invented radius
    would be the single most misleading number the product could display.
    """

    key = "track_cliper"
    version = "phase0-persistence"
    is_trained = False

    LEAD_HOURS = (12, 24, 48)

    def forecast(self, history: list[HistoryPoint]) -> list[TrackPoint]:
        if len(history) < 2:
            return []

        ordered = sorted(history, key=lambda p: p.t)
        last, previous = ordered[-1], ordered[-2]

        hours = (last.t - previous.t).total_seconds() / 3600.0
        if hours <= 0:
            return []

        dlat_per_hour = (last.lat - previous.lat) / hours
        dlon_per_hour = (last.lon - previous.lon) / hours

        points: list[TrackPoint] = []
        for lead in self.LEAD_HOURS:
            lat = last.lat + dlat_per_hour * lead
            lon = last.lon + dlon_per_hour * lead
            points.append(
                TrackPoint(
                    leadHours=lead,
                    lat=round(max(-90.0, min(90.0, lat)), 4),
                    lon=round(((lon + 180.0) % 360.0) - 180.0, 4),
                    coneRadiusP67Km=None,
                    coneRadiusP90Km=None,
                    predictedVmaxKt=None,
                )
            )
        return points

    def cone_radii(self, lead_hours: int) -> tuple[float | None, float | None]:
        return None, None


class PlaceholderAnalogueIndex:
    """Stands in for the KNN analogue ensemble until the historical index is built.

    Returns an empty result set. There is no historical feature matrix yet, so there are
    genuinely no analogues to retrieve; inventing plausible-looking storm names would be
    the worst kind of demo fakery.
    """

    key = "analogue"
    version = "phase0"
    is_trained = False

    def query(
        self,
        window: np.ndarray,
        *,
        k: int,
        exclude_sid: str,
        exclude_season: int | None,
    ) -> AnalogueBlock:
        return AnalogueBlock(
            k=0,
            outcome=AnalogueOutcome(),
            matches=[],
            exclusions=["same-storm", "same-season"],
            source=Source(
                provenance=Provenance.DEMO_DATA,
                model=self.key,
                version=self.version,
                isTrained=False,
            ),
        )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres. Shared with the track baseline's evaluation."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))
