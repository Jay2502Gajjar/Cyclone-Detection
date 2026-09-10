import { AlertCircle, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

import { TopNav } from "@/components/layout/TopNav";
import { Modals } from "@/components/dashboard/Modals";
import { DataSourceStrip } from "@/components/layout/DataSourceStrip";
import { useCyclone } from "@/state/cyclone-store";

export function AppShell({ children }: { children: ReactNode }) {
  const { error, refetch } = useCyclone();

  return (
    <div className="min-h-screen bg-background px-3 py-3 md:px-5 md:py-4">
      <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-3">
        <TopNav />

        {error ? (
          <div className="flex items-center justify-between gap-3 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-2.5 text-[12px] text-destructive">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={refetch}
              className="flex items-center gap-1 font-mono text-[11px] font-medium text-foreground underline hover:text-primary"
            >
              <RefreshCw className="h-3 w-3" /> Retry Connection
            </button>
          </div>
        ) : null}

        <main className="flex-1">{children}</main>
        <DataSourceStrip />
      </div>
      <Modals />
    </div>
  );
}
