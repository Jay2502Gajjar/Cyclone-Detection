import { useState, useMemo } from "react";
import { Search, X, ChevronDown, ChevronUp, Radio } from "lucide-react";

import { Panel, PanelTitle } from "@/components/ui/primitives";
import { useCyclone } from "@/state/cyclone-store";
import { cn } from "@/lib/utils";

export function ActiveCyclones() {
  const { cyclones, selectedId, selectCyclone, loading } = useCyclone();
  const [searchQuery, setSearchQuery] = useState("");
  const [isOpen, setIsOpen] = useState(true);

  // Filter cyclones dynamically by name, basin, category, or wind speed
  const filteredCyclones = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return cyclones;
    return cyclones.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.basin && c.basin.toLowerCase().includes(q)) ||
        (c.category && c.category.toLowerCase().includes(q)) ||
        (c.risk?.level && c.risk.level.toLowerCase().includes(q)) ||
        String(c.windKph).includes(q),
    );
  }, [cyclones, searchQuery]);

  return (
    <Panel className="space-y-2.5">
      {/* Header with Title, Count Badge & Dropdown Accordion Toggle */}
      <div className="flex items-center justify-between">
        <PanelTitle
          title="Active Cyclones"
          sub={`· ${String(cyclones.length).padStart(2, "0")}`}
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
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search active cyclones..."
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

          {/* Cyclones Dropdown List (Configured to show 5 items cleanly at a time with smooth scrolling) */}
          {loading && cyclones.length === 0 ? (
            <div className="py-6 text-center">
              <p className="tech-label animate-pulse text-[10px]">Scanning meteorological data...</p>
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
              style={{ maxHeight: "295px" }} // Exactly sized to display 5 items at a time
            >
              {filteredCyclones.map((c) => {
                const isSelected = selectedId === c.id;
                const riskLevel = c.risk?.level ?? "MONITORING";

                return (
                  <button
                    key={c.id}
                    onClick={() => selectCyclone(c.id)}
                    className={cn(
                      "w-full rounded-lg border px-2.5 py-2 text-left transition-all",
                      isSelected
                        ? "border-primary bg-primary/10 shadow-sm"
                        : "border-border/70 bg-card/60 hover:border-border hover:bg-secondary/70",
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={cn(
                            "h-2 w-2 rounded-full",
                            isSelected
                              ? "bg-primary animate-pulse"
                              : riskLevel === "HIGH"
                                ? "bg-red-500"
                                : riskLevel === "MODERATE"
                                  ? "bg-amber-500"
                                  : "bg-emerald-500",
                          )}
                        />
                        <span
                          className={cn(
                            "font-display text-[11px] font-semibold tracking-wider",
                            isSelected ? "text-primary" : "text-foreground",
                          )}
                        >
                          {c.name}
                        </span>
                      </div>

                      <span
                        className={cn(
                          "rounded px-1.5 py-0.5 font-display text-[9px] font-medium uppercase tracking-wider",
                          riskLevel === "HIGH"
                            ? "bg-red-500/15 text-red-400 border border-red-500/30"
                            : riskLevel === "MODERATE"
                              ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                              : "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
                        )}
                      >
                        {riskLevel}
                      </span>
                    </div>

                    <div className="mt-1 flex items-center justify-between text-[10px] text-muted-foreground">
                      <span className="font-mono">{c.basin || "North Indian"}</span>
                      <span className="font-mono text-foreground/90">
                        {c.windKph > 0 ? `${c.windKph} km/h` : "Monitoring"}
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
              <span>Showing {filteredCyclones.length} of {cyclones.length} tracked</span>
              <span className="flex items-center gap-1">
                <Radio className="h-2.5 w-2.5 text-primary" /> Live Feeds
              </span>
            </div>
          )}
        </>
      )}
    </Panel>
  );
}
