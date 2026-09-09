"""The regime rule engine.

What matters here is not that the thresholds are right — they are documented starting
points, tuned in Phase 2 — but that the engine is honest about how it reached a label,
and that it declines to guess when it has nothing to work with.
"""

from __future__ import annotations

import pytest

from app.structure.metrics import StructuralMetrics
from app.structure.regime_rules import REGIME_LABELS, classify


def metrics(**overrides) -> StructuralMetrics:
    base = dict(
        eye_present=False,
        eye_radius_km=None,
        eye_ring_bt_contrast_k=None,
        min_bt_k=210.0,
        cdo_fraction_100km=0.3,
        axisymmetry=0.5,
        convective_ring_radius_km=60.0,
        cold_cloud_offset_km=10.0,
    )
    base.update(overrides)
    return StructuralMetrics(**base)


class TestRegimeAssignment:
    def test_eye_pattern(self):
        result = classify(
            metrics(eye_present=True, axisymmetry=0.89, cold_cloud_offset_km=9.0)
        )
        assert result.regime == "EYE"

    def test_central_dense_overcast(self):
        result = classify(
            metrics(cdo_fraction_100km=0.88, axisymmetry=0.70, cold_cloud_offset_km=15.0)
        )
        assert result.regime == "CENTRAL_DENSE_OVERCAST"

    def test_banding(self):
        result = classify(
            metrics(cdo_fraction_100km=0.35, axisymmetry=0.40, cold_cloud_offset_km=20.0)
        )
        assert result.regime == "BANDING"

    def test_sheared(self):
        result = classify(metrics(cdo_fraction_100km=0.7, cold_cloud_offset_km=120.0))
        assert result.regime == "SHEARED"

    def test_disorganised(self):
        result = classify(metrics(cdo_fraction_100km=0.05, axisymmetry=0.2))
        assert result.regime == "DISORGANISED"

    def test_every_regime_is_reachable(self):
        reached = {
            classify(
                metrics(eye_present=True, axisymmetry=0.89, cold_cloud_offset_km=9.0)
            ).regime,
            classify(metrics(cdo_fraction_100km=0.88, axisymmetry=0.70)).regime,
            classify(metrics(cdo_fraction_100km=0.35, axisymmetry=0.40)).regime,
            classify(metrics(cold_cloud_offset_km=120.0)).regime,
            classify(metrics(cdo_fraction_100km=0.05, axisymmetry=0.2)).regime,
        }
        assert reached == set(REGIME_LABELS)


class TestTransparency:
    def test_reports_the_thresholds_that_fired(self):
        result = classify(
            metrics(eye_present=True, axisymmetry=0.89, cold_cloud_offset_km=9.0)
        )
        assert any("axisymmetry" in rule for rule in result.rules_applied)
        assert any("eyePresent" in rule for rule in result.rules_applied)

    def test_every_label_has_readable_text(self):
        for regime in REGIME_LABELS:
            assert REGIME_LABELS[regime]
            assert not REGIME_LABELS[regime].isupper()

    def test_shear_overrides_an_apparently_cold_core(self):
        # Displaced convection wins: the cold shield is real but no longer sits over the
        # circulation centre, so calling it a CDO would misdescribe the storm.
        result = classify(
            metrics(cdo_fraction_100km=0.9, axisymmetry=0.8, cold_cloud_offset_km=150.0)
        )
        assert result.regime == "SHEARED"


class TestAbsentInput:
    def test_returns_no_label_when_there_is_nothing_to_classify(self):
        result = classify(None)
        assert result.regime is None
        assert result.label is None
        assert result.rules_applied == []

    @pytest.mark.parametrize("offset", [59.9, 60.0])
    def test_shear_threshold_boundary(self, offset):
        result = classify(metrics(cold_cloud_offset_km=offset, cdo_fraction_100km=0.05))
        expected = "SHEARED" if offset >= 60.0 else "DISORGANISED"
        assert result.regime == expected
