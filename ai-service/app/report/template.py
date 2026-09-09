"""Deterministic situation report.

Plain string interpolation over values the pipeline has already computed. It is instant,
works offline, and cannot invent a number — it can only restate ones that exist.

An LLM pass over this text is a Phase 4 option (``app/report/llm.py``), tagged
``LLM_NARRATION``, and it will be allowed to rephrase but never to originate a figure.
The template output is kept either way so the two can be compared.
"""

from __future__ import annotations

from app.schemas.analogue import AnalogueBlock
from app.schemas.forecast import IntensityForecast, RiskBlock
from app.schemas.frame import StructureBlock


def build_report(
    *,
    name: str,
    vmax_kt: float | None,
    category: str | None,
    structure: StructureBlock,
    intensity: IntensityForecast,
    analogues: AnalogueBlock,
    risk: RiskBlock,
) -> str:
    """Compose a short intelligence summary from whatever is actually known.

    Sentences are emitted only when their inputs exist. In Phase 0 that means a short
    paragraph describing the observed state and stating plainly that no trained model
    has contributed to it — which is the honest report for this build.
    """
    parts: list[str] = []

    if vmax_kt is not None and category is not None:
        parts.append(
            f"{name} is at {vmax_kt:.0f} kt ({_humanise(category)}) at the selected time."
        )
    elif vmax_kt is not None:
        parts.append(f"{name} is at {vmax_kt:.0f} kt at the selected time.")
    else:
        parts.append(f"{name} — no observed intensity is recorded at the selected time.")

    if structure.regime and structure.axisymmetry is not None:
        parts.append(
            f"Satellite structure reads as {structure.regimeLabel or structure.regime} "
            f"with a symmetry of {structure.axisymmetry:.2f}."
        )

    if intensity.deltaVmax24hKt is not None:
        direction = "strengthening" if intensity.deltaVmax24hKt > 0 else "weakening"
        parts.append(
            f"Models indicate {direction} of {intensity.deltaVmax24hKt:+.0f} kt over 24 hours."
        )
        if intensity.riProbability is not None and intensity.riBaseRate:
            multiple = intensity.riProbability / intensity.riBaseRate
            parts.append(
                f"Probability of rapid intensification is "
                f"{intensity.riProbability:.0%}, about {multiple:.0f} times the "
                f"climatological base rate of {intensity.riBaseRate:.0%}."
            )

    if analogues.matches:
        outcome = analogues.outcome
        parts.append(
            f"Of {analogues.k} closest historical analogues, "
            f"{outcome.intensifiedCount} intensified and {outcome.riCount} underwent "
            f"rapid intensification."
        )

    if risk.score is not None and risk.level:
        parts.append(f"Overall risk is assessed {risk.level.lower()} ({risk.score:.2f}).")

    if intensity.deltaVmax24hKt is None and not analogues.matches:
        parts.append(
            "No trained model has contributed to this summary: the model bundle is not "
            "yet trained, so forecast fields are unavailable rather than estimated."
        )

    return " ".join(parts)


def _humanise(category: str) -> str:
    return category.replace("_", " ").lower()
