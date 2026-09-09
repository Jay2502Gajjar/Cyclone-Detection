import {
  humaniseCategory,
  knots,
  percent,
  ratio,
  signedKnots,
} from '../../lib/format'
import type { ForecastResponse, FrameAnalysis, TrackFrame } from '../../types/api'
import { ConfidenceBar } from '../ui/ConfidenceBar'
import { GlassPanel } from '../ui/GlassPanel'
import { Metric } from '../ui/Metric'
import { ProvenanceChip } from '../ui/ProvenanceChip'
import { VerificationReadout } from '../viz/VerificationReadout'

/**
 * The intelligence panel: six facts, no scrolling, on the right.
 *
 * Ordered by what a viewer needs first — what the storm is doing now, what the satellite
 * structure says, where it is going, what history suggests, how risky it is. Detail lives
 * behind the two drawer buttons at the bottom, so the panel stays readable in a glance
 * and the deeper evidence is one click away rather than in the way.
 */
export function IntelligencePanel({
  frame,
  currentTrackFrame,
  forecast,
  mode,
  onRunForecast,
  onReveal,
  onOpenEvidence,
  onOpenAnalogues,
  forecastPending,
  revealed,
}: {
  frame: FrameAnalysis | undefined
  currentTrackFrame: TrackFrame | null
  forecast: ForecastResponse | null
  mode: 'explore' | 'verify'
  onRunForecast: () => void
  onReveal: () => void
  onOpenEvidence: () => void
  onOpenAnalogues: () => void
  forecastPending: boolean
  revealed: boolean
}) {
  const observed = frame?.observed
  const structure = frame?.structure
  const intensity = forecast?.intensityForecast
  const analogues = forecast?.analogues
  const risk = forecast?.risk

  return (
    <GlassPanel
      as="aside"
      className="pointer-events-auto absolute top-3 right-3 bottom-[132px] z-20 flex w-[340px] flex-col overflow-y-auto"
    >
      <div className="flex flex-col gap-5 px-5 py-4">
        {/* --- Observed state --------------------------------------------------- */}
        <Metric
          label="Sustained wind"
          value={knots(observed?.vmaxKt ?? currentTrackFrame?.vmaxKt)}
          source={observed?.source}
          size="lg"
          hint={humaniseCategory(observed?.category ?? currentTrackFrame?.category)}
        />

        {/* --- Structure -------------------------------------------------------- */}
        <Section title="Satellite structure">
          {structure?.regime ? (
            <>
              <p className="text-[13px] text-cv-text">{structure.regimeLabel}</p>
              <div className="mt-1 flex items-center gap-3 text-[11px] text-cv-muted">
                <span className="cv-num">symmetry {ratio(structure.axisymmetry)}</span>
                {structure.eyePresent ? <span>eye detected</span> : null}
              </div>
              <ProvenanceChip source={structure.regimeSource} className="mt-1.5" />
            </>
          ) : (
            <Absent>
              No satellite frame is matched to this observation, so no structural
              measurement was made.
            </Absent>
          )}
        </Section>

        {/* --- Intensity forecast ----------------------------------------------- */}
        <Section title="Intensity outlook">
          {intensity?.deltaVmax24hKt != null ? (
            <>
              <p className="cv-num text-[18px] text-cv-truth">
                {signedKnots(intensity.deltaVmax24hKt)}{' '}
                <span className="text-[11px] text-cv-muted">over 24 h</span>
              </p>
              {intensity.riProbability != null ? (
                <p className="mt-1 text-[11px] text-cv-muted">
                  Rapid intensification {percent(intensity.riProbability)}
                  {intensity.riBaseRate != null
                    ? ` · base rate ${percent(intensity.riBaseRate)}`
                    : ''}
                </p>
              ) : null}
              <div className="mt-2">
                <ConfidenceBar confidence={intensity.confidence} />
              </div>
              <ProvenanceChip source={intensity.source} className="mt-1.5" />
            </>
          ) : (
            <Absent>
              {forecast
                ? 'The intensity model is not trained yet, so no forecast is offered.'
                : 'Run a forecast to see the intensity outlook.'}
            </Absent>
          )}
        </Section>

        {/* --- Analogues -------------------------------------------------------- */}
        <Section title="Historical analogues">
          {analogues && analogues.matches.length > 0 ? (
            <>
              <p className="text-[13px] text-cv-text">
                {analogues.outcome.intensifiedCount} of {analogues.k} intensified
              </p>
              <p className="mt-1 text-[11px] text-cv-muted">
                {analogues.outcome.riCount} underwent rapid intensification
              </p>
              <ProvenanceChip source={analogues.source} className="mt-1.5" />
            </>
          ) : (
            <Absent>
              {forecast
                ? 'The historical analogue index is not built yet.'
                : 'Run a forecast to retrieve analogues.'}
            </Absent>
          )}
        </Section>

        {/* --- Risk ------------------------------------------------------------- */}
        <Section title="Risk">
          {risk?.level ? (
            <>
              <p className="text-[13px] text-cv-text">
                {risk.level} <span className="cv-num text-cv-muted">{ratio(risk.score)}</span>
              </p>
              <ProvenanceChip source={risk.source} className="mt-1.5" />
            </>
          ) : (
            <Absent>
              {risk?.formula
                ? 'Not all terms of the risk formula are available yet, so no score is shown.'
                : 'Run a forecast to assess risk.'}
            </Absent>
          )}
        </Section>

        {/* --- Verify ----------------------------------------------------------- */}
        {mode === 'verify' ? (
          <Section title="Rewind & verify">
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={onRunForecast}
                disabled={forecastPending || !currentTrackFrame}
                className="rounded-lg bg-cv-accent-dim px-3 py-2 text-[12px] text-cv-accent transition-colors duration-150 hover:bg-cv-accent/25 disabled:opacity-40"
              >
                {forecastPending ? 'Forecasting…' : 'Forecast from this moment'}
              </button>
              {forecast ? (
                <button
                  type="button"
                  onClick={onReveal}
                  className="rounded-lg border border-cv-glass-border px-3 py-2 text-[12px] text-cv-muted transition-colors duration-150 hover:text-cv-text"
                >
                  {revealed ? 'Hide what happened' : 'Reveal what happened'}
                </button>
              ) : null}
              {revealed && forecast?.verification ? (
                <VerificationReadout verification={forecast.verification} />
              ) : null}
            </div>
          </Section>
        ) : null}

        {/* --- Report ----------------------------------------------------------- */}
        {forecast?.report ? (
          <Section title="Summary">
            <p className="text-[12px] leading-relaxed text-cv-muted">
              {forecast.report.text}
            </p>
            <ProvenanceChip source={forecast.report.source} className="mt-1.5" />
          </Section>
        ) : null}
      </div>

      {/* --- Progressive disclosure ---------------------------------------------- */}
      <div className="mt-auto flex gap-2 border-t border-cv-glass-border px-5 py-3">
        <DrawerButton onClick={onOpenEvidence}>Why?</DrawerButton>
        <DrawerButton onClick={onOpenAnalogues}>Analogues</DrawerButton>
      </div>
    </GlassPanel>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-cv-glass-border pt-4 first:border-0 first:pt-0">
      <h3 className="mb-1.5 text-[10px] uppercase tracking-wider text-cv-faint">{title}</h3>
      {children}
    </section>
  )
}

/** Absent is not the same as zero. Saying why keeps a gap from reading as a bug. */
function Absent({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] leading-relaxed text-cv-faint">{children}</p>
}

function DrawerButton({
  children,
  onClick,
}: {
  children: React.ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex-1 rounded-lg border border-cv-glass-border px-3 py-1.5 text-[12px] text-cv-muted transition-colors duration-150 hover:text-cv-text"
    >
      {children}
    </button>
  )
}
