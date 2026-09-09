import type { AnalogueBlock } from '../../types/api'

/**
 * What happened next to the storms that looked like this one.
 *
 * This is the whole argument for the analogue ensemble being a forecast rather than a
 * curiosity: the retrieved storms are only interesting because of what they went on to
 * do. The rapid-intensification share is shown against the climatological base rate,
 * because a quarter of analogues intensifying rapidly only means something when you know
 * the background rate is about one in twenty.
 */
export function AnalogueOutcomeChart({ analogues }: { analogues: AnalogueBlock }) {
  const { outcome, k } = analogues

  if (k === 0) {
    return (
      <p className="text-[11px] leading-relaxed text-cv-faint">
        No analogues retrieved. The historical index is built in Phase 2 from the joined
        IBTrACS and satellite record.
      </p>
    )
  }

  const total = Math.max(1, outcome.intensifiedCount + outcome.weakenedCount)
  const intensifiedPct = (outcome.intensifiedCount / total) * 100

  return (
    <div className="flex flex-col gap-3">
      <div>
        <div className="mb-1 flex items-baseline justify-between">
          <span className="text-[11px] text-cv-muted">Subsequent 24 hours</span>
          <span className="cv-num text-[11px] text-cv-muted">{k} analogues</span>
        </div>
        <div className="flex h-2 overflow-hidden rounded-full bg-cv-glass-strong">
          <span className="bg-cv-int-5" style={{ width: `${intensifiedPct}%` }} />
          <span className="bg-cv-int-1" style={{ width: `${100 - intensifiedPct}%` }} />
        </div>
        <div className="mt-1 flex justify-between text-[10px] text-cv-faint">
          <span>{outcome.intensifiedCount} intensified</span>
          <span>{outcome.weakenedCount} weakened</span>
        </div>
      </div>

      {outcome.riFraction != null ? (
        <div className="flex items-baseline justify-between border-t border-cv-glass-border pt-2">
          <span className="text-[11px] text-cv-muted">Rapidly intensified</span>
          <span className="cv-num text-[12px] text-cv-truth">
            {outcome.riCount} of {k}
            {outcome.riBaseRate != null ? (
              <span className="ml-1 text-cv-faint">
                (base rate {Math.round(outcome.riBaseRate * 100)}%)
              </span>
            ) : null}
          </span>
        </div>
      ) : null}
    </div>
  )
}
