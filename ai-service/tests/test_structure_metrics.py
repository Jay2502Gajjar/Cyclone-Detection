"""Structural metrics, tested against synthetic brightness-temperature fields.

Synthetic fields are the right test here because we know the answer by construction: if
we build a perfectly circular annulus, symmetry must come out at 1.0, and if we build a
warm hole inside a cold ring, the eye detector must find it at the radius we put it. No
real satellite data is needed to establish that the physics is implemented correctly,
which means these tests run in Phase 0, before any dataset exists.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.structure.metrics import compute_metrics
from app.structure.polar import background_temperature, to_polar

KM_PER_PIXEL = 8.0
GRID = 121  # 121 * 8 km ≈ 960 km across, comparable to a HURSAT tile


def _grid_distance_km(size: int = GRID, km_per_pixel: float = KM_PER_PIXEL) -> np.ndarray:
    centre = (size - 1) / 2.0
    rows, cols = np.ogrid[:size, :size]
    return np.hypot(rows - centre, cols - centre) * km_per_pixel


def uniform_field(value: float = 280.0) -> np.ndarray:
    return np.full((GRID, GRID), value, dtype=float)


def symmetric_annulus(
    *, ring_radius_km: float = 60.0, ring_width_km: float = 40.0,
    ring_bt: float = 195.0, eye_bt: float = 265.0, background: float = 285.0
) -> np.ndarray:
    """A textbook eye: warm centre, cold circular eyewall, warm environment."""
    dist = _grid_distance_km()
    field = np.full((GRID, GRID), background, dtype=float)
    inner = ring_radius_km - ring_width_km / 2
    outer = ring_radius_km + ring_width_km / 2
    field[(dist >= inner) & (dist <= outer)] = ring_bt
    field[dist < inner] = eye_bt
    return field


def one_sided_blob(*, offset_km: float = 120.0, blob_radius_km: float = 90.0) -> np.ndarray:
    """Cold convection displaced well off centre — the signature of strong shear."""
    size = GRID
    centre = (size - 1) / 2.0
    rows, cols = np.ogrid[:size, :size]
    offset_px = offset_km / KM_PER_PIXEL

    field = np.full((size, size), 285.0, dtype=float)
    dist_to_blob = np.hypot(rows - centre, cols - (centre + offset_px)) * KM_PER_PIXEL
    field[dist_to_blob <= blob_radius_km] = 200.0
    return field


class TestPolarRegrid:
    def test_preserves_a_uniform_field(self):
        polar = to_polar(uniform_field(275.0), KM_PER_PIXEL, r_max_km=200.0)
        finite = polar.values[np.isfinite(polar.values)]
        assert np.allclose(finite, 275.0, atol=1e-6)

    def test_samples_outside_the_grid_are_nan_not_clamped(self):
        # r_max well beyond the tile: the outer rings must be missing, not edge-repeated.
        polar = to_polar(uniform_field(), KM_PER_PIXEL, r_max_km=2000.0)
        assert np.isnan(polar.values[-1]).any()

    def test_background_is_read_from_the_outer_annulus(self):
        field = symmetric_annulus(background=288.0)
        assert background_temperature(field, KM_PER_PIXEL) == pytest.approx(288.0, abs=0.5)


class TestAxisymmetry:
    def test_perfect_annulus_is_almost_perfectly_symmetric(self):
        metrics = compute_metrics(symmetric_annulus(), KM_PER_PIXEL)
        assert metrics.axisymmetry > 0.95

    def test_one_sided_convection_is_strongly_asymmetric(self):
        metrics = compute_metrics(one_sided_blob(), KM_PER_PIXEL)
        assert metrics.axisymmetry < 0.5

    def test_symmetric_scores_higher_than_asymmetric(self):
        symmetric = compute_metrics(symmetric_annulus(), KM_PER_PIXEL).axisymmetry
        asymmetric = compute_metrics(one_sided_blob(), KM_PER_PIXEL).axisymmetry
        assert symmetric > asymmetric

    def test_bounded_to_unit_interval(self):
        for field in (uniform_field(), symmetric_annulus(), one_sided_blob()):
            value = compute_metrics(field, KM_PER_PIXEL).axisymmetry
            assert 0.0 <= value <= 1.0


class TestEyeDetection:
    def test_finds_a_warm_core_inside_a_cold_ring(self):
        metrics = compute_metrics(symmetric_annulus(), KM_PER_PIXEL)
        assert metrics.eye_present is True
        assert metrics.eye_radius_km is not None
        # The eye edge sits inside the eyewall's inner boundary (60 - 40/2 = 40 km).
        assert 0 < metrics.eye_radius_km <= 60

    def test_reports_the_eye_to_eyewall_contrast(self):
        metrics = compute_metrics(symmetric_annulus(eye_bt=265.0, ring_bt=195.0), KM_PER_PIXEL)
        assert metrics.eye_ring_bt_contrast_k == pytest.approx(70.0, abs=8.0)

    def test_no_eye_in_a_uniform_field(self):
        metrics = compute_metrics(uniform_field(), KM_PER_PIXEL)
        assert metrics.eye_present is False
        assert metrics.eye_radius_km is None

    def test_no_eye_in_displaced_convection(self):
        # A sheared storm leaves a warm centre with cold cloud on one side only. That
        # produces a real eye-to-ring contrast in the azimuthal mean, so contrast alone
        # would report an eye here. The enclosure check is what prevents it.
        metrics = compute_metrics(one_sided_blob(), KM_PER_PIXEL)
        assert metrics.eye_present is False

    def test_partial_eyewall_is_not_an_eye(self):
        # Half a cold ring: strong contrast, but the convection does not encircle the
        # centre, so this is an incomplete eyewall rather than an eye.
        field = symmetric_annulus()
        field[:, : GRID // 2] = 285.0
        metrics = compute_metrics(field, KM_PER_PIXEL)
        assert metrics.eye_present is False


class TestColdCloudOffset:
    def test_centred_convection_has_near_zero_offset(self):
        metrics = compute_metrics(symmetric_annulus(), KM_PER_PIXEL)
        assert metrics.cold_cloud_offset_km < 10.0

    def test_displaced_convection_recovers_the_offset(self):
        metrics = compute_metrics(one_sided_blob(offset_km=120.0), KM_PER_PIXEL)
        assert metrics.cold_cloud_offset_km == pytest.approx(120.0, abs=15.0)


class TestConvectionMetrics:
    def test_min_bt_is_the_coldest_pixel(self):
        metrics = compute_metrics(symmetric_annulus(ring_bt=192.5), KM_PER_PIXEL)
        assert metrics.min_bt_k == pytest.approx(192.5, abs=0.01)

    def test_cdo_fraction_is_zero_for_a_warm_uniform_field(self):
        metrics = compute_metrics(uniform_field(285.0), KM_PER_PIXEL)
        assert metrics.cdo_fraction_100km == 0.0

    def test_cdo_fraction_is_one_for_a_uniformly_cold_field(self):
        metrics = compute_metrics(uniform_field(190.0), KM_PER_PIXEL)
        assert metrics.cdo_fraction_100km == pytest.approx(1.0)

    def test_convective_ring_radius_matches_the_constructed_eyewall(self):
        metrics = compute_metrics(symmetric_annulus(ring_radius_km=60.0), KM_PER_PIXEL)
        assert metrics.convective_ring_radius_km == pytest.approx(60.0, abs=20.0)


class TestInputValidation:
    def test_rejects_a_non_2d_field(self):
        with pytest.raises(ValueError, match="2-D"):
            compute_metrics(np.zeros((4, 4, 3)), KM_PER_PIXEL)

    def test_rejects_an_all_nan_field(self):
        with pytest.raises(ValueError, match="no finite values"):
            compute_metrics(np.full((GRID, GRID), np.nan), KM_PER_PIXEL)

    def test_rejects_a_non_positive_pixel_size(self):
        with pytest.raises(ValueError, match="km_per_pixel"):
            to_polar(uniform_field(), 0.0)

    def test_tolerates_missing_pixels(self):
        field = symmetric_annulus()
        field[0:5, 0:5] = np.nan
        metrics = compute_metrics(field, KM_PER_PIXEL)
        assert math.isfinite(metrics.axisymmetry)
