"""The model registry: the single place a provenance stamp can be created.

This module exists to make one class of mistake impossible rather than merely
discouraged. Invariant I3 says an untrained model can never emit ``TRAINED_MODEL``, and
the way that is guaranteed is that :func:`ModelRegistry.stamp` is the only constructor of
a ``Source`` anywhere in the service. A component declares what it *would* be if it were
loaded and working; the registry decides what it actually gets to claim.

Two rules, applied in order:

1. A component declaring ``TRAINED_MODEL`` while ``is_trained`` is false is downgraded
   to ``DEMO_DATA``.
2. A component that is not available — no weights on disk, thresholds not yet
   calibrated, no data to measure — is downgraded to ``DEMO_DATA`` regardless of what it
   declares.

In Phase 0 every component fails at least one of those, so every stamp in the whole
service comes back ``DEMO_DATA``. That is the correct state of the system, and the
frontend surfaces it as a banner. It is impossible for this build to look like a working
AI system, which is exactly the point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from app.schemas.common import MetricInfo, Provenance, Source


@dataclass
class RegisteredComponent:
    """One model or deterministic component, and what it is allowed to claim."""

    key: str
    version: str
    declared_provenance: Provenance
    is_trained: bool = False
    available: bool = False
    impl: Any | None = None
    metric: MetricInfo | None = None
    notes: str | None = None

    def effective_provenance(self) -> Provenance:
        """What this component may actually claim, after the registry's rules."""
        if self.declared_provenance == Provenance.TRAINED_MODEL and not self.is_trained:
            return Provenance.DEMO_DATA
        if not self.available:
            return Provenance.DEMO_DATA
        return self.declared_provenance


class ModelRegistry:
    """Holds every component and issues every provenance stamp."""

    def __init__(self) -> None:
        self._components: dict[str, RegisteredComponent] = {}

    def register(self, component: RegisteredComponent) -> None:
        if (
            component.declared_provenance == Provenance.TRAINED_MODEL
            and component.is_trained
            and component.metric is None
        ):
            # A trained-model claim without a held-out metric is not auditable, so it is
            # not accepted. The database enforces the same rule on model_registry rows.
            raise ValueError(
                f"component '{component.key}' claims TRAINED_MODEL but reports no "
                f"held-out metric; a claim we cannot show evidence for is not allowed"
            )
        self._components[component.key] = component
        logger.info(
            "registered {} v{} declared={} effective={} trained={} available={}",
            component.key,
            component.version,
            component.declared_provenance.value,
            component.effective_provenance().value,
            component.is_trained,
            component.available,
        )

    def get(self, key: str) -> RegisteredComponent:
        if key not in self._components:
            raise KeyError(f"no component registered under '{key}'")
        return self._components[key]

    def has(self, key: str) -> bool:
        return key in self._components

    def impl(self, key: str) -> Any:
        return self.get(key).impl

    def is_usable(self, key: str) -> bool:
        """True when the component is loaded and can actually be run."""
        return self.has(key) and self.get(key).available and self.get(key).impl is not None

    def stamp(self, key: str, *, available: bool | None = None) -> Source:
        """Produce the provenance stamp for a component's output.

        Args:
            key: the registered component key.
            available: optionally override availability for this one call — used when a
                component is loaded but cannot run on *this* input, for example a
                structural measurement on a frame that has no satellite imagery.
        """
        component = self.get(key)
        effective = component.effective_provenance()

        if available is False:
            effective = Provenance.DEMO_DATA

        return Source(
            provenance=effective,
            model=component.key,
            version=component.version,
            isTrained=component.is_trained,
            metric=component.metric if effective == Provenance.TRAINED_MODEL else None,
        )

    def health(self) -> list[dict]:
        return [
            {
                "key": c.key,
                "version": c.version,
                "provenance": c.effective_provenance().value,
                "isTrained": c.is_trained,
            }
            for c in sorted(self._components.values(), key=lambda c: c.key)
        ]

    def all(self) -> list[RegisteredComponent]:
        return list(self._components.values())


registry = ModelRegistry()
"""Process-wide registry. Populated once at startup by :func:`load_all`."""


