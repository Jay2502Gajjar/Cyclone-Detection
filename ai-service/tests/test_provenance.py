"""Invariant I3 — an untrained component can never claim to be a trained model.

The registry is the only constructor of a provenance stamp in the service, so testing it
tests every stamp the service can emit.
"""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.registry import ModelRegistry, RegisteredComponent, load_all
from app.schemas.common import MetricInfo, Provenance


@pytest.fixture
def registry() -> ModelRegistry:
    return ModelRegistry()


class TestRegistryEnforcement:
    def test_untrained_trained_model_claim_is_downgraded(self, registry):
        registry.register(
            RegisteredComponent(
                key="ir_intensity",
                version="phase0",
                declared_provenance=Provenance.TRAINED_MODEL,
                is_trained=False,
                available=True,
            )
        )
        assert registry.stamp("ir_intensity").provenance is Provenance.DEMO_DATA

    def test_unavailable_component_is_downgraded_whatever_it_declares(self, registry):
        registry.register(
            RegisteredComponent(
                key="regime_rules",
                version="phase0",
                declared_provenance=Provenance.RULE_ENGINE,
                available=False,
            )
        )
        assert registry.stamp("regime_rules").provenance is Provenance.DEMO_DATA

    def test_available_deterministic_component_keeps_its_claim(self, registry):
        registry.register(
            RegisteredComponent(
                key="structure",
                version="phase0",
                declared_provenance=Provenance.DERIVED_MEASUREMENT,
                available=True,
            )
        )
        assert registry.stamp("structure").provenance is Provenance.DERIVED_MEASUREMENT

    def test_per_request_availability_override_downgrades(self, registry):
        registry.register(
            RegisteredComponent(
                key="structure",
                version="phase0",
                declared_provenance=Provenance.DERIVED_MEASUREMENT,
                available=True,
            )
        )
        # Loaded and working, but this particular frame has no imagery to measure.
        stamped = registry.stamp("structure", available=False)
        assert stamped.provenance is Provenance.DEMO_DATA

    def test_trained_model_with_evidence_keeps_its_claim(self, registry):
        registry.register(
            RegisteredComponent(
                key="ir_intensity",
                version="v1.2",
                declared_provenance=Provenance.TRAINED_MODEL,
                is_trained=True,
                available=True,
                metric=MetricInfo(
                    name="MAE (kt)",
                    value=12.4,
                    baseline="mean predictor",
                    baselineValue=24.1,
                    n=1204,
                ),
            )
        )
        stamped = registry.stamp("ir_intensity")
        assert stamped.provenance is Provenance.TRAINED_MODEL
        assert stamped.metric is not None
        assert stamped.metric.baseline == "mean predictor"

    def test_trained_model_without_a_held_out_metric_is_refused(self, registry):
        with pytest.raises(ValueError, match="held-out metric"):
            registry.register(
                RegisteredComponent(
                    key="ir_intensity",
                    version="v1.2",
                    declared_provenance=Provenance.TRAINED_MODEL,
                    is_trained=True,
                    available=True,
                )
            )

    def test_metric_is_withheld_when_the_claim_is_downgraded(self, registry):
        registry.register(
            RegisteredComponent(
                key="dvmax_ri",
                version="phase0",
                declared_provenance=Provenance.TRAINED_MODEL,
                is_trained=False,
                available=False,
                metric=MetricInfo(name="MAE (kt)", value=9.8),
            )
        )
        assert registry.stamp("dvmax_ri").metric is None

    def test_unknown_component_raises_rather_than_defaulting(self, registry):
        with pytest.raises(KeyError):
            registry.stamp("does_not_exist")


class TestPhase0Bundle:
    def test_no_component_is_trained_in_phase_0(self):
        loaded = load_all(get_settings())
        assert all(not c.is_trained for c in loaded.all())

    def test_no_phase_0_component_claims_a_trained_model(self):
        loaded = load_all(get_settings())
        for component in loaded.all():
            assert loaded.stamp(component.key).provenance is not Provenance.TRAINED_MODEL, (
                f"{component.key} must not claim TRAINED_MODEL before it is trained"
            )

    def test_untrained_model_components_stamp_demo_data(self):
        loaded = load_all(get_settings())
        # The five model-backed components. The deterministic ones (structure,
        # report_template) are genuinely available and legitimately claim more.
        for key in ("ir_intensity", "dvmax_ri", "track_cliper", "track_cone", "analogue"):
            assert loaded.stamp(key).provenance is Provenance.DEMO_DATA

    def test_uncalibrated_rule_engines_stamp_demo_data(self):
        loaded = load_all(get_settings())
        for key in ("regime_rules", "risk_rules"):
            assert loaded.stamp(key).provenance is Provenance.DEMO_DATA

    def test_health_reports_the_effective_provenance(self):
        loaded = load_all(get_settings())
        entries = loaded.health()
        assert len(entries) == 9
        assert all(entry["isTrained"] is False for entry in entries)
