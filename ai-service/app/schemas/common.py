"""Shared contract types. Mirrors the `Source` section of API_CONTRACT.md."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Provenance(str, Enum):
    """Where a value came from. See docs/provenance.md for the rules.

    The ordering here matches the contract and the database CHECK constraint; changing
    it means changing all three.
    """

    OBSERVED = "OBSERVED"
    TRAINED_MODEL = "TRAINED_MODEL"
    DERIVED_MEASUREMENT = "DERIVED_MEASUREMENT"
    STATISTICAL_BASELINE = "STATISTICAL_BASELINE"
    ANALOGUE_ENSEMBLE = "ANALOGUE_ENSEMBLE"
    RULE_ENGINE = "RULE_ENGINE"
    LLM_NARRATION = "LLM_NARRATION"
    DEMO_DATA = "DEMO_DATA"


class MetricInfo(BaseModel):
    """A held-out metric together with the baseline it is compared against.

    Both halves are required for a claim to mean anything: an MAE with no baseline says
    nothing about whether the model is better than guessing the mean.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str
    value: float
    baseline: str | None = None
    baselineValue: float | None = None
    n: int | None = None


class Source(BaseModel):
    """The provenance stamp attached to every analysis block.

    Never construct this directly — go through ``registry.stamp()``, which is what
    enforces invariant I3.
    """

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    provenance: Provenance
    model: str | None = None
    version: str | None = None
    isTrained: bool | None = None
    metric: MetricInfo | None = None


class ObservedBlock(BaseModel):
    """The storm's observed state. Always OBSERVED, always from the best track."""

    model_config = ConfigDict(populate_by_name=True)

    lat: float
    lon: float
    vmaxKt: float | None = None
    pressureHpa: float | None = None
    category: str | None = None
    distToCoastKm: float | None = None
    source: Source


class ShapFactor(BaseModel):
    """One feature's contribution to an intensity-change prediction."""

    feature: str
    shap: float
    direction: str = Field(description="'increases' or 'decreases'")
