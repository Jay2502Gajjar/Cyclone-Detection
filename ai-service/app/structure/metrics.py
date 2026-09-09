"""Deterministic structural measurements from a storm-centred infrared field.

These are the quantities a Dvorak analyst reads off an image by eye — is there an eye,
how symmetric is the cloud shield, how cold are the tops, is the convection displaced
from the centre — computed numerically from the raw brightness temperature instead of
estimated visually.

They are measurements, not predictions. Nothing here is trained, nothing is fitted, and
the same input always produces the same output. That is why they carry
``DERIVED_MEASUREMENT`` provenance and why the regime label built on top of them
(see :mod:`app.structure.regime_rules`) carries ``RULE_ENGINE`` separately: the numbers
and the interpretation of the numbers have different standing.

We deliberately do **not** claim these reproduce Dvorak T-numbers. No free labelled
Dvorak dataset exists at scale, so we report what we can actually measure and say so.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from app.structure.polar import (
    COLD_CLOUD_K,
    DEEP_CONVECTION_K,
    background_temperature,
    to_polar,
)

# Radial band used for the symmetry decomposition: outside the eye, inside the environment.
SYMMETRY_INNER_KM = 50.0
SYMMETRY_OUTER_KM = 200.0

# An eye is searched for within this radius of the centre.
EYE_SEARCH_KM = 50.0

# Minimum eye-to-eyewall contrast before we are willing to call it an eye.
# Tuned in Phase 2; until then this is a documented starting point, not a result.
EYE_CONTRAST_MIN_K = 8.0

# Fraction of the eyewall ring that must actually be cold for the centre to count as an
# eye. Without this, a single cold cloud mass sitting off to one side produces a warm
# "centre" and a cold ring *on average*, and a mean-only test calls it an eye. An eye is
# defined by the convection encircling the centre, so we require it explicitly.
EYE_ENCLOSURE_MIN = 0.70


@dataclass(frozen=True)
class StructuralMetrics:
    """The seven metrics, plus the eye geometry used to draw on the image."""

    eye_present: bool
    eye_radius_km: float | None
    eye_ring_bt_contrast_k: float | None
    min_bt_k: float
    cdo_fraction_100km: float
    axisymmetry: float
    convective_ring_radius_km: float | None
    cold_cloud_offset_km: float

    def to_dict(self) -> dict:
        return asdict(self)


def compute_metrics(
    bt: np.ndarray,
    km_per_pixel: float,
    *,
    deep_convection_k: float = DEEP_CONVECTION_K,
    cold_cloud_k: float = COLD_CLOUD_K,
) -> StructuralMetrics:
    """Measure the structure of one storm-centred infrared frame.

    Args:
        bt: 2-D brightness temperature in Kelvin, storm-centred.
        km_per_pixel: ground resolution of one pixel.
        deep_convection_k: threshold below which a pixel counts as deep convection.
        cold_cloud_k: threshold used for the cold-cloud centroid.

    Returns:
        The measured metrics. Fields that cannot be determined from this frame are
        ``None`` rather than a guessed value.
    """
    if bt.ndim != 2:
        raise ValueError(f"expected a 2-D field, got shape {bt.shape}")
    if not np.isfinite(bt).any():
        raise ValueError("brightness-temperature field contains no finite values")

    polar = to_polar(bt, km_per_pixel)
    profile = polar.azimuthal_mean()
    background = background_temperature(bt, km_per_pixel)

    min_bt_k = float(np.nanmin(bt))
    cdo_fraction = _cdo_fraction(bt, km_per_pixel, deep_convection_k, radius_km=100.0)
    ring_radius, ring_bt = _convective_ring(profile, polar.radii_km)
    eye_present, eye_radius, eye_contrast = _detect_eye(polar, profile, ring_radius, ring_bt)
    axisymmetry = _axisymmetry(polar, background)
    cold_offset = _cold_cloud_offset(bt, km_per_pixel, cold_cloud_k)

    return StructuralMetrics(
        eye_present=eye_present,
        eye_radius_km=eye_radius,
        eye_ring_bt_contrast_k=eye_contrast,
        min_bt_k=min_bt_k,
        cdo_fraction_100km=cdo_fraction,
        axisymmetry=axisymmetry,
        convective_ring_radius_km=ring_radius,
        cold_cloud_offset_km=cold_offset,
    )


def _cdo_fraction(
    bt: np.ndarray, km_per_pixel: float, threshold_k: float, *, radius_km: float
) -> float:
    """Fraction of pixels colder than ``threshold_k`` within ``radius_km`` of the centre.

    A proxy for the extent of the central dense overcast: a mature storm has a large,
    continuous cold shield over its core, a sheared one does not.
    """
    rows, cols = bt.shape
    cr, cc = (rows - 1) / 2.0, (cols - 1) / 2.0
    rr, cc_idx = np.ogrid[:rows, :cols]
    dist_km = np.hypot(rr - cr, cc_idx - cc) * km_per_pixel

    within = (dist_km <= radius_km) & np.isfinite(bt)
    if not within.any():
        return 0.0
    return float(np.count_nonzero(bt[within] < threshold_k) / np.count_nonzero(within))


def _convective_ring(
    profile: np.ndarray, radii_km: np.ndarray
) -> tuple[float | None, float]:
    """Radius of the coldest ring of the azimuthal-mean profile, and its temperature.

    In a storm with an eye this is the eyewall. In one without, it is simply where the
    deepest convection sits, which is still the reference the eye contrast is measured
    against.
    """
    band = (radii_km >= 10.0) & (radii_km <= 200.0)
    candidates = np.where(band, profile, np.nan)
    if not np.isfinite(candidates).any():
        return None, float(np.nanmin(profile)) if np.isfinite(profile).any() else float("nan")

    idx = int(np.nanargmin(candidates))
    return float(radii_km[idx]), float(profile[idx])


def _detect_eye(
    polar, profile: np.ndarray, ring_radius_km: float | None, ring_bt: float
) -> tuple[bool, float | None, float | None]:
    """Find a warm core *enclosed* by a markedly colder ring.

    Two conditions, both required:

    1. **Contrast.** The warm centre must be at least ``EYE_CONTRAST_MIN_K`` above the
       coldest ring of the azimuthal-mean profile.
    2. **Enclosure.** At that ring radius, at least ``EYE_ENCLOSURE_MIN`` of the azimuths
       must actually be cold. Contrast alone is not sufficient: a storm whose convection
       has been sheared off to one side leaves a warm centre and, on average, a cold
       ring, so a mean-only test reports an eye where there is plainly none.

    Returns ``(eye_present, eye_radius_km, contrast_k)``. The radius is where the
    azimuthal-mean profile falls halfway from the warm centre to the cold ring, which is
    stable even when the eye edge is gradual.
    """
    radii_km = polar.radii_km
    inner = radii_km <= EYE_SEARCH_KM
    if not inner.any() or not np.isfinite(ring_bt) or ring_radius_km is None:
        return False, None, None

    core = np.where(inner, profile, np.nan)
    if not np.isfinite(core).any():
        return False, None, None

    centre_bt = float(np.nanmax(core))
    contrast = centre_bt - ring_bt
    if not np.isfinite(contrast) or contrast < EYE_CONTRAST_MIN_K:
        return False, None, float(contrast) if np.isfinite(contrast) else None

    half = centre_bt - 0.5 * contrast

    ring_values = polar.ring(ring_radius_km)
    finite = ring_values[np.isfinite(ring_values)]
    if finite.size == 0:
        return False, None, float(contrast)

    enclosure = float(np.count_nonzero(finite <= half) / finite.size)
    if enclosure < EYE_ENCLOSURE_MIN:
        return False, None, float(contrast)

    radius = None
    for r, value in zip(radii_km, profile):
        if np.isfinite(value) and value <= half:
            radius = float(r)
            break

    return True, radius, float(contrast)


def _axisymmetry(polar, background: float) -> float:
    """How rotationally symmetric the cloud field is, on a 0-1 scale.

    Implements ``1 - (wavenumber-1 amplitude / wavenumber-0 amplitude)`` over the
    50-200 km annulus, averaged across radii.

    The one subtlety worth stating: the decomposition runs on the *perturbation* field
    (brightness temperature minus the environmental background), not on the raw Kelvin
    values. Against raw values the wavenumber-0 term is the ~230 K absolute temperature,
    which swamps everything and would leave this metric pinned near 1.0 for every storm.
    Removing the background makes wavenumber-0 the storm's own radial signal, so the
    ratio measures what it is meant to.

    A perfectly circular storm scores 1.0; a one-sided, sheared cloud mass scores near 0.
    """
    band = (polar.radii_km >= SYMMETRY_INNER_KM) & (polar.radii_km <= SYMMETRY_OUTER_KM)
    if not band.any() or not np.isfinite(background):
        return 0.0

    ratios: list[float] = []
    for values in polar.values[band]:
        finite = np.isfinite(values)
        if finite.sum() < 8:
            continue
        series = np.where(finite, values, np.nan)
        series = np.nan_to_num(series, nan=float(np.nanmean(series))) - background

        n = series.size
        spectrum = np.fft.rfft(series)
        wavenumber0 = abs(spectrum[0]) / n            # mean perturbation at this radius
        wavenumber1 = 2.0 * abs(spectrum[1]) / n      # one-sidedness at this radius

        if wavenumber0 < 1e-6:
            continue
        ratios.append(wavenumber1 / wavenumber0)

    if not ratios:
        return 0.0
    return float(np.clip(1.0 - float(np.mean(ratios)), 0.0, 1.0))


def _cold_cloud_offset(bt: np.ndarray, km_per_pixel: float, threshold_k: float) -> float:
    """Distance from the storm centre to the centroid of the coldest cloud.

    A proxy for vertical wind shear: when shear is strong, deep convection is pushed
    downshear and no longer sits over the circulation centre.
    """
    rows, cols = bt.shape
    cr, cc = (rows - 1) / 2.0, (cols - 1) / 2.0

    cold = np.isfinite(bt) & (bt < threshold_k)
    if not cold.any():
        return 0.0

    coords = np.argwhere(cold)
    centroid = coords.mean(axis=0)
    return float(np.hypot(centroid[0] - cr, centroid[1] - cc) * km_per_pixel)
