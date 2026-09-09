import type { ForecastResponse, FrameAnalysis } from '../../types/api'
import { Drawer } from '../ui/Drawer'
import { GradCamView } from '../viz/GradCamView'
import { ShapBars } from '../viz/ShapBars'
import { StructureMetrics } from '../viz/StructureMetrics'

/**
 * "Why?" — the evidence behind the numbers on the panel.
 *
 * Grouped so the argument builds: the image and what the model looked at, the
 * measurements taken from the same image, then the attributions for the forecast those
 * measurements feed. The map stays visible behind the blur, so this reads as looking
 * closer rather than navigating away.
 */
export function EvidenceDrawer({
  open,
  onOpenChange,
  frame,
  forecast,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  frame: FrameAnalysis | undefined
  forecast: ForecastResponse | null
}) {
  return (
    <Drawer
      open={open}
      onOpenChange={onOpenChange}
      title="Evidence"
      subtitle="What the satellite frame shows, and what the models made of it"
    >
      {!frame ? (
        <p className="text-[11px] text-cv-faint">Select a moment on the timeline.</p>
      ) : (
        <div className="flex flex-col gap-6">
          <section>
            <h3 className="mb-2 text-[10px] uppercase tracking-wider text-cv-faint">
              Satellite frame
            </h3>
            <GradCamView imageUrl={frame.imageUrl} vision={frame.vision} />
          </section>

          <section>
            <StructureMetrics structure={frame.structure} />
          </section>

          <section>
            <h3 className="mb-2 text-[10px] uppercase tracking-wider text-cv-faint">
              What drove the intensity forecast
            </h3>
            <ShapBars factors={forecast?.intensityForecast.topFactors ?? []} />
          </section>

          <section className="border-t border-cv-glass-border pt-4">
            <h3 className="mb-2 text-[10px] uppercase tracking-wider text-cv-faint">
              Provenance
            </h3>
            <p className="text-[11px] leading-relaxed text-cv-muted">
              Every figure in CycloVision is tagged with what produced it. Measurements
              are computed deterministically from the raw brightness-temperature field;
              regime labels come from a rule engine whose thresholds are listed above;
              forecasts come from trained models with published held-out metrics. Anything
              tagged <span className="text-cv-risk-moderate">Placeholder</span> was not
              produced by a trained model, and is shown as absent rather than estimated.
            </p>
          </section>
        </div>
      )}
    </Drawer>
  )
}
