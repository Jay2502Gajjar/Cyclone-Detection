import { lazy, Suspense } from "react";

import { ClientOnly } from "@/components/ui/client-only";
import { useCyclone } from "@/state/cyclone-store";
import { cn } from "@/lib/utils";

const Globe3D = lazy(() => import("@/components/globe/Globe3D"));
const CycloneMap = lazy(() => import("@/components/map/CycloneMap"));

function StageLoading({ label }: { label: string }) {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <p className="tech-label animate-pulse">{label}</p>
    </div>
  );
}

export function StageView({ className }: { className?: string }) {
  const { cyclone, view, setView } = useCyclone();

  return (
    <div className={cn("relative h-full w-full", className)}>
      <div className="absolute inset-0">
        <ClientOnly fallback={<StageLoading label="Loading cyclone..." />}>
          <Suspense fallback={<StageLoading label={view === "3D" ? "Rendering globe..." : "Loading map..."} />}>
            {view === "3D" ? <Globe3D /> : <CycloneMap />}
          </Suspense>
        </ClientOnly>
      </div>

      {/* Sleek, Non-intrusive Top Left Telemetry Chip */}
      <div className="pointer-events-none absolute left-4 top-4 z-10 flex items-center gap-2 rounded-lg border border-border/80 bg-card/85 px-3 py-1.5 shadow-md backdrop-blur-md">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
        </span>
        <span className="font-display text-[11px] font-bold uppercase tracking-wider text-foreground">
          {cyclone.name}
        </span>
        <span className="text-[10px] text-muted-foreground/60">|</span>
        <span className="font-mono text-[10px] text-muted-foreground uppercase">
          {cyclone.basin || "NORTH INDIAN"}
        </span>
        <span className="text-[10px] text-muted-foreground/60">|</span>
        <span className="font-display text-[10px] font-medium text-primary">
          {cyclone.category}
        </span>
        {cyclone.windKph > 0 ? (
          <>
            <span className="text-[10px] text-muted-foreground/60">|</span>
            <span className="font-mono text-[10px] font-semibold text-foreground">
              {cyclone.windKph} km/h
            </span>
          </>
        ) : null}
      </div>

      {/* View Switcher Controls (3D Globe / 2D Map) */}
      <div className="absolute bottom-4 left-1/2 z-10 flex -translate-x-1/2 items-center gap-1 rounded-full border border-border bg-card/90 p-1 shadow-md backdrop-blur-md">
        {(["3D", "2D"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={cn(
              "rounded-full px-4 py-1.5 font-display text-[10px] uppercase tracking-[0.16em] transition-colors",
              view === v ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {v === "3D" ? "3D Globe" : "2D Map"}
          </button>
        ))}
      </div>
    </div>
  );
}
