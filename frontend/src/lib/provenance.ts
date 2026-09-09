import type { Provenance, Source } from '../types/api'

/**
 * How each provenance tag is presented.
 *
 * The wording matters as much as the colour. "Placeholder" is the honest word for
 * DEMO_DATA, and using it consistently is what keeps a Phase 0 build from looking like a
 * working AI system.
 */
export const PROVENANCE_LABEL: Record<Provenance, string> = {
  OBSERVED: 'Observed',
  TRAINED_MODEL: 'Trained model',
  DERIVED_MEASUREMENT: 'Measured',
  STATISTICAL_BASELINE: 'Empirical baseline',
  ANALOGUE_ENSEMBLE: 'Analogue ensemble',
  RULE_ENGINE: 'Rule engine',
  LLM_NARRATION: 'AI narration',
  DEMO_DATA: 'Placeholder',
}

export const PROVENANCE_DESCRIPTION: Record<Provenance, string> = {
  OBSERVED: 'Ground truth read from the best-track record. Not a model output.',
  TRAINED_MODEL: 'Produced by a model trained and evaluated on held-out storms.',
  DERIVED_MEASUREMENT:
    'Computed deterministically from the raw brightness-temperature field. Not trained, not fitted.',
  STATISTICAL_BASELINE:
    'Derived from the empirical distribution of the model’s own held-out errors.',
  ANALOGUE_ENSEMBLE:
    'The empirical outcome distribution of the closest historical analogues.',
  RULE_ENGINE: 'A transparent hand-written rule. Its thresholds are shown alongside it.',
  LLM_NARRATION:
    'Wording generated over already-computed values. It never originates a number.',
  DEMO_DATA:
    'Placeholder. No trained model produced this — the model bundle is not yet trained.',
}

/** DEMO_DATA is the one tag that needs to catch the eye; the rest recede. */
export function isPlaceholder(source: Source | null | undefined): boolean {
  return source?.provenance === 'DEMO_DATA'
}

/** True when any stamp on the page is a placeholder, which raises the global banner. */
export function anyPlaceholder(sources: (Source | null | undefined)[]): boolean {
  return sources.some(isPlaceholder)
}
