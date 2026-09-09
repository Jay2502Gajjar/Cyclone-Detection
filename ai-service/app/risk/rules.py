"""Rule-based risk scoring.

A transparent weighted formula, not a model. The formula string and every term that fed
it are returned alongside the score, so "why is this High?" is answerable on screen
rather than requiring trust.

We chose rules over a learned risk model deliberately. A supervised risk model needs
labelled outcome severity mapped onto a discrete scale, which does not cleanly exist in
IBTrACS; fitting one on proxies would produce a number that looks authoritative and
means very little. A weighted rule is honest about being a judgement call.
"""

from __future__ import annotations

from dataclasses import dataclass

FORMULA = (
    "0.35*vmaxNorm + 0.25*riProbability + 0.25*(1 - coastDistNorm) + 0.15*categoryNorm"
)

# Normalisation reference points.
VMAX_REFERENCE_KT = 160.0
COAST_REFERENCE_KM = 800.0

CATEGORY_SCALE = {
    "DEPRESSION": 0.1,
    "DEEP_DEPRESSION": 0.2,
    "CYCLONIC_STORM": 0.4,
    "SEVERE": 0.6,
    "VERY_SEVERE": 0.8,
    "EXTREMELY_SEVERE": 0.9,
    "SUPER_CYCLONIC_STORM": 1.0,
}


@dataclass(frozen=True)
class RiskResult:
    score: float | None
    level: str | None
    formula: str
    terms: dict[str, float]


def score_risk(
    *,
    vmax_kt: float | None,
    ri_probability: float | None,
    dist_to_coast_km: float | None,
    category: str | None,
) -> RiskResult:
    """Compute the risk score, or report that it cannot be computed.

    Every term the formula needs must be present. If any is missing — which is the Phase
    0 state, because rapid-intensification probability comes from a model that is not yet
    trained — the score is ``None`` and only the terms we actually have are returned.
    A partial score presented as a whole one would be exactly the kind of number this
    project has committed to not producing.
    """
    terms: dict[str, float] = {}

    if vmax_kt is not None:
        terms["vmaxNorm"] = _clamp(vmax_kt / VMAX_REFERENCE_KT)
    if ri_probability is not None:
        terms["riProbability"] = _clamp(ri_probability)
    if dist_to_coast_km is not None:
        terms["coastDistNorm"] = _clamp(dist_to_coast_km / COAST_REFERENCE_KM)
    if category is not None and category in CATEGORY_SCALE:
        terms["categoryNorm"] = CATEGORY_SCALE[category]

    required = {"vmaxNorm", "riProbability", "coastDistNorm", "categoryNorm"}
    if not required.issubset(terms):
        return RiskResult(score=None, level=None, formula=FORMULA, terms=terms)

    score = (
        0.35 * terms["vmaxNorm"]
        + 0.25 * terms["riProbability"]
        + 0.25 * (1.0 - terms["coastDistNorm"])
        + 0.15 * terms["categoryNorm"]
    )
    score = _clamp(score)
    return RiskResult(score=round(score, 3), level=_level(score), formula=FORMULA, terms=terms)


def _level(score: float) -> str:
    if score > 0.80:
        return "CRITICAL"
    if score > 0.60:
        return "HIGH"
    if score > 0.35:
        return "MODERATE"
    return "LOW"


def _clamp(value: float) -> float:
    return float(max(0.0, min(1.0, value)))
