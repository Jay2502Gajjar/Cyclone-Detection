import clsx from 'clsx'
import type { ReactNode } from 'react'

import { ProvenanceChip } from './ProvenanceChip'
import type { Source } from '../../types/api'

/**
 * A labelled figure with its provenance.
 *
 * Label above, value below, left-aligned — not centred in a tile. Centred numbers in
 * boxes is the visual grammar of a dashboard; a column of aligned figures reads as an
 * instrument.
 */
export function Metric({
  label,
  value,
  source,
  hint,
  size = 'md',
  className,
}: {
  label: string
  value: ReactNode
  source?: Source | null
  hint?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}) {
  return (
    <div className={clsx('flex flex-col gap-0.5', className)}>
      <div className="flex items-center gap-1.5">
        <span className="text-[10px] uppercase tracking-wider text-cv-faint">{label}</span>
        {source ? <ProvenanceChip source={source} /> : null}
      </div>
      <span
        className={clsx(
          'cv-num text-cv-truth',
          size === 'lg' && 'text-[32px] leading-none',
          size === 'md' && 'text-[18px] leading-tight',
          size === 'sm' && 'text-[13px] leading-tight',
        )}
      >
        {value}
      </span>
      {hint ? <span className="text-[11px] text-cv-muted">{hint}</span> : null}
    </div>
  )
}
