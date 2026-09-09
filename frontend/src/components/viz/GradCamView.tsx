import { useState } from 'react'

import { mediaUrl } from '../../api/client'
import type { VisionBlock } from '../../types/api'
import { ProvenanceChip } from '../ui/ProvenanceChip'

/**
 * The satellite frame with the model's attention overlaid.
 *
 * Grad-CAM on its own is easy to show and hard to interpret. It earns its place here
 * because it sits next to the structural measurements: when the network attends to the
 * eyewall ring that those measurements independently located, the agreement is a real
 * validation signal rather than a pretty heatmap.
 */
export function GradCamView({
  imageUrl,
  vision,
}: {
  imageUrl: string | null
  vision: VisionBlock
}) {
  const [showOverlay, setShowOverlay] = useState(true)
  const base = mediaUrl(imageUrl)
  const overlay = mediaUrl(vision.gradcamUrl)

  if (!base) {
    return (
      <p className="text-[11px] leading-relaxed text-cv-faint">
        No satellite frame is matched to this observation. Not every best-track point has
        a matching satellite pass, so this gap is expected rather than an error.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="relative overflow-hidden rounded-[10px] border border-cv-glass-border bg-cv-ground-soft">
        <img src={base} alt="Infrared satellite frame" className="w-full" />
        {overlay && showOverlay ? (
          <img
            src={overlay}
            alt="Model attention overlay"
            className="absolute inset-0 h-full w-full opacity-70 mix-blend-screen"
          />
        ) : null}
      </div>

      <div className="flex items-center justify-between">
        <ProvenanceChip source={vision.source} />
        {overlay ? (
          <button
            type="button"
            onClick={() => setShowOverlay((v) => !v)}
            className="rounded border border-cv-glass-border px-2 py-1 text-[11px] text-cv-muted transition-colors duration-150 hover:text-cv-text"
          >
            {showOverlay ? 'Hide attention' : 'Show attention'}
          </button>
        ) : (
          <span className="text-[10px] text-cv-faint">
            No attention map: the vision model is not trained yet
          </span>
        )}
      </div>
    </div>
  )
}
