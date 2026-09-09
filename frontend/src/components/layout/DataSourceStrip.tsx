import { useQuery } from "@tanstack/react-query";

import { hasBackend } from "@/api/client";
import { fetchIngestionStatus } from "@/api/ingestionApi";
import { useCyclone } from "@/state/cyclone-store";

export function DataSourceStrip() {
  const { cyclone } = useCyclone();

  const { data: ingestStatus } = useQuery({
    queryKey: ["ingest", "status"],
    queryFn: fetchIngestionStatus,
    staleTime: 60_000,
    retry: 1,
  });

  const ingestLabel = ingestStatus
    ? ingestStatus.running
      ? `${ingestStatus.provider || "IBTrACS"} (Syncing)`
      : `${ingestStatus.provider || "IBTrACS"} (${ingestStatus.lastRunSuccess ? "Idle · Healthy" : "Idle"})`
    : hasBackend
    ? "IBTrACS (Connected)"
    : "Offline";

  const items = [
    { l: "Data Source", v: hasBackend ? "Spring Boot REST API" : "Offline" },
    { l: "Ingestion Status", v: ingestLabel },
    { l: "Basin", v: cyclone.basin || "NI" },
    { l: "Category", v: cyclone.category || "Unclassified" },
    { l: "Status", v: cyclone.status ? cyclone.status.toUpperCase() : "HISTORICAL" },
    { l: "Telemetry", v: cyclone.track.length > 0 ? `${cyclone.track.length} obs points` : "None" },
  ];

  return (
    <div className="panel flex flex-wrap items-center gap-x-6 gap-y-2 px-5 py-2.5">
      {items.map((i) => (
        <span key={i.l} className="flex items-center gap-2">
          <span className="tech-label">{i.l}</span>
          <span className="font-display text-[11px]">{i.v}</span>
        </span>
      ))}
    </div>
  );
}
