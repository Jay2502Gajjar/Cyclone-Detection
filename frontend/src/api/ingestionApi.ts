import { getJson } from "./client";

export interface BackendIngestionStatus {
  running: boolean;
  provider: string | null;
  currentRunStartTime: string | null;
  lastRunStartTime: string | null;
  lastRunEndTime: string | null;
  lastRunDurationMs: number | null;
  lastRunSuccess: boolean | null;
  lastRunFailures: number | null;
  lastRunSkippedRecords: number | null;
  lastRunMessage: string | null;
}

/**
 * Fetches internal ingestion status from the backend.
 */
export async function fetchIngestionStatus(): Promise<BackendIngestionStatus> {
  return getJson<BackendIngestionStatus>("/api/internal/ingest/status");
}
