"""Analogue ensemble contract types.

The analogue ensemble is an independent second forecast, not a "similar storms" card.
That is why :class:`AnalogueOutcome` — what happened *next* to the retrieved storms —
is a required part of the block rather than an optional extra, and why the exclusions
are reported alongside the matches.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import Source


class AnalogueOutcome(BaseModel):
    """What happened to the retrieved analogues over the following 24 hours.

    ``riBaseRate`` sits next to ``riFraction`` so the comparison a viewer needs to make
    is on screen: 5 of 20 analogues rapidly intensifying only means something against
    the roughly 5% climatological rate.
    """

    model_config = ConfigDict(populate_by_name=True)

    intensifiedCount: int = 0
    weakenedCount: int = 0
    meanDeltaVmax24hKt: float | None = None
    riCount: int = 0
    riFraction: float | None = None
    riBaseRate: float | None = None


class AnalogueMatch(BaseModel):
    """One retrieved historical analogue and its subsequent outcome."""

    model_config = ConfigDict(populate_by_name=True)

    rank: int
    sid: str
    name: str
    time: datetime
    similarity: float
    outcomeDeltaVmax24hKt: float | None = None
    wasRi: bool | None = None
    onwardTrack: list[list[float]] = []


class AnalogueBlock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    k: int = 0
    outcome: AnalogueOutcome = AnalogueOutcome()
    matches: list[AnalogueMatch] = []
    exclusions: list[str] = []
    source: Source
