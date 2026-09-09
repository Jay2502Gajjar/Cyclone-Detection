import type { ShapFactor } from '../../types/api'

/**
 * Which features moved the intensity-change prediction, and in which direction.
 *
 * Signed bars from a centre line rather than a ranked list: the sign is the interesting
 * part, and a list of magnitudes hides it.
 */
export function ShapBars({ factors }: { factors: ShapFactor[] }) {
  if (factors.length === 0) {
    return (
      <p className="text-[11px] leading-relaxed text-cv-faint">
        No feature attributions available. The intensity-change model is not trained yet,
        so there is nothing to attribute.
      </p>
    )
  }

  const max = Math.max(...factors.map((f) => Math.abs(f.shap)), 0.001)

  return (
    <ul className="flex flex-col gap-2">
      {factors.map((factor) => {
        const width = (Math.abs(factor.shap) / max) * 50
        const increases = factor.direction === 'increases'
        return (
          <li key={factor.feature} className="flex flex-col gap-1">
            <div className="flex items-baseline justify-between">
              <span className="text-[12px] text-cv-text">{factor.feature}</span>
              <span className="cv-num text-[11px] text-cv-muted">
                {factor.shap > 0 ? '+' : ''}
                {factor.shap.toFixed(2)}
              </span>
            </div>
            <div className="relative h-1.5 rounded-full bg-cv-glass-strong">
              <span className="absolute top-0 bottom-0 left-1/2 w-px bg-cv-glass-border" />
              <span
                className={`absolute top-0 bottom-0 rounded-full ${
                  increases ? 'bg-cv-accent' : 'bg-cv-int-1'
                }`}
                style={
                  increases
                    ? { left: '50%', width: `${width}%` }
                    : { right: '50%', width: `${width}%` }
                }
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}
