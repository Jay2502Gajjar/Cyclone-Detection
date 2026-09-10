import { useState, useMemo } from "react";
import { Search, X, ChevronDown, ChevronUp, Trophy, Check, Database, Zap, Flame, ShieldAlert, RotateCcw } from "lucide-react";

import { Panel } from "@/components/ui/primitives";
import { useCyclone } from "@/state/cyclone-store";
import { cn } from "@/lib/utils";
import type { Cyclone } from "@/types/cyclone";

type ClassificationTab = "named" | "unnamed";
type IntensityFilter = "all" | "max" | "severe" | "moderate";

function isNamedCyclone(c: Cyclone): boolean {
  if (typeof c.isNamed === "boolean") return c.isNamed;
  const n = c.name.toUpperCase().trim();
  if (
    n.startsWith("DEPRESSION") ||
    n.startsWith("DEEP DEPRESSION") ||
    n.startsWith("INVEST") ||
    n.startsWith("UNNAMED") ||
    n.startsWith("BOB ") ||
    n.startsWith("ARB ") ||
    n.startsWith("DISTURBANCE")
  ) {
    return false;
  }
  return true;
}

export function ActiveCyclones() {
  const { cyclones, selectedId, selectCyclone, loading } = useCyclone();
  const [searchQuery, setSearchQuery] = useState("");
  const [isOpen, setIsOpen] = useState(true);
  const [classificationTab, setClassificationTab] = useState<ClassificationTab>("named");
  const [intensityFilter, setIntensityFilter] = useState<IntensityFilter>("all");
  const [showAllDropdown, setShowAllDropdown] = useState(false);

  // Group into named & unnamed
  const namedCyclones = useMemo(() => cyclones.filter(isNamedCyclone), [cyclones]);
  const unnamedCyclones = useMemo(() => cyclones.filter((c) => !isNamedCyclone(c)), [cyclones]);

  const currentList = classificationTab === "named" ? namedCyclones : unnamedCyclones;

  // Filter by intensity first
  const intensityFilteredList = useMemo(() => {
    if (intensityFilter === "max") {
      return currentList.filter((c) => (c.windKph || 0) >= 165);
    }
    if (intensityFilter === "severe") {
      return currentList.filter((c) => (c.windKph || 0) >= 100 && (c.windKph || 0) < 165);
    }
    if (intensityFilter === "moderate") {
      return currentList.filter((c) => (c.windKph || 0) < 100);
    }
    return currentList;
  }, [currentList, intensityFilter]);

  // Sorted by highest intensity (wind speed descending)
  const sortedByIntensity = useMemo(() => {
    return [...intensityFilteredList].sort((a, b) => (b.windKph || 0) - (a.windKph || 0));
  }, [intensityFilteredList]);

  // Search filtered
  const searchResults = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return sortedByIntensity;
    return sortedByIntensity.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.basin && c.basin.toLowerCase().includes(q)) ||
        (c.category && c.category.toLowerCase().includes(q)) ||
        String(c.windKph).includes(q),
    );
  }, [sortedByIntensity, searchQuery]);

  // Top 5 Highest Intensity in current filter
  const top5Cyclones = useMemo(() => {
    return sortedByIntensity.slice(0, 5);
  }, [sortedByIntensity]);

  // Currently selected cyclone
  const selectedCyclone = useMemo(() => {
    return cyclones.find((c) => c.id === selectedId) ?? cyclones[0];
  }, [cyclones, selectedId]);

  const isSelectedInTop5 = top5Cyclones.some((c) => c.id === selectedId);

  // Basin shortcode helper
  const getBasinShortCode = (basin?: string) => {
    if (!basin) return "NI";
    const b = basin.toLowerCase();
    if (b.includes("bay") || b.includes("arabian") || b.includes("north indian") || b.includes("indian")) return "NI";
    if (b.includes("pacific")) return "WP";
    if (b.includes("atlantic")) return "NATL";
    if (b.includes("south")) return "SI";
    return "GLOBAL";
  };

  const renderRankBadge = (index: number) => {
    if (index === 0) {
      return (
        <span className="shrink-0 rounded border border-amber-500/40 bg-amber-500/15 px-1.5 py-0.5 font-mono text-[9px] font-bold text-amber-300">
          #1
        </span>
      );
    }
    if (index === 1) {
      return (
        <span className="shrink-0 rounded border border-primary/50 bg-primary/20 px-1.5 py-0.5 font-mono text-[9px] font-bold text-primary">
          #2
        </span>
      );
    }
    if (index === 2) {
      return (
        <span className="shrink-0 rounded border border-primary/35 bg-primary/10 px-1.5 py-0.5 font-mono text-[9px] font-bold text-sky-400">
          #3
        </span>
      );
    }
    return (
      <span className="shrink-0 rounded border border-border/80 bg-secondary/80 px-1.5 py-0.5 font-mono text-[9px] font-medium text-muted-foreground">
        #{index + 1}
      </span>
    );
  };

  const renderCycloneCard = (c: Cyclone, index?: number) => {
    const isSelected = selectedId === c.id;
    const basinCode = getBasinShortCode(c.basin);
    const isExtreme = c.windKph >= 140;
    const isSevere = c.windKph >= 100 && c.windKph < 140;

    return (
      <button
        key={c.id}
        onClick={() => selectCyclone(c.id)}
        className={cn(
          "group relative w-full rounded-xl border p-2.5 text-left transition-all duration-200",
          isSelected
            ? "border-primary/80 bg-primary/10 shadow-[0_0_15px_rgba(59,130,246,0.14)] ring-1 ring-primary/40"
            : "border-border/70 bg-card/60 hover:border-border hover:bg-secondary/70 hover:shadow-xs",
        )}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            {typeof index === "number" ? renderRankBadge(index) : null}
            <span
              className={cn(
                "truncate font-display text-[12px] font-semibold uppercase tracking-[0.14em] transition-colors",
                isSelected ? "text-primary" : "text-foreground group-hover:text-primary",
              )}
            >
              {c.name}
            </span>
          </div>

          <span
            className={cn(
              "shrink-0 rounded-md px-2 py-0.5 font-display text-[9px] font-semibold uppercase tracking-[0.16em] border",
              isExtreme
                ? "bg-red-500/10 text-red-400 border-red-500/30"
                : isSevere
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                  : "bg-primary/10 text-primary border-primary/30",
            )}
          >
            {isExtreme ? "EXTREME" : isSevere ? "SEVERE" : "ACTIVE"}
          </span>
        </div>

        <div className="mt-1.5 flex items-center justify-between font-mono text-[10px]">
          <span className="text-muted-foreground truncate mr-2">
            {basinCode} · {c.category || "Cyclonic Storm"}
          </span>
          <span className="shrink-0 text-foreground/90 font-medium">
            {c.windKph > 0 ? `${c.windKph} km/h` : "Monitoring"}
          </span>
        </div>
      </button>
    );
  };

  const hasFilterActive = intensityFilter !== "all" || searchQuery !== "";

  return (
    <Panel className="space-y-3">
      {/* Header with Title, Count Badge & Accordion Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[15px] font-medium tracking-tight">Cyclone Catalog</h3>
          <p className="tech-label mt-0.5">· {classificationTab === "named" ? "146" : "1712"}</p>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex h-7 w-7 items-center justify-center rounded-lg border border-border/80 bg-card/50 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          title={isOpen ? "Collapse list" : "Expand list"}
          aria-label={isOpen ? "Collapse list" : "Expand list"}
        >
          {isOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>
      </div>

      {isOpen && (
        <>
          {/* Pill Toggle (Named vs Unnamed) Styled with Platform Theme */}
          <div className="flex items-center rounded-full border border-border bg-card/90 p-1 shadow-xs backdrop-blur-md">
            <button
              onClick={() => {
                setClassificationTab("named");
                setShowAllDropdown(false);
              }}
              className={cn(
                "flex-1 rounded-full py-1.5 text-center font-display text-[10px] font-semibold uppercase tracking-[0.16em] transition-all duration-200",
                classificationTab === "named"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Named (146)
            </button>

            <button
              onClick={() => {
                setClassificationTab("unnamed");
                setShowAllDropdown(false);
              }}
              className={cn(
                "flex-1 rounded-full py-1.5 text-center font-display text-[10px] font-semibold uppercase tracking-[0.16em] transition-all duration-200",
                classificationTab === "unnamed"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              Unnamed (1712)
            </button>
          </div>

          {/* Pill-shaped Search Input */}
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={`Search ${classificationTab} cyclones (e.g. Mocha)...`}
              className="w-full rounded-full border border-border bg-background/50 py-2 pl-9 pr-8 font-mono text-[11px] text-foreground placeholder:text-muted-foreground/60 transition-all focus:border-primary focus:bg-background/80 focus:outline-none focus:ring-1 focus:ring-primary/40"
            />
            {searchQuery ? (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                title="Clear search"
              >
                <X className="h-3 w-3" />
              </button>
            ) : (
              <ChevronDown className="absolute right-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/60 pointer-events-none" />
            )}
          </div>

          {/* Subtle Intensity Filter Segmented Control */}
          <div className="space-y-1">
            <div className="flex items-center justify-between px-0.5 text-[9px] font-mono uppercase tracking-[0.16em] text-muted-foreground/70">
              <span>Intensity Range</span>
              {hasFilterActive && (
                <button
                  onClick={() => {
                    setIntensityFilter("all");
                    setSearchQuery("");
                  }}
                  className="flex items-center gap-1 font-mono text-[9px] text-primary/90 hover:text-primary transition-colors"
                >
                  <RotateCcw className="h-2.5 w-2.5" />
                  <span>Reset</span>
                </button>
              )}
            </div>

            <div className="grid grid-cols-4 gap-1 rounded-lg border border-border/60 bg-background/40 p-0.5 text-center">
              <button
                onClick={() => setIntensityFilter("all")}
                className={cn(
                  "rounded-md py-1 font-mono text-[9.5px] uppercase tracking-wider transition-all duration-150",
                  intensityFilter === "all"
                    ? "bg-secondary text-foreground font-semibold border border-border/80 shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/40",
                )}
              >
                All
              </button>

              <button
                onClick={() => setIntensityFilter("max")}
                className={cn(
                  "rounded-md py-1 font-mono text-[9.5px] uppercase tracking-wider transition-all duration-150",
                  intensityFilter === "max"
                    ? "bg-red-500/15 text-red-300 font-semibold border border-red-500/30 shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/40",
                )}
                title="Maximum Intensity (≥165 km/h)"
              >
                ≥165
              </button>

              <button
                onClick={() => setIntensityFilter("severe")}
                className={cn(
                  "rounded-md py-1 font-mono text-[9.5px] uppercase tracking-wider transition-all duration-150",
                  intensityFilter === "severe"
                    ? "bg-amber-500/15 text-amber-300 font-semibold border border-amber-500/30 shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/40",
                )}
                title="Severe Storms (100–164 km/h)"
              >
                100–164
              </button>

              <button
                onClick={() => setIntensityFilter("moderate")}
                className={cn(
                  "rounded-md py-1 font-mono text-[9.5px] uppercase tracking-wider transition-all duration-150",
                  intensityFilter === "moderate"
                    ? "bg-primary/15 text-primary font-semibold border border-primary/30 shadow-xs"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/40",
                )}
                title="Moderate Storms & Depressions (<100 km/h)"
              >
                &lt;100
              </button>
            </div>
          </div>

          {/* Subtle Section Header */}
          {!searchQuery && (
            <div className="flex items-center justify-between px-1 pt-1 pb-1 border-b border-border/40 text-[9.5px] font-mono uppercase tracking-[0.14em] text-muted-foreground/80">
              <div className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-primary/80" />
                <span>
                  Top {Math.min(5, sortedByIntensity.length)} {classificationTab === "named" ? "Named Storms" : "Unnamed Systems"}
                </span>
              </div>
              <span className="text-[9px] font-mono text-muted-foreground/60">
                {intensityFilter === "max"
                  ? "≥165 km/h"
                  : intensityFilter === "severe"
                    ? "100–164 km/h"
                    : intensityFilter === "moderate"
                      ? "<100 km/h"
                      : "Highest Intensity"}
              </span>
            </div>
          )}

          {/* Cyclones Content Area */}
          {loading && cyclones.length === 0 ? (
            <div className="py-8 text-center">
              <p className="tech-label animate-pulse text-[10px]">Scanning meteorological catalog...</p>
            </div>
          ) : searchResults.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border/80 p-4 text-center">
              <p className="text-[11px] text-muted-foreground">No cyclones match active intensity filter</p>
              <button
                onClick={() => {
                  setIntensityFilter("all");
                  setSearchQuery("");
                }}
                className="mt-2 text-[10px] font-medium text-primary underline hover:opacity-80"
              >
                Reset intensity filter
              </button>
            </div>
          ) : (
            <div className="space-y-1.5">
              {/* Show Search results OR Filtered Ranking List */}
              {searchQuery ? (
                <div className="space-y-1.5 max-h-[290px] overflow-y-auto pr-1">
                  {searchResults.map((c, i) => renderCycloneCard(c, i))}
                </div>
              ) : (
                <div className="space-y-1.5">
                  {(showAllDropdown ? sortedByIntensity : top5Cyclones).map((c, i) => renderCycloneCard(c, i))}
                </div>
              )}
            </div>
          )}

          {/* Currently Selected (From Search/Click) Theme Box */}
          {selectedCyclone && (!isSelectedInTop5 || searchQuery) && (
            <div className="rounded-xl border border-primary/60 bg-primary/10 p-2.5 shadow-sm">
              <div className="flex items-center justify-between text-[9px] font-display font-semibold uppercase tracking-[0.16em] text-primary">
                <span>CURRENTLY SELECTED (FROM SEARCH)</span>
                <Check className="h-3 w-3" />
              </div>
              <div className="mt-1 flex items-center justify-between">
                <span className="font-display text-[12px] font-bold uppercase tracking-wider text-foreground">
                  {selectedCyclone.name}
                </span>
                <span className="font-mono text-[10px] text-foreground/90 font-medium">
                  {selectedCyclone.windKph > 0 ? `${selectedCyclone.windKph} km/h` : "Monitoring"}
                </span>
              </div>
            </div>
          )}

          {/* Browse all named cyclones dropdown toggle button */}
          {!searchQuery && (
            <button
              onClick={() => setShowAllDropdown(!showAllDropdown)}
              className="flex w-full items-center justify-center gap-1.5 rounded-full border border-border bg-card/60 py-2 px-3 font-display text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-primary/40 hover:bg-secondary hover:text-foreground"
            >
              <span>
                {showAllDropdown
                  ? `Collapse to Top 5 ${classificationTab} cyclones`
                  : `Browse all ${sortedByIntensity.length} ${classificationTab === "named" ? "named" : "unnamed"} cyclones in dropdown`}
              </span>
              <ChevronDown className={cn("h-3 w-3 transition-transform", showAllDropdown && "rotate-180")} />
            </button>
          )}

          {/* Footer Info */}
          <div className="flex items-center justify-between pt-1 text-[9px] font-mono tracking-wider text-muted-foreground/60 border-t border-border/40">
            <span>
              Showing {showAllDropdown ? sortedByIntensity.length : Math.min(5, sortedByIntensity.length)} of{" "}
              {sortedByIntensity.length} {classificationTab === "named" ? "Named Storms" : "Unnamed Systems"}
            </span>
          </div>
        </>
      )}
    </Panel>
  );
}
