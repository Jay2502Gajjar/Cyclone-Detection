import type { TrackFrame } from '../../types/api'

/**
 * Observed intensity against the CNN's per-frame estimate, across the storm's whole life.
 *
 * This is the application's strongest single piece of evidence, and it is visible before
 * anyone clicks anything: a solid line of what was observed, a dashed line of what the
 * model estimated from imagery alone, tracking each other for days. When the model is
 * trained, two lines agreeing over a nine-day lifecycle says more than any accuracy
 * figure.
 *
 * Hand-drawn SVG rather than a charting library. It has to redraw under a 60fps drag and
 * sit inside a 132px bar, so a general-purpose chart component would be both slower and
 * harder to make this small.
 */

const HEIGHT = 46
const PAD_TOP = 4
const PAD_BOTTOM = 4

export function IntensitySparkline({
  frames,
  cursorIndex,
  verifyIndex,
}: {
  frames: TrackFrame[]
  cursorIndex: number
  verifyIndex: number | null
}) {
  if (frames.length < 2) {
    return (
      <div className="flex h-[46px] items-center text-[11px] text-cv-faint">
        No observations to plot.
      </div>
    )
  }

  const values = frames
    .flatMap((f) => [f.vmaxKt, f.cnnVmaxKt])
    .filter((v): v is number => v != null)

  const min = values.length ? Math.min(...values) : 0
  const max = values.length ? Math.max(...values) : 1
  const span = Math.max(1, max - min)

  const x = (index: number) => (index / (frames.length - 1)) * 100
  const y = (value: number) =>
    PAD_TOP + (1 - (value - min) / span) * (HEIGHT - PAD_TOP - PAD_BOTTOM)

  const observed = buildPath(frames, (f) => f.vmaxKt, x, y)
  const estimated = buildPath(frames, (f) => f.cnnVmaxKt, x, y)

  return (
    <svg
      viewBox={`0 0 100 ${HEIGHT}`}
      preserveAspectRatio="none"
      className="h-[46px] w-full"
      role="img"
      aria-label="Observed intensity against the model's per-frame estimate"
    >
      {observed ? (
        <path
          d={observed}
          fill="none"
          stroke="var(--color-cv-truth)"
          strokeWidth={0.6}
          vectorEffect="non-scaling-stroke"
        />
      ) : null}

      {estimated ? (
        <path
          d={estimated}
          fill="none"
          stroke="var(--color-cv-accent)"
          strokeWidth={0.6}
          strokeDasharray="3 2"
          vectorEffect="non-scaling-stroke"
        />
      ) : null}

      {verifyIndex != null ? (
        <line
          x1={x(verifyIndex)}
          x2={x(verifyIndex)}
          y1={0}
          y2={HEIGHT}
          stroke="var(--color-cv-accent)"
          strokeWidth={0.5}
          strokeDasharray="2 2"
          vectorEffect="non-scaling-stroke"
        />
      ) : null}

      <line
        x1={x(cursorIndex)}
        x2={x(cursorIndex)}
        y1={0}
        y2={HEIGHT}
        stroke="var(--color-cv-truth)"
        strokeWidth={0.7}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

/**
 * Builds a path that breaks across gaps.
 *
 * Frames without a value are common — not every best-track point has matched imagery, so
 * the estimate line is genuinely absent there. Interpolating across the gap would draw a
 * model output where none exists.
 */
function buildPath(
  frames: TrackFrame[],
  pick: (frame: TrackFrame) => number | null,
  x: (index: number) => number,
  y: (value: number) => number,
): string | null {
  let path = ''
  let penDown = false

  frames.forEach((frame, index) => {
    const value = pick(frame)
    if (value == null) {
      penDown = false
      return
    }
    path += `${penDown ? 'L' : 'M'}${x(index).toFixed(2)} ${y(value).toFixed(2)} `
    penDown = true
  })

  return path.trim() || null
}