def load_all(settings) -> ModelRegistry:
    """Register every component at boot.

    Phase 0 registers real implementations where they exist (the structural metrics and
    regime rules are genuine deterministic code) and placeholders where they do not.
    Nothing is loaded per request: a demo cannot afford model loading on the interaction
    path.
    """
    from app.inference import placeholders

    registry._components.clear()

    # --- Trained models: none yet. Placeholders stand in behind the real interfaces. ---
    registry.register(
        RegisteredComponent(
            key="ir_intensity",
            version=settings.bundle_version,
            declared_provenance=Provenance.TRAINED_MODEL,
            is_trained=False,
            available=False,
            impl=placeholders.PlaceholderIntensityEstimator(),
            notes="Phase 2: EfficientNet-B0 Vmax regression trained on HURSAT IR frames "
            "labelled from IBTrACS best-track intensity.",
        )
    )
    registry.register(
        RegisteredComponent(
            key="dvmax_ri",
            version=settings.bundle_version,
            declared_provenance=Provenance.TRAINED_MODEL,
            is_trained=False,
            available=False,
            impl=placeholders.PlaceholderIntensityChangeModel(),
            notes="Phase 2: XGBoost 24h intensity change and rapid-intensification "
            "probability over fused image, structural and track features.",
        )
    )
    registry.register(
        RegisteredComponent(
            key="track_cliper",
            version=settings.bundle_version,
            declared_provenance=Provenance.TRAINED_MODEL,
            is_trained=False,
            available=False,
            impl=placeholders.PersistenceTrackModel(),
            notes="Phase 2: CLIPER-style gradient-boosted track model, benchmarked "
            "against pure persistence.",
        )
    )
    registry.register(
        RegisteredComponent(
            key="track_cone",
            version=settings.bundle_version,
            declared_provenance=Provenance.STATISTICAL_BASELINE,
            available=False,
            notes="Phase 2: cone radii become p67/p90 percentiles of the track model's "
            "own held-out error, making the cone empirical rather than chosen.",
        )
    )
    registry.register(
        RegisteredComponent(
            key="analogue",
            version=settings.bundle_version,
            declared_provenance=Provenance.ANALOGUE_ENSEMBLE,
            available=False,
            impl=placeholders.PlaceholderAnalogueIndex(),
            notes="Phase 2: KNN over 24h evolution windows, excluding same-storm and "
            "same-season neighbours.",
        )
    )

    # --- Deterministic components: real code, waiting on real data / calibration. ---
    registry.register(
        RegisteredComponent(
            key="structure",
            version=settings.bundle_version,
            declared_provenance=Provenance.DERIVED_MEASUREMENT,
            # The code is real and tested; availability is decided per request by whether
            # a brightness-temperature array actually exists for the frame.
            available=True,
            notes="Deterministic metrics over the raw brightness-temperature field.",
        )
    )
    registry.register(
        RegisteredComponent(
            key="regime_rules",
            version=settings.bundle_version,
            declared_provenance=Provenance.RULE_ENGINE,
            # Thresholds are documented starting points, not yet tuned on held-out data,
            # so the engine is registered as uncalibrated and its output stamps DEMO_DATA.
            available=False,
            notes="Transparent threshold rules; thresholds tuned in Phase 2.",
        )
    )
    registry.register(
        RegisteredComponent(
            key="risk_rules",
            version=settings.bundle_version,
            declared_provenance=Provenance.RULE_ENGINE,
            available=False,
            notes="Weighted risk formula; the formula and its terms are always returned "
            "alongside the score.",
        )
    )
    registry.register(
        RegisteredComponent(
            key="report_template",
            version=settings.bundle_version,
            declared_provenance=Provenance.RULE_ENGINE,
            available=True,
            notes="Deterministic string interpolation over already-computed values. "
            "Never originates a number.",
        )
    )

    trained = sum(1 for c in registry.all() if c.is_trained)
    logger.warning(
        "model bundle '{}' loaded: {} components, {} trained. "
        "Every output will be stamped DEMO_DATA until Phase 2.",
        settings.bundle_version,
        len(registry.all()),
        trained,
    )
    return registry
