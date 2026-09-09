import { Link } from 'react-router-dom'

import type { HealthResponse, StormDetail } from '../../types/api'
import type { Mode } from '../../store/timeline'
import { GlassPanel } from '../ui/GlassPanel'
import { Segmented } from '../ui/Segmented'

/**
 * One slim bar. Storm identity, a mode switch, and a link to the model card.
 *
 * No nav tree, no hamburger, no breadcrumbs. The application has two routes and one
 * primary control; a navigation structure would imply somewhere else to go.
 */
export function HeaderBar({
  storm,
  health,
  mode,
  onModeChange,
}: {
  storm: StormDetail | undefined
  health: HealthResponse | undefined
  mode: Mode
  onModeChange: (mode: Mode) => void
}) {
  return (
    <GlassPanel
      as="header"
      className="pointer-events-auto absolute top-3 right-3 left-3 z-30 flex h-[56px] items-center gap-4 px-4"
    >
      <span className="flex items-baseline gap-2">
        <span className="text-[15px] font-medium tracking-tight text-cv-text">
          ◈ CycloVision
        </span>
      </span>

      {storm ? (
        <span className="flex items-baseline gap-2 text-[12px] text-cv-muted">
          <span className="text-cv-text">{storm.name}</span>
          <span>·</span>
          <span>{basinName(storm.basin)}</span>
          <span>·</span>
          <span className="cv-num">{storm.seasonYear}</span>
        </span>
      ) : null}

      <div className="ml-auto flex items-center gap-3">
        <Segmented<Mode>
          value={mode}
          onChange={onModeChange}
          options={[
            { value: 'explore', label: 'Explore' },
            { value: 'verify', label: 'Verify' },
          ]}
        />

        {health ? (
          <span
            className="text-[10px] uppercase tracking-wider text-cv-faint"
            title={`AI service ${health.aiService.status} · database ${health.database} · bundle ${health.bundleVersion}`}
          >
            {health.status}
          </span>
        ) : null}

        <Link
          to="/model"
          className="rounded px-2 py-1 text-[12px] text-cv-muted transition-colors duration-150 hover:text-cv-text"
          title="Datasets, held-out metrics, and what we did not build"
        >
          ⓘ
        </Link>
      </div>
    </GlassPanel>
  )
}

const BASIN_NAMES: Record<string, string> = {
  NI: 'North Indian Ocean',
  SI: 'South Indian Ocean',
  WP: 'Western Pacific',
  EP: 'Eastern Pacific',
  NA: 'North Atlantic',
  SP: 'South Pacific',
}

function basinName(basin: string): string {
  return BASIN_NAMES[basin] ?? basin
}
