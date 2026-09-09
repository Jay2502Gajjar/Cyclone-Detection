import { Link } from 'react-router-dom'

import { useModelCard } from '../hooks/useModelCard'
import { PROVENANCE_LABEL } from '../lib/provenance'
import type { ModelRow } from '../types/api'

/**
 * The credibility screen.
 *
 * It exists to answer "how do I know any of this is real?" without the answer being
 * "trust us". Datasets with counts, a storm-wise split, every model with its held-out
 * metric and the baseline it beats, the fusion ablation, cone calibration — and a list of
 * what we deliberately did not build.
 *
 * It is built in Phase 0, before there is anything flattering to put on it. A page that
 * only appears once the numbers are good is a marketing page; one that reports an
 * untrained bundle honestly is an audit trail.
 */
export function ModelCard() {
  const { data, isLoading } = useModelCard()

  return (
    <div className="h-full overflow-y-auto bg-cv-ground">
      <div className="mx-auto max-w-[880px] px-8 py-10">
        <header className="mb-8 flex items-baseline justify-between">
          <div>
            <h1 className="text-[24px] font-medium tracking-tight text-cv-text">
              Model card
            </h1>
            <p className="mt-1 text-[12px] text-cv-muted">
              What is trained, what it scored, and what we did not build.
            </p>
          </div>
          <Link
            to="/"
            className="text-[12px] text-cv-muted transition-colors duration-150 hover:text-cv-text"
          >
            ← Command Center
          </Link>
        </header>

        {isLoading ? <p className="text-[12px] text-cv-muted">Loading…</p> : null}

        {data ? (
          <div className="flex flex-col gap-10">
            <Section
              title="Bundle"
              note={`${data.bundleVersion} · generated ${new Date(data.generatedAt).toISOString().slice(0, 16).replace('T', ' ')} UTC`}
            >
              <p className="text-[12px] leading-relaxed text-cv-muted">
                A model may only be reported as trained when it has a recorded training
                time and a held-out metric together with the baseline it is compared
                against. The database enforces this, and so does the inference service:
                an untrained component cannot emit a trained-model provenance tag even if
                it claims one.
              </p>
            </Section>

            <Section title="Datasets">
              {data.datasets.length === 0 ? (
                <Empty>
                  No datasets ingested yet. Phase 1 imports the IBTrACS best track and
                  joins it to HURSAT-B1 satellite frames on storm identifier and
                  observation time.
                </Empty>
              ) : (
                <Table
                  head={['Dataset', 'Source', 'Licence', 'Storms', 'Frames', 'Match rate']}
                  rows={data.datasets.map((d) => [
                    d.name,
                    d.source,
                    d.licence,
                    String(d.stormCount),
                    String(d.frameCount),
                    d.matchRatePct == null ? '—' : `${d.matchRatePct.toFixed(1)}%`,
                  ])}
                />
              )}
            </Section>

            <Section
              title="Split"
              note="Storm-wise, never frame-wise: frames within one storm are highly autocorrelated, so a random split would leak and inflate every metric below."
            >
              <Table
                head={['Strategy', 'Train', 'Validation', 'Test', 'Demo storms held out']}
                rows={[
                  [
                    data.split.strategy,
                    String(data.split.train),
                    String(data.split.val),
                    String(data.split.test),
                    data.split.demoStormsInTest ? 'yes' : 'NO — INVALID',
                  ],
                ]}
              />
            </Section>

            <Section title="Models">
              <Table
                head={['Component', 'Version', 'Provenance', 'Metric', 'Baseline']}
                rows={data.models.map(modelRow)}
              />
            </Section>

            <Section
              title="Multi-source ablation"
              note="Does the satellite imagery actually add information the best track does not already carry? This table is the answer, measured on identical held-out storms."
            >
              <Table
                head={['Feature set', 'MAE (kt)', 'n']}
                rows={data.ablation.map((a) => [
                  a.setting,
                  a.maeKt == null ? 'not measured' : a.maeKt.toFixed(1),
                  a.n == null ? '—' : String(a.n),
                ])}
              />
            </Section>

            <Section
              title="Cone calibration"
              note="Cone radii are percentiles of the track model's own held-out error, not chosen widths. Observed containment is how often the truth actually fell inside."
            >
              <Table
                head={['Lead (h)', 'p67 (km)', 'p90 (km)', 'Observed containment', 'n']}
                rows={data.coneCalibration.map((c) => [
                  String(c.leadHours),
                  c.p67Km == null ? 'not calibrated' : c.p67Km.toFixed(0),
                  c.p90Km == null ? 'not calibrated' : c.p90Km.toFixed(0),
                  c.observedContainmentP67 == null
                    ? '—'
                    : `${Math.round(c.observedContainmentP67 * 100)}%`,
                  c.n == null ? '—' : String(c.n),
                ])}
              />
            </Section>

            <Section title="What we did not build, and why">
              <ul className="flex flex-col gap-3">
                {data.notBuilt.map((item) => (
                  <li key={item.item} className="border-l-2 border-cv-glass-border pl-3">
                    <p className="text-[13px] text-cv-text">{item.item}</p>
                    <p className="mt-0.5 text-[12px] leading-relaxed text-cv-muted">
                      {item.reason}
                    </p>
                  </li>
                ))}
              </ul>
            </Section>
          </div>
        ) : null}
      </div>
    </div>
  )
}

function modelRow(model: ModelRow): string[] {
  return [
    model.key,
    model.version,
    PROVENANCE_LABEL[model.provenance],
    model.metric && model.value != null ? `${model.metric} ${model.value}` : 'not trained',
    model.baseline && model.baselineValue != null
      ? `${model.baseline} ${model.baselineValue}`
      : '—',
  ]
}

function Section({
  title,
  note,
  children,
}: {
  title: string
  note?: string
  children: React.ReactNode
}) {
  return (
    <section>
      <h2 className="text-[10px] uppercase tracking-wider text-cv-faint">{title}</h2>
      {note ? (
        <p className="mt-1 mb-3 max-w-[640px] text-[11px] leading-relaxed text-cv-muted">
          {note}
        </p>
      ) : (
        <div className="mb-3" />
      )}
      {children}
    </section>
  )
}

function Table({ head, rows }: { head: string[]; rows: string[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left">
        <thead>
          <tr>
            {head.map((cell) => (
              <th
                key={cell}
                className="border-b border-cv-glass-border py-2 pr-4 text-[10px] font-normal uppercase tracking-wider text-cv-faint"
              >
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className={`border-b border-cv-glass-border py-2 pr-4 text-[12px] ${
                    cellIndex === 0 ? 'text-cv-text' : 'cv-num text-cv-muted'
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="text-[12px] leading-relaxed text-cv-faint">{children}</p>
}
