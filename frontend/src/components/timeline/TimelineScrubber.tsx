import * as Slider from '@radix-ui/react-slider'
import { useCallback, useEffect, useRef, useState } from 'react'

import { formatDay, formatUtc } from '../../lib/format'
import type { StormDetail } from '../../types/api'
import { GlassPanel } from '../ui/GlassPanel'
import { IntensitySparkline } from './IntensitySparkline'

/**
 * The signature control. Dragging it moves everything else in the application.
 *
 * Two properties matter and both are structural rather than cosmetic:
 *
 *   1. It reads an array already in memory. The storm-detail call returns every frame, so
 *      a drag issues no network request and triggers no inference (invariant I5). That is
 *      what makes it feel like an instrument rather than a web page.
 *   2. The scrub is 1:1 with the pointer and unanimated. Easing a value the user is
 *      directly manipulating makes it feel laggy, so the only "motion" here is the
 *      cursor following the finger exactly.
 */
export function TimelineScrubber({
  storm,
  cursorIndex,
  verifyIndex,
  onIndexChange,
}: {
  storm: StormDetail
  cursorIndex: number
  verifyIndex: number | null
  onIndexChange: (index: number) => void
}) {
  const [playing, setPlaying] = useState(false)
  const timerRef = useRef<number | null>(null)
  const frames = storm.frames
  const lastIndex = Math.max(0, frames.length - 1)
  const current = frames[cursorIndex]

  const step = useCallback(
    (delta: number) => {
      onIndexChange(Math.min(lastIndex, Math.max(0, cursorIndex + delta)))
    },
    [cursorIndex, lastIndex, onIndexChange],
  )

  // Playback. Stops at the end rather than looping: a storm has a beginning and an end,
  // and looping past dissipation would misrepresent the record.
  useEffect(() => {
    if (!playing) return
    timerRef.current = window.setInterval(() => {
      onIndexChange(cursorIndex >= lastIndex ? lastIndex : cursorIndex + 1)
      if (cursorIndex >= lastIndex) setPlaying(false)
    }, 220)
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current)
    }
  }, [playing, cursorIndex, lastIndex, onIndexChange])

  // Arrow keys step frame by frame — the precision a scrub cannot give.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      if (target && ['INPUT', 'TEXTAREA'].includes(target.tagName)) return
      if (event.key === 'ArrowLeft') step(-1)
      if (event.key === 'ArrowRight') step(1)
      if (event.key === ' ') {
        event.preventDefault()
        setPlaying((p) => !p)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [step])

  return (
    <GlassPanel
      as="footer"
      className="pointer-events-auto absolute right-3 bottom-3 left-3 z-20 px-4 py-3"
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <ScrubButton label="First frame" onClick={() => onIndexChange(0)}>
            ⏮
          </ScrubButton>
          <ScrubButton
            label={playing ? 'Pause' : 'Play'}
            onClick={() => setPlaying((p) => !p)}
          >
            {playing ? '⏸' : '⏵'}
          </ScrubButton>
          <ScrubButton label="Last frame" onClick={() => onIndexChange(lastIndex)}>
            ⏭
          </ScrubButton>
        </div>

        <span className="w-[68px] shrink-0 text-[11px] text-cv-muted">
          {formatDay(frames[0]?.t)}
        </span>

        <div className="relative flex-1">
          <IntensitySparkline
            frames={frames}
            cursorIndex={cursorIndex}
            verifyIndex={verifyIndex}
          />
          <Slider.Root
            className="relative flex h-5 w-full touch-none items-center select-none"
            min={0}
            max={lastIndex}
            step={1}
            value={[cursorIndex]}
            onValueChange={([value]) => onIndexChange(value)}
            aria-label="Storm timeline"
          >
            <Slider.Track className="relative h-[2px] w-full rounded-full bg-cv-glass-strong">
              <Slider.Range className="absolute h-full rounded-full bg-cv-glass-border" />
            </Slider.Track>
            <Slider.Thumb className="block h-3 w-3 rounded-full border-2 border-cv-ground bg-cv-truth focus:outline-none focus-visible:ring-2 focus-visible:ring-cv-accent" />
          </Slider.Root>
        </div>

        <span className="w-[68px] shrink-0 text-right text-[11px] text-cv-muted">
          {formatDay(frames[lastIndex]?.t)}
        </span>

        <div className="w-[150px] shrink-0 text-right">
          <div className="cv-num text-[13px] text-cv-truth">{formatUtc(current?.t)}</div>
          <div className="text-[10px] text-cv-faint">
            frame {cursorIndex + 1} of {frames.length}
          </div>
        </div>
      </div>

      <div className="mt-1.5 flex items-center gap-4 pl-[132px] text-[10px] text-cv-faint">
        <LegendSwatch className="bg-cv-truth">Observed intensity</LegendSwatch>
        <LegendSwatch className="bg-cv-accent" dashed>
          Model estimate from imagery
        </LegendSwatch>
        <span className="ml-auto">← → step · space play</span>
      </div>
    </GlassPanel>
  )
}

function ScrubButton({
  children,
  label,
  onClick,
}: {
  children: React.ReactNode
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="rounded px-1.5 py-0.5 text-[13px] text-cv-muted transition-colors duration-150 hover:text-cv-text"
    >
      {children}
    </button>
  )
}

function LegendSwatch({
  children,
  className,
  dashed,
}: {
  children: React.ReactNode
  className: string
  dashed?: boolean
}) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className={`inline-block h-[2px] w-4 ${className}`}
        style={dashed ? { maskImage: 'repeating-linear-gradient(90deg,#000 0 3px,transparent 3px 5px)' } : undefined}
      />
      {children}
    </span>
  )
}
