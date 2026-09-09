import { kelvin, km, ratio } from '../../lib/format'
import type { StructureBlock } from '../../types/api'
import { ProvenanceChip } from '../ui/ProvenanceChip'

/**
 * The seven structural measurements, with the rules that produced the regime label.
 *
 * Showing the thresholds is the point. A label a viewer can check is worth more than a
 * confident one they have to trust, and these are measurements rather than predictions —
 * which is why they carry a different provenance tag from the label sitting on top of
 * them.
 */
export function StructureMetrics({ structure }: { structure: StructureBlock }) {
  const rows: { label: string; value: string; note?: string }[] = [
    {
      label: 'Eye detected',
      value: structure.eyePresent == null ? '—' : structure.eyePresent ? 'yes' : 'no',
      note: 'warm core enclosed by a cold ring on at least 70% of azimuths',
    },
    { label: 'Eye radius', value: km(structure.eyeRadiusKm) },
    {
      label: 'Eye / eyewall contrast',
      value: kelvin(structure.eyeRingBtContrastK),
      note: 'the physical basis of the Dvorak eye adjustment',
    },
    {
      label: 'Coldest cloud top',
      value: kelvin(structure.minBtK),
      note: 'proxy for convective vigour',
    },
    {
      label: 'CDO fraction (100 km)',
      value: ratio(structure.cdoFraction100km),
      note: 'share of the core colder than the deep-convection threshold',
    },
    {
      label: 'Axisymmetry',
      value: ratio(structure.axisymmetry),
      note: '1 - wavenumber-1 / wavenumber-0 of the perturbation field, 50-200 km',
    },
    { label: 'Convective ring radius', value: km(structure.convectiveRingRadiusKm) },
    {
      label: 'Cold-cloud offset',
      value: km(structure.coldCloudOffsetKm),
      note: 'displacement of deep convection from the centre, a shear signature',
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <h4 className="text-[10px] uppercase tracking-wider text-cv-faint">
            Structural measurements
          </h4>
          <ProvenanceChip source={structure.metricsSource} />
        </div>

        <dl className="flex flex-col">
          {rows.map((row) => (
            <div
              key={row.label}
              className="flex items-start justify-between gap-4 border-b border-cv-glass-border py-1.5 last:border-0"
            >
              <dt className="flex flex-col">
                <span className="text-[12px] text-cv-text">{row.label}</span>
                {row.note ? (
                  <span className="text-[10px] text-cv-faint">{row.note}</span>
                ) : null}
              </dt>
              <dd className="cv-num shrink-0 text-[13px] text-cv-truth">{row.value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div>
        <div className="mb-2 flex items-center gap-2">
          <h4 className="text-[10px] uppercase tracking-wider text-cv-faint">
            Regime {structure.regime ? `· ${structure.regime}` : ''}
          </h4>
          <ProvenanceChip source={structure.regimeSource} />
        </div>

        {structure.rulesApplied.length > 0 ? (
          <ul className="flex flex-col gap-1">
            {structure.rulesApplied.map((rule) => (
              <li key={rule} className="cv-num text-[11px] text-cv-muted">
                {rule}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[11px] leading-relaxed text-cv-faint">
            No regime was assigned. Either no satellite frame is matched to this
            observation, or the rule thresholds are not yet calibrated.
          </p>
        )}
      </div>
    </div>
  )
}
