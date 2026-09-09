import clsx from 'clsx'

import { PROVENANCE_DESCRIPTION, PROVENANCE_LABEL } from '../../lib/provenance'
import type { Source } from '../../types/api'

/**
 * The provenance stamp, rendered.
 *
 * Every number in the application carries one of these. They are quiet by design —
 * uppercase micro-type, no fill — except DEMO_DATA, which is the one tag that must catch
 * the eye, because it is the one that says "this did not come from a trained model".
 */
export function ProvenanceChip({
  source,
  className,
}: {
  source: Source | null | undefined
  className?: string
}) {
  if (!source) return null

  const placeholder = source.provenance === 'DEMO_DATA'
  const version = source.model ? `${source.model} ${source.version ?? ''}`.trim() : null
  const metric = source.metric
    ? ` · ${source.metric.name} ${source.metric.value}` +
      (source.metric.baseline ? ` vs ${source.metric.baseline} ${source.metric.baselineValue}` : '')
    : ''

  return (
    <span
      title={`${PROVENANCE_DESCRIPTION[source.provenance]}${version ? `\n\n${version}` : ''}${metric}`}
      className={clsx(
        'inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider',
        placeholder
          ? 'bg-cv-risk-moderate/15 text-cv-risk-moderate'
          : 'text-cv-faint',
        className,
      )}
    >
      {PROVENANCE_LABEL[source.provenance]}
    </span>
  )
}
