import clsx from 'clsx'

import type { StormSummary } from '../../types/api'
import { GlassPanel } from '../ui/GlassPanel'

/**
 * The storm selector, on the left.
 *
 * Recedes deliberately: it is used once at the start of a demo and then ignored, so it
 * is a plain list rather than a grid of cards. Each row states the storm's split, because
 * "held out" is the fact that makes everything the verification screen later claims
 * meaningful.
 */
export function StormRail({
  storms,
  selectedSid,
  onSelect,
  loading,
}: {
  storms: StormSummary[]
  selectedSid: string | null
  onSelect: (sid: string) => void
  loading: boolean
}) {
  return (
    <GlassPanel
      as="aside"
      className="pointer-events-auto absolute top-3 bottom-[132px] left-3 z-20 flex w-[260px] flex-col overflow-hidden"
    >
      <div className="border-b border-cv-glass-border px-4 py-3">
        <h2 className="text-[10px] uppercase tracking-wider text-cv-faint">Storms</h2>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? <RailMessage>Loading…</RailMessage> : null}

        {!loading && storms.length === 0 ? (
          <RailMessage>
            No storms loaded yet. Phase 1 imports the IBTrACS best track and joins it to
            HURSAT satellite frames.
          </RailMessage>
        ) : null}

        {storms.map((storm) => (
          <button
            key={storm.sid}
            type="button"
            onClick={() => onSelect(storm.sid)}
            className={clsx(
              'flex w-full flex-col gap-0.5 border-l-2 px-4 py-2.5 text-left transition-colors duration-150',
              storm.sid === selectedSid
                ? 'border-cv-accent bg-cv-glass-strong'
                : 'border-transparent hover:bg-cv-glass',
            )}
          >
            <span className="flex items-baseline justify-between gap-2">
              <span className="text-[13px] text-cv-text">{storm.name}</span>
              <span className="cv-num text-[11px] text-cv-muted">{storm.seasonYear}</span>
            </span>
            <span className="text-[11px] text-cv-muted">
              {storm.peakCategory
                ? storm.peakCategory.replace(/_/g, ' ').toLowerCase()
                : 'no peak category'}
            </span>
            <span className="cv-num text-[10px] text-cv-faint">
              {storm.frameCount} frames · {storm.framesWithImagery} with imagery ·{' '}
              {storm.split === 'test' ? 'held out' : storm.split}
            </span>
          </button>
        ))}
      </div>
    </GlassPanel>
  )
}

function RailMessage({ children }: { children: React.ReactNode }) {
  return <p className="px-4 py-3 text-[11px] leading-relaxed text-cv-muted">{children}</p>
}
