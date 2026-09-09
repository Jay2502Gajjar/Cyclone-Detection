import { useEffect, useMemo, useState } from 'react'

import { AnaloguesDrawer } from '../components/drawers/AnaloguesDrawer'
import { EvidenceDrawer } from '../components/drawers/EvidenceDrawer'
import { StormMap } from '../components/map/StormMap'
import { HeaderBar } from '../components/panels/HeaderBar'
import { IntelligencePanel } from '../components/panels/IntelligencePanel'
import { StormRail } from '../components/panels/StormRail'
import { TimelineScrubber } from '../components/timeline/TimelineScrubber'
import { DemoDataBanner } from '../components/ui/DemoDataBanner'
import { useForecast } from '../hooks/useForecast'
import { useFrame } from '../hooks/useFrame'
import { useStorm } from '../hooks/useStorm'
import { useHealth, useStormList } from '../hooks/useStormList'
import { anyPlaceholder } from '../lib/provenance'
import { useTimeline } from '../store/timeline'

/**
 * The Command Center. Effectively the whole product.
 *
 * The map fills the viewport; the rail, panel and timeline float on top of it. There is
 * one primary control — the scrubber — and everything else responds to it. Detail is
 * behind two drawers rather than on the page, so the first thing a viewer sees is a
 * storm rather than a layout.
 */
export function CommandCenter() {
  const { data: storms, isLoading: stormsLoading } = useStormList()
  const { data: health } = useHealth()

  const {
    selectedSid,
    cursorTime,
    mode,
    verifyFrom,
    revealed,
    selectStorm,
    setCursor,
    setMode,
    setVerifyFrom,
    setRevealed,
  } = useTimeline()

  const { data: storm } = useStorm(selectedSid)
  const { data: frame } = useFrame(selectedSid, cursorTime)
  const forecastMutation = useForecast(selectedSid)

  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [analoguesOpen, setAnaloguesOpen] = useState(false)

  // Open on a storm rather than an empty state: a demo should never begin with a chooser.
  useEffect(() => {
    if (!selectedSid && storms && storms.length > 0) {
      const demo = storms.find((s) => s.isDemo) ?? storms[0]
      selectStorm(demo.sid)
    }
  }, [storms, selectedSid, selectStorm])

  // Park the cursor mid-lifecycle, where a storm is most interesting, rather than at
  // formation where nothing has happened yet.
  useEffect(() => {
    if (storm && storm.frames.length > 0 && !cursorTime) {
      setCursor(storm.frames[Math.floor(storm.frames.length / 2)].t)
    }
  }, [storm, cursorTime, setCursor])

  const cursorIndex = useMemo(() => {
    if (!storm || !cursorTime) return 0
    const index = storm.frames.findIndex((f) => f.t === cursorTime)
    return index >= 0 ? index : 0
  }, [storm, cursorTime])

  const verifyIndex = useMemo(() => {
    if (!storm || !verifyFrom) return null
    const index = storm.frames.findIndex((f) => f.t === verifyFrom)
    return index >= 0 ? index : null
  }, [storm, verifyFrom])

  const currentTrackFrame = storm?.frames[cursorIndex] ?? null
  const forecast = forecastMutation.data ?? null

  const showDemoBanner = anyPlaceholder([
    frame?.structure.metricsSource,
    frame?.structure.regimeSource,
    frame?.vision.source,
    forecast?.intensityForecast.source,
    forecast?.trackForecast.source,
    forecast?.analogues.source,
    forecast?.risk.source,
  ])

  function runForecast(reveal: boolean) {
    if (!currentTrackFrame) return
    setVerifyFrom(currentTrackFrame.t)
    forecastMutation.mutate({ from: currentTrackFrame.t, reveal })
  }

  return (
    <div className="relative h-full w-full overflow-hidden bg-cv-ground">
      <StormMap storm={storm} currentFrame={currentTrackFrame} forecast={forecast} />

      <div className="pointer-events-none absolute inset-0">
        <HeaderBar storm={storm} health={health} mode={mode} onModeChange={setMode} />

        {showDemoBanner ? (
          <div className="pointer-events-auto absolute top-[68px] right-3 left-3 z-30 overflow-hidden rounded-lg">
            <DemoDataBanner bundleVersion={health?.bundleVersion} />
          </div>
        ) : null}

        <StormRail
          storms={storms ?? []}
          selectedSid={selectedSid}
          onSelect={selectStorm}
          loading={stormsLoading}
        />

        <IntelligencePanel
          frame={frame}
          currentTrackFrame={currentTrackFrame}
          forecast={forecast}
          mode={mode}
          onRunForecast={() => runForecast(false)}
          onReveal={() => {
            const next = !revealed
            setRevealed(next)
            if (next && currentTrackFrame) {
              forecastMutation.mutate({ from: verifyFrom ?? currentTrackFrame.t, reveal: true })
            }
          }}
          onOpenEvidence={() => setEvidenceOpen(true)}
          onOpenAnalogues={() => setAnaloguesOpen(true)}
          forecastPending={forecastMutation.isPending}
          revealed={revealed}
        />

        {storm && storm.frames.length > 0 ? (
          <TimelineScrubber
            storm={storm}
            cursorIndex={cursorIndex}
            verifyIndex={verifyIndex}
            onIndexChange={(index) => setCursor(storm.frames[index].t)}
          />
        ) : (
          <EmptyTimeline loading={stormsLoading} hasStorms={(storms?.length ?? 0) > 0} />
        )}
      </div>

      <EvidenceDrawer
        open={evidenceOpen}
        onOpenChange={setEvidenceOpen}
        frame={frame}
        forecast={forecast}
      />
      <AnaloguesDrawer
        open={analoguesOpen}
        onOpenChange={setAnaloguesOpen}
        forecast={forecast}
      />
    </div>
  )
}

function EmptyTimeline({ loading, hasStorms }: { loading: boolean; hasStorms: boolean }) {
  return (
    <div className="cv-glass pointer-events-auto absolute right-3 bottom-3 left-3 z-20 flex h-[92px] items-center justify-center px-4">
      <p className="max-w-[560px] text-center text-[11px] leading-relaxed text-cv-muted">
        {loading
          ? 'Loading storms…'
          : hasStorms
            ? 'This storm has no observations loaded.'
            : 'No storms in the database yet. Phase 1 imports the IBTrACS best track and joins it to HURSAT satellite frames; the timeline appears here once that runs.'}
      </p>
    </div>
  )
}
