package com.cyclovision.domain;

/**
 * Where a value came from. Every important output in CycloVision carries one of these.
 *
 * <p>The rules are documented in {@code docs/provenance.md}. The two that matter most:
 * <ul>
 *   <li>{@link #TRAINED_MODEL} requires a {@code model_registry} row with
 *       {@code is_trained = true} and a held-out metric plus the baseline it beats.</li>
 *   <li>{@link #OBSERVED} may only originate from {@code storm_frame} columns read by
 *       this service. The AI service can never emit it.</li>
 * </ul>
 */
public enum Provenance {
    /** Ground truth from a dataset. Never a model output. */
    OBSERVED,
    /** Output of a model trained and evaluated on held-out data. */
    TRAINED_MODEL,
    /** Deterministic physical computation over real data. */
    DERIVED_MEASUREMENT,
    /** Derived from empirical error statistics rather than a fitted predictor. */
    STATISTICAL_BASELINE,
    /** Empirical distribution over retrieved historical analogues. */
    ANALOGUE_ENSEMBLE,
    /** Transparent hand-written rules whose thresholds are shown to the user. */
    RULE_ENGINE,
    /** Language generated over already-computed numbers. May never originate a number. */
    LLM_NARRATION,
    /** Placeholder or seeded value. Not produced by a trained model. */
    DEMO_DATA
}
