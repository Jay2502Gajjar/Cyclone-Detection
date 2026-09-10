import { useState, useMemo } from "react";
import { Search, X, ChevronDown, ChevronUp, Radio, Archive } from "lucide-react";

import { Panel, PanelTitle } from "@/components/ui/primitives";
import { useCyclone } from "@/state/cyclone-store";
import { cn } from "@/lib/utils";

export function ActiveCyclones() {
  const { cyclones, activeCyclones, activeCount, selectedId, selectCyclone, loading } = useCyclone();
  const [searchQuery, setSearchQuery] = useState("");
  const [isOpen, setIsOpen] = useState(true);
  const [tab, setTab] = useState<"active" | "all">(activeCount > 0 ? "active" : "all");

  // Determine the candidate list based on active tab
  const candidateList = useMemo(() => {
    if (tab === "active") {
      const activeIds = new Set(activeCyclones.map((a) => a.id));
      return cyclones.filter((c) => activeIds.has(c.id) || c.status?.toLowerCase() === "active");
    }
    return cyclones;
  }, [tab, activeCyclones, cyclones]);

  // Filter cyclones dynamically by name, basin, category, or externalId
  const filteredCyclones = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return candidateList;
    return candidateList.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.basin && c.basin.toLowerCase().includes(q)) ||
        (c.category && c.category.toLowerCase().includes(q)) ||
        (c.externalId && c.externalId.toLowerCase().includes(q)) ||
        (c.status && c.status.toLowerCase().includes(q)) ||
        String(c.windKph).includes(q),
    );
  }, [candidateList, searchQuery]);

  return (
    <Panel className="space-y-2.5">
      {/* Header with Title, Count Badge & Dropdown Accordion Toggle */}
      <div className="flex items-center justify-between">
        <PanelTitle
          title={tab === "active" ? "Active Cyclones" : "Cyclone Catalog"}
          sub={`· ${String(candidateList.length).padStart(2, "0")}`}
        />
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex h-6 w-6 items-center justify-center rounded-md border border-border/80 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          title={isOpen ? "Collapse list" : "Expand list"}
          aria-label={isOpen ? "Collapse list" : "Expand list"}
        >
          {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>
      </div>

      {isOpen && (
        <>
          {/* Active vs Historical Tab Switcher */}
          <div className="flex gap-1 rounded-lg border border-border/70 bg-secondary/40 p-0.5">
            <button
              onClick={() => setTab("active")}
              className={cn(
                "flex-1 rounded-md py-1 text-center font-display text-[10px] font-semibold tracking-wider transition-all",
                tab === "active"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => setTab("all")}
              className={cn(
                "flex-1 rounded-md py-1 text-center font-display text-[10px] font-semibold tracking-wider transition-all",
                tab === "all"
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Historical ({cyclones.length})
            </button>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={tab === "active" ? "Search active storms..." : "Search 1,858 IBTrACS storms..."}
              className="w-full rounded-md border border-border/80 bg-background/60 py-1.5 pl-8 pr-7 font-mono text-[11px] text-foreground placeholder:text-muted-foreground/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/40"
            />
            {searchQuery ? (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
                title="Clear search"
              >
                <X className="h-3 w-3" />
              </button>
            ) : null}
          </div>

          {/* Cyclones Dropdown List */}
          {loading && cyclones.length === 0 ? (
            <div className="py-6 text-center">
              <p className="tech-label animate-pulse text-[10px]">Scanning meteorological data...</p>
            </div>
          ) : tab === "active" && candidateList.length === 0 ? (
            <div className="rounded-lg border border-border/60 bg-secondary/20 p-4 text-center">
              <div className="mx-auto mb-2 flex h-7 w-7 items-center justify-center rounded-full bg-secondary text-muted-foreground">
                <Radio className="h-3.5 w-3.5" />
              </div>
              <p className="font-display text-[11px] font-semibold tracking-wide text-foreground">
                No Active Cyclones
              </p>
              <p className="tech-label mt-1 text-[10px] text-muted-foreground">
                IBTrACS telemetry indicates 0 active tropical systems currently in monitored basins.
              </p>
              <button
                onClick={() => setTab("all")}
                className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-primary/30 bg-primary/10 px-3 py-1 font-display text-[10px] font-semibold text-primary transition-colors hover:bg-primary/20"
              >
                <Archive className="h-3 w-3" />
                Browse Historical Catalog ({cyclones.length})
              </button>
            </div>
          ) : filteredCyclones.length === 0 ? (
            <div className="py-4 text-center">
              <p className="text-[11px] text-muted-foreground">No cyclones match "{searchQuery}"</p>
              <button
                onClick={() => setSearchQuery("")}
                className="mt-1.5 text-[10px] font-medium text-primary underline hover:text-primary/80"
              >
                Reset search filter
              </button>
            </div>
          ) : (
            <div
              className="space-y-1.5 overflow-y-auto pr-1"
              style={{ maxHeight: "295px" }}
            >
              {filteredCyclones.map((c) => {
                const isSelected = selectedId === c.id;
                const isActive = c.status?.toLowerCase() === "active";

                return (
                  <button
                    key={c.id}
                    onClick={() => selectCyclone(c.id)}
                    className={cn(
                      "w-full rounded-lg border px-2.5 py-2 text-left transition-all",
                      isSelected
                        ? "border-primary bg-primary/10 shadow-xs"
                        : "border-border/70 bg-card/60 hover:border-border hover:bg-secondary/70",
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 truncate">
                        <span
                          className={cn(
                            "h-2 w-2 shrink-0 rounded-full",
                            isActive
                              ? "bg-primary animate-pulse"
                              : "bg-muted-foreground/60",
                          )}
                        />
                        <span
                          className={cn(
                            "truncate font-display text-[11px] font-semibold tracking-wider",
                            isSelected ? "text-primary" : "text-foreground",
                          )}
                        >
                          {c.name}
                        </span>
                      </div>

                      <span
                        className={cn(
                          "shrink-0 rounded px-1.5 py-0.5 font-display text-[9px] font-medium uppercase tracking-wider",
                          isActive
                            ? "border border-emerald-500/30 bg-emerald-500/15 text-emerald-400"
                            : "border border-border bg-secondary/80 text-muted-foreground",
                        )}
                      >
                        {isActive ? "ACTIVE" : "HISTORICAL"}
                      </span>
                    </div>

                    <div className="mt-1 flex items-center justify-between text-[10px] text-muted-foreground">
                      <span className="font-mono">{c.basin || "NI"} · {c.category || "Unclassified"}</span>
                      <span className="font-mono text-foreground/90">
                        {c.windKph > 0 ? `${c.windKph} km/h` : "—"}
                        {c.pressureHpa > 0 ? ` · ${c.pressureHpa} hPa` : ""}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}

          {/* Quick Filter Info Footer */}
          {filteredCyclones.length > 0 && (
            <div className="flex items-center justify-between pt-1 text-[9px] text-muted-foreground/70">
              <span>Showing {filteredCyclones.length} of {candidateList.length}</span>
              <span className="flex items-center gap-1">
                {tab === "active" ? (
                  <>
                    <Radio className="h-2.5 w-2.5 text-primary" /> Live IBTrACS
                  </>
                ) : (
                  <>
                    <Archive className="h-2.5 w-2.5 text-muted-foreground" /> IBTrACS Archive
                  </>
                )}
              </span>
            </div>
          )}
        </>
      )}
    </Panel>
  );
}
