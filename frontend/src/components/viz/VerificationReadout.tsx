import { km, knots } from '../../lib/format'
import type { VerificationBlock } from '../../types/api'
import { ProvenanceChip } from '../ui/ProvenanceChip'

/**
 * The measured result of a hindcast: the moment a prediction becomes a checkable number.
 *
 * Everything here is OBSERVED. The errors are computed by the backend from the
 * best-track record, never by the inference service, which is the structural guarantee
 * that the forecast could not have seen what it is being scored against.
 */
export function VerificationReadout({
  verification,
}: {
  verification: VerificationBlock
}) {
  if (!verification.available) {
    return (
      <p className="text-[11px] leading-relaxed text-cv-faint">
        No ground truth is available past this point: the storm record ends before the
        forecast horizon, so there is nothing to verify against.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2 rounded-[10px] border border-cv-glass-border bg-cv-glass p-3">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider text-cv-faint">
          Measured against what happened
        </span>
        <ProvenanceChip source={verification.source} />
      </div>

      <dl className="flex flex-col gap-1.5">
        <Row label="Track error at 24 h" value={km(verification.trackErrorKm24h)} />
        <Row label="Track error at 48 h" value={km(verification.trackErrorKm48h)} />
        <Row
          label="Intensity error at 24 h"
          value={knots(verification.intensityErrorKt24h)}
        />
        <Row
          label="Inside the 67% cone"
          value={boolText(verification.insideConeP67)}
        />
        <Row
          label="Rapid intensification"
          value={riText(verification.riOccurred, verification.riWarningIssued)}
        />
      </dl>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-[11px] text-cv-muted">{label}</dt>
      <dd className="cv-num text-[12px] text-cv-truth">{value}</dd>
    </div>
  )
}

function boolText(value: boolean | null): string {
  if (value == null) return 'not calibrated'
  return value ? 'yes' : 'no'
}

/** Reports the warning and the outcome together — a hit and a false alarm read differently. */
function riText(occurred: boolean | null, warned: boolean | null): string {
  if (occurred == null && warned == null) return '—'
  const outcome = occurred == null ? 'unknown' : occurred ? 'occurred' : 'did not occur'
  const warning = warned == null ? '' : warned ? ', warned' : ', not warned'
  return `${outcome}${warning}`
}
