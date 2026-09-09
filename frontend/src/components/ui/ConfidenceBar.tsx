import clsx from 'clsx'

/**
 * Confidence as four segments rather than a number.
 *
 * A percentage invites false precision from a model whose calibration we have not yet
 * measured. Four filled-or-not segments say "roughly this confident" and nothing more,
 * which is all we can honestly claim.
 */
export function ConfidenceBar({
  confidence,
  label = 'Confidence',
}: {
  confidence: number | null | undefined
  label?: string
}) {
  const filled = confidence == null ? 0 : Math.ceil(confidence * 4)

  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] uppercase tracking-wider text-cv-faint">{label}</span>
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4].map((segment) => (
          <span
            key={segment}
            className={clsx(
              'h-1 w-6 rounded-full',
              segment <= filled ? 'bg-cv-accent' : 'bg-cv-glass-strong',
            )}
          />
        ))}
        {confidence == null ? (
          <span className="ml-1 text-[11px] text-cv-faint">not available</span>
        ) : null}
      </div>
    </div>
  )
}
