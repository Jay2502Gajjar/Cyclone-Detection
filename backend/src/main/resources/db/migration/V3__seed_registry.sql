-- Phase 0 model registry.
--
-- Every component is registered up front so the Model Card and /api/health can report
-- the true state of the system from the first run. All seven are DEMO_DATA with
-- is_trained = false, because in Phase 0 nothing is trained. Phase 2 updates these rows
-- in place as each model is trained and evaluated, and the DEMO_DATA chips disappear
-- from the UI one at a time — visible, honest progress.

INSERT INTO model_registry (model_key, version, provenance, is_trained, notes) VALUES
    ('ir_intensity',  'phase0', 'DEMO_DATA', FALSE,
     'Placeholder. Phase 2: EfficientNet-B0 Vmax regression + category head, trained on '
     || 'HURSAT IR frames labelled from IBTrACS best-track intensity.'),
    ('dvmax_ri',      'phase0', 'DEMO_DATA', FALSE,
     'Placeholder. Phase 2: XGBoost 24h intensity change + rapid-intensification '
     || 'probability over fused image, structural and track features.'),
    ('track_cliper',  'phase0', 'DEMO_DATA', FALSE,
     'Placeholder. Phase 2: CLIPER-style gradient-boosted track model, benchmarked '
     || 'against pure persistence.'),
    ('track_cone',    'phase0', 'DEMO_DATA', FALSE,
     'Placeholder. Phase 2: cone radii become the p67/p90 percentiles of the track '
     || 'model''s own held-out error, making the cone empirical rather than chosen.'),
    ('analogue',      'phase0', 'DEMO_DATA', FALSE,
     'Placeholder. Phase 2: KNN over 24h evolution windows, excluding same-storm and '
     || 'same-season neighbours.'),
    ('structure',     'phase0', 'DEMO_DATA', FALSE,
     'Deterministic metrics over the raw brightness-temperature field. Becomes '
     || 'DERIVED_MEASUREMENT in Phase 1, when real BT arrays exist to measure.'),
    ('regime_rules',  'phase0', 'DEMO_DATA', FALSE,
     'Transparent threshold rules over the structural metrics. Becomes RULE_ENGINE in '
     || 'Phase 2, once thresholds are tuned on held-out data.'),
    ('risk_rules',    'phase0', 'DEMO_DATA', FALSE,
     'Weighted risk formula. Becomes RULE_ENGINE in Phase 3; the formula and its terms '
     || 'are always returned with the score.');
