import { useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";

import { AppShell } from "@/components/layout/AppShell";
import { StageView } from "@/components/dashboard/StageView";
import { LayersControl } from "@/components/dashboard/LayersControl";
import { ActiveCyclones } from "@/components/dashboard/ActiveCyclones";
import { LeftMetrics } from "@/components/dashboard/MetricCards";
import { useCyclone } from "@/state/cyclone-store";

export const Route = createFileRoute("/map")({
  head: () => ({
    meta: [
      { title: "Live Cyclone Map — VAIYU" },
      { name: "description", content: "Interactive 2D and 3D cyclone map with wind particles, tracks, forecast corridor and risk zones." },
      { property: "og:title", content: "Live Cyclone Map — VAIYU" },
      { property: "og:description", content: "Interactive cyclone map with wind particles, tracks and risk zones." },
    ],
  }),
  component: MapPage,
});

function MapPage() {
  const { setView } = useCyclone();

  useEffect(() => {
    setView("2D");
  }, [setView]);

  return (
    <AppShell>
      <div className="grid gap-3 lg:grid-cols-[300px_minmax(0,1fr)]">
        <div className="space-y-3">
          <ActiveCyclones />
          <LayersControl />
          <LeftMetrics />
        </div>
        <div className="panel relative min-h-[520px] overflow-hidden lg:min-h-[720px]">
          <StageView />
        </div>
      </div>
    </AppShell>
  );
}
