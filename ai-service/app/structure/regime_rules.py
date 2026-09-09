"""Morphological regime classification from structural metrics.

This is a transparent rule engine, and it is labelled as one everywhere it appears. It
takes the measurements produced by :mod:`app.structure.metrics` and assigns a
descriptive regime, returning the exact thresholds that fired so the user can see the
reasoning rather than take the label on trust.

Two things this is deliberately *not*:

* It is not a trained classifier. Nothing here was fitted to data.
* It is not a Dvorak pattern classifier. The regimes are Dvorak-*inspired* names for
  morphologies we can measure, but we have no labelled Dvorak dataset to validate
  against, so we do not claim agreement with the Dvorak technique.

The thresholds below are documented starting points. Phase 2 tunes them against
held-out storms; until then the registry reports this component as uncalibrated and the
API stamps its output ``DEMO_DATA`` rather than ``RULE_ENGINE``.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.structure.metrics import StructuralMetrics

# --- thresholds (uncalibrated in Phase 0) -----------------------------------------

EYE_SYMMETRY_MIN = 0.70
EYE_SHEAR_OFFSET_MAX_KM = 40.0

CDO_FRACTION_MIN = 0.60
CDO_SYMMETRY_MIN = 0.55

SHEAR_OFFSET_MIN_KM = 60.0

BANDING_CDO_MIN = 0.25

REGIME_LABELS = {
    "EYE": "Eye pattern — well organised",
    "CENTRAL_DENSE_OVERCAST": "Central dense overcast — consolidated core",
    "BANDING": "Banding pattern — organising",
    "SHEARED": "Sheared — convection displaced from centre",
    "DISORGANISED": "Disorganised — no coherent core",
}


@dataclass(frozen=True)
class RegimeResult:
    """A regime label together with the rules that produced it."""

    regime: str | None
    label: str | None
    rules_applied: list[str]


def classify(metrics: StructuralMetrics | None) -> RegimeResult:
    """Assign a morphological regime.

    Returns a result with ``regime=None`` when there is nothing to classify. An absent
    label is the correct answer for a frame with no imagery; guessing one would be worse
    than saying nothing.
    """
    if metrics is None:
        return RegimeResult(None, None, [])

    rules: list[str] = []

    # Sheared is checked first: displaced convection overrides an apparently cold core,
    # because the cold shield is real but is no longer over the circulation centre.
    if metrics.cold_cloud_offset_km >= SHEAR_OFFSET_MIN_KM:
        rules.append(
            f"coldCloudOffsetKm ({metrics.cold_cloud_offset_km:.0f}) "
            f">= {SHEAR_OFFSET_MIN_KM:.0f}"
        )
        return _result("SHEARED", rules)

    if (
        metrics.eye_present
        and metrics.axisymmetry >= EYE_SYMMETRY_MIN
        and metrics.cold_cloud_offset_km < EYE_SHEAR_OFFSET_MAX_KM
    ):
        rules.append("eyePresent == true")
        rules.append(f"axisymmetry ({metrics.axisymmetry:.2f}) >= {EYE_SYMMETRY_MIN:.2f}")
        rules.append(
            f"coldCloudOffsetKm ({metrics.cold_cloud_offset_km:.0f}) "
            f"< {EYE_SHEAR_OFFSET_MAX_KM:.0f}"
        )
        return _result("EYE", rules)

    if (
        metrics.cdo_fraction_100km >= CDO_FRACTION_MIN
        and metrics.axisymmetry >= CDO_SYMMETRY_MIN
    ):
        rules.append(
            f"cdoFraction100km ({metrics.cdo_fraction_100km:.2f}) >= {CDO_FRACTION_MIN:.2f}"
        )
        rules.append(f"axisymmetry ({metrics.axisymmetry:.2f}) >= {CDO_SYMMETRY_MIN:.2f}")
        return _result("CENTRAL_DENSE_OVERCAST", rules)

    if metrics.cdo_fraction_100km >= BANDING_CDO_MIN:
        rules.append(
            f"cdoFraction100km ({metrics.cdo_fraction_100km:.2f}) >= {BANDING_CDO_MIN:.2f}"
        )
        rules.append("no eye, insufficient symmetry for CDO")
        return _result("BANDING", rules)

    rules.append(
        f"cdoFraction100km ({metrics.cdo_fraction_100km:.2f}) < {BANDING_CDO_MIN:.2f}"
    )
    return _result("DISORGANISED", rules)


def _result(regime: str, rules: list[str]) -> RegimeResult:
    return RegimeResult(regime=regime, label=REGIME_LABELS[regime], rules_applied=rules)
