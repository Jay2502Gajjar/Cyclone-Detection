import { formatUtc, ratio, signedKnots } from '../../lib/format'
import type { ForecastResponse } from '../../types/api'
import { Drawer } from '../ui/Drawer'
import { ProvenanceChip } from '../ui/ProvenanceChip'
import { AnalogueOutcomeChart } from '../viz/AnalogueOutcomeChart'

/**
 * The analogue ensemble, in full.
 *
 * The outcome distribution comes first and the individual matches second, because the
 * aggregate is the forecast and the named storms are the evidence for it. Presenting the
 * list first would turn this back into the "similar storms" card the design explicitly
 * rejected.
 */
export function AnaloguesDrawer({
  open,
  onOpenChange,
  forecast,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  forecast: ForecastResponse | null
}) {
  const analogues = forecast?.analogues

  return (
    <Drawer
      open={open}
      onOpenChange={onOpenChange}
      title="Historical analogues"
      subtitle="Storms whose last 24 hours of evolution resemble this one, and what they did next"
    >
      {!analogues ? (
        <p className="text-[11px] text-cv-faint">
          Run a forecast to retrieve analogues for this moment.
        </p>
      ) : (
        <div className="flex flex-col gap-6">
          <section>
            <div className="mb-2 flex items-center gap-2">
              <h3 className="text-[10px] uppercase tracking-wider text-cv-faint">
                Ensemble outcome
              </h3>
              <ProvenanceChip source={analogues.source} />
            </div>
            <AnalogueOutcomeChart analogues={analogues} />
          </section>

          <section>
            <h3 className="mb-2 text-[10px] uppercase tracking-wider text-cv-faint">
              Closest matches
            </h3>
            {analogues.matches.length === 0 ? (
              <p className="text-[11px] leading-relaxed text-cv-faint">
                No matches. The analogue index is built in Phase 2 from the joined
                historical record.
              </p>
            ) : (
              <ul className="flex flex-col">
                {analogues.matches.map((match) => (
                  <li
                    key={`${match.sid}-${match.rank}`}
                    className="flex items-baseline justify-between gap-4 border-b border-cv-glass-border py-2 last:border-0"
                  >
                    <div className="flex flex-col">
                      <span className="text-[12px] text-cv-text">
                        {match.rank}. {match.name}
                      </span>
                      <span className="text-[10px] text-cv-faint">
                        {formatUtc(match.time)}
                      </span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="cv-num text-[12px] text-cv-truth">
                        {signedKnots(match.outcomeDeltaVmax24hKt)}
                      </span>
                      <span className="cv-num text-[10px] text-cv-faint">
                        similarity {ratio(match.similarity)}
                        {match.wasRi ? ' · RI' : ''}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {analogues.exclusions.length > 0 ? (
            <section className="border-t border-cv-glass-border pt-4">
              <h3 className="mb-1.5 text-[10px] uppercase tracking-wider text-cv-faint">
                Exclusions
              </h3>
              <p className="text-[11px] leading-relaxed text-cv-muted">
                {analogues.exclusions.join(', ')} neighbours are excluded, so a storm
                cannot be retrieved as its own analogue and a same-season neighbour cannot
                leak the outcome we are trying to forecast.
              </p>
            </section>
          ) : null}
        </div>
      )}
    </Drawer>
  )
}
