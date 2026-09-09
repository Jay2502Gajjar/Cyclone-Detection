/**
 * The banner that makes a Phase 0 build impossible to mistake for a working system.
 *
 * It appears whenever anything on screen is stamped DEMO_DATA. That is the entire point:
 * the provenance system is only worth having if its consequence is visible without
 * hunting for a chip.
 */
export function DemoDataBanner({ bundleVersion }: { bundleVersion?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 bg-cv-risk-moderate/15 px-4 py-1.5 text-[11px] text-cv-risk-moderate">
      <span className="font-medium uppercase tracking-wider">Demo data</span>
      <span className="text-cv-muted">
        No trained model is loaded
        {bundleVersion ? ` (bundle ${bundleVersion})` : ''} — forecast values are absent
        rather than estimated.
      </span>
    </div>
  )
}
