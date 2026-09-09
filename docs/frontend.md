# Frontend

The intended structure of the Command Center. This documents what exists and what it is for;
it does not propose new UI.

**Stack:** React 19 · Vite 8 · TypeScript 6 · Tailwind v4 · MapLibre GL · Recharts ·
TanStack Query · Zustand · Radix primitives.

---

## Routes — exactly two

```
/         CommandCenter    the product
/model    ModelCard        the credibility screen
*         → CommandCenter  no 404 page; there is nowhere to be lost
```

**Depth on one screen beats breadth across seven.** Every extra route dilutes a four-minute
demo, and a navigation tree implies somewhere else to go. Everything that would have been a
page is a drawer instead.

`react-router-dom` is used so `/model` is linkable and the back button works. It is not
state management.

---

## Component tree

```
App
└── AppRoutes
    ├── CommandCenter                                          route /
    │   ├── StormMap                    ★ full-bleed background
    │   │   └── layers/
    │   │       ├── track.ts            observed · forecast · cone · analogues · truth · marker
    │   │       └── irOverlay.ts        georeferenced satellite frame
    │   ├── HeaderBar                   name · Explore|Verify · health · ⓘ→/model
    │   ├── DemoDataBanner              conditional: any DEMO_DATA on screen
    │   ├── StormRail                   left, 260px, collapsible
    │   ├── IntelligencePanel           right, 340px
    │   │   ├── Metric                  headline wind
    │   │   ├── ConfidenceBar
    │   │   ├── ProvenanceChip          on every value
    │   │   └── VerificationReadout     Verify mode only
    │   ├── TimelineScrubber            ★ bottom, 132px — the signature element
    │   │   └── IntensitySparkline      observed vs model estimate
    │   ├── EvidenceDrawer              overlay
    │   │   ├── GradCamView
    │   │   ├── StructureMetrics
    │   │   └── ShapBars
    │   └── AnaloguesDrawer             overlay
    │       └── AnalogueOutcomeChart
    └── ModelCard                                              route /model
```

### Responsibilities

| Component | Owns |
|---|---|
| `StormMap` | The MapLibre instance and every layer. Nothing else touches the map. |
| `TimelineScrubber` | The primary interaction; playback; keyboard handling |
| `IntensitySparkline` | Hand-drawn SVG of observed vs estimated intensity |
| `IntelligencePanel` | Progressive disclosure level 1, and the drawer triggers |
| `StormRail` | Storm selection; deliberately recedes |
| `HeaderBar` | Identity, mode switch, health, the Model Card link |
| `EvidenceDrawer` | Level 2 — Grad-CAM, metrics, attributions |
| `AnaloguesDrawer` | Level 2 — outcome distribution, then matches |
| `ProvenanceChip` | The visible consequence of the provenance system |
| `DemoDataBanner` | Global honesty signal |

---

## State ownership

Three tiers, and nothing crosses them.

### 1. Server state — TanStack Query

| Hook | Query key | Stale time | Notes |
|---|---|---|---|
| `useStormList` | `['storms']` | `Infinity` | The curated set does not change in-session |
| `useHealth` | `['health']` | 30 s poll | |
| `useStorm(sid)` | `['storm', sid]` | `Infinity` | **The whole timeline, held forever** |
| `useFrame(sid, t)` | `['frame', sid, t]` | `Infinity` | `keepPreviousData` prevents flicker while scrubbing |
| `useForecast(sid)` | mutation | — | An explicit user action that writes server-side |
| `useModelCard` | `['model-card']` | default | |

`retry: false` globally. During a demo a failed call should surface immediately as a clear
message rather than hang through three silent attempts — and the backend already degrades
gracefully on its own side.

### 2. Global UI state — Zustand, three fields

```ts
{
  selectedSid: string | null
  cursorTime:  string | null       // ISO instant of the scrubber
  mode:        'explore' | 'verify'
  verifyFrom:  string | null       // the moment a forecast was issued for
  revealed:    boolean
}
```

**A store that grows past this is a sign something is in the wrong place.**

`selectStorm()` resets the cursor and any in-progress verification: carrying a timestamp
from one storm to another would silently show the wrong frame.

### 3. Local state — `useState`

Drawer open/closed, Grad-CAM toggle, playback. Nothing shared, so nothing global.

**No Redux, no Context for data, no prop-drilling of server state.** Components receive data
via props; nothing reaches into a store directly except the pages.

---

## API usage

`api/client.ts` — native `fetch`, no wrapper library. Its one job beyond fetching is turning
the backend's error envelope into a thrown `ApiRequestError` **with its code intact**, so
callers can distinguish "no frame at that instant" from "the AI service is down" without
parsing strings.

`types/api.ts` mirrors [`API_CONTRACT.md`](../API_CONTRACT.md) exactly. **`tsc -b` is the
frontend's half of the drift check**: if the backend changes a field, the build fails here
rather than the UI silently rendering `undefined` during a demo.

`mediaUrl()` resolves `/media/...` paths against the configured origin. In development the
Vite proxy forwards `/api` and `/media` to `:8090`, so image URLs are identical in
development and production.

---

## Map layers

Owned by `components/map/`, driven **imperatively**.

| Order | Layer | Source | Colour |
|---|---|---|---|
| 1 | Dark basemap | CARTO dark-matter (free, no API key) | — |
| 2 | IR frame | `image` source, updated per scrub | greyscale |
| 3 | Analogue tracks | `analogue-tracks` | neutral, 35% |
| 4 | Confidence cone | `forecast-cone` | accent, 6–12% |
| 5 | Observed track | `observed-track` | **truth** |
| 6 | Forecast track | `forecast-track` | **accent, dashed** |
| 7 | Revealed truth | `observed-future` | **truth**, solid, heavier |
| 8 | Storm marker | `current-position` | truth |

### Two colour rules that carry meaning

- **Near-white (`--cv-truth`)** — observed values and ground truth. Never accented.
- **Cool accent (`--cv-accent`)** — AI output and interactive affordances. Nothing else.

A viewer can tell a measurement from a prediction at a glance, without a legend.

### Why imperative

MapLibre owns a WebGL canvas and its own layer graph. Wrapping that declaratively buys
little for six layers and adds a version-compatibility dependency. `StormMap` owns the
instance; layer functions update sources in `useEffect`. React never re-creates the map.

**Confining it to `components/map/` is also what makes a swap to React Leaflet a local
change rather than a rewrite** — the pre-agreed fallback if MapLibre causes friction.

### Behaviours that matter

- **Fit bounds once per storm.** Refitting on every scrub would fight the user's own panning.
- **A frame with no imagery removes the overlay** rather than leaving the previous image
  behind — showing an old picture at a new timestamp would be a quiet lie.
- **A point with null cone radii draws no cone.** An uncalibrated cone would be the single
  most misleading thing on the map.

---

## The timeline

The signature element, and the primary interaction.

### Performance contract

| Property | Requirement | How |
|---|---|---|
| No network on drag | Hard requirement | `frames[]` is in the TanStack cache |
| No inference on drag | **Invariant I5** | The read path serves precomputed rows |
| 60 fps | Target | Only the sparkline SVG and map sources update |
| 1:1 with the pointer | Hard requirement | No easing on the scrub |

**Easing a value the user is directly manipulating makes it feel laggy.** The only "motion"
here is the cursor following the finger exactly.

### The sparkline

Observed intensity (solid, truth colour) against the model's per-frame estimate (dashed,
accent) across the whole storm.

Hand-drawn SVG, not a charting library: it must redraw under a 60 fps drag inside a 132 px
bar, and a general-purpose chart component would be both slower and harder to make that
small.

**The line breaks across gaps.** Frames without an estimate are genuinely absent;
interpolating would draw a model output where none exists.

### Keyboard

`←` `→` step one frame · `space` toggles playback. Ignored while focus is in an input.

---

## Drawers

Radix `Dialog`, sliding from the right at ~52% width, over a blurred map.

**The map stays visible behind them**, so opening one reads as *looking closer at the same
thing* rather than navigating away. That is precisely why they are drawers and not routes.

`Esc` dismisses. At most one is open at a time.

**Evidence** builds an argument in order: the frame and what the model looked at → the
measurements taken from that same frame → the regime rules that fired → the attributions for
the forecast those measurements feed → a provenance explainer.

**Analogues** puts the aggregate first and the individual storms second. The aggregate *is*
the forecast; the named storms are the evidence for it. Reversing that order is how this
becomes a "similar storms" card again.

---

## Model Card

A conventional document layout — the one place a plain, scrollable page is correct, because
it is a reference rather than an instrument.

Sections: bundle · datasets · split · models · **ablation** · cone calibration · **what we
did not build, and why**.

It renders correctly when `metrics.json` is absent — datasets empty, every model "not
trained", ablation "not measured". That honest empty state is why the page is built in
Phase 0, before there is anything flattering on it.

---

## Design tokens

`src/theme/tokens.css`, Tailwind v4 `@theme`.

```
--color-cv-ground        #0B1020    deep desaturated navy, never pure black
--color-cv-glass         rgb(255 255 255 / 0.055)
--color-cv-glass-border  rgb(255 255 255 / 0.10)
--color-cv-accent        #4DD4CE    AI output + interactive ONLY
--color-cv-truth         #E8EAF0    observed values ONLY, never accented
--radius-cv              14px
--blur-cv                20px
font                     Inter; 32 / 18 / 13; JetBrains Mono for figures
```

Intensity ramp — sequential, for storm categories only, never a rainbow:
`#6BA6D6 → #8FC0C8 → #E8C25A → #E08E4A → #E0654A`

### The discipline rules

| Rule | Reason |
|---|---|
| **Max two glass surfaces stacked** | Blur-on-blur turns to mud |
| **Max two panels open at once** | The map is the centrepiece |
| **Accent appears at most ~3 times per screen** | Reserved means reserved |
| **No card inside a card** | The failure mode this design exists to avoid |
| **No card grid anywhere** | Same |
| **One shadow, no glow** | Restrained, not cyberpunk |
| **Tabular numerals on every figure** | Columns must not jitter while scrubbing |
| **150 ms ease-out; the scrub is unanimated** | Direct manipulation must feel direct |

`.cv-glass`: one background, one border (brighter on top, as if lit from above), one
backdrop blur, one shadow. Nothing pulses, nothing glows.

`prefers-reduced-motion` collapses transitions. The scrub is already unanimated.

**Dark only.** Committing to one theme is the right trade for a demo product; a light theme
would double the design surface for no evaluator benefit.

---

## Responsive expectations

Designed for a **laptop or projector at ≥1280×800** — the demo context.

| Element | Behaviour |
|---|---|
| Map | Fills the viewport at any size |
| Storm rail | 260 px fixed; collapsible |
| Intelligence panel | 340 px fixed; scrolls internally |
| Timeline | Full width minus 24 px |
| Drawers | `min(52vw, 720px)` |
| Body | `overflow: hidden` — the map owns the viewport; panels scroll internally |

**Mobile is out of scope.** A timeline scrubber driving a map and two side panels does not
compress to a phone without becoming a different product, and no evaluator will open it on
one. Stated rather than half-attempted.

---

## Performance expectations

| Operation | Target | Mechanism |
|---|---|---|
| Initial load | < 2 s | Single bundle |
| Storm selection | < 500 ms | One request for the whole timeline |
| **Scrub** | **60 fps, zero network** | In-memory array (I5) |
| Frame detail | < 200 ms | Cached + ±5 prefetch |
| Forecast | < 8 s | AI timeout; falls back rather than hanging |
| Drawer | Instant | Already-fetched data |

The production bundle is ~1.36 MB (≈380 KB gzipped), dominated by MapLibre and Recharts.
Code-splitting is deliberately **not** done: the app has two routes and a demo loads once,
so splitting would add complexity and a loading state for no benefit.

---

## Testing

| Check | Command | Guards |
|---|---|---|
| Type check | `npm run build` (`tsc -b`) | **Contract drift** |
| Lint | `npm run lint` (oxlint) | Correctness patterns |
| Manual click-through | before every demo | Everything else |

**No component test suite.** For a product of this size and lifespan, `tsc` against a
locked contract plus a rehearsed manual pass catches more real problems than a component
suite would — and the contract check is the one that matters, because a silent
`undefined` during a demo is the failure that costs most.

---

## Phase 0 state

| Built | Not built |
|---|---|
| All routes, components, hooks, layers, tokens | Real data to render |
| Empty states with explanations | Grad-CAM overlays (no model) |
| Provenance chips and the banner | Populated analogue drawer |
| Build, typecheck and lint passing | Visual verification — **nobody has looked at it yet** |

With no storms, the rail says "No storms loaded yet" and the timeline shows an explanation
instead of a scrubber. `/model` renders fully and is the most informative screen today.

> **Outstanding:** the UI has never been visually confirmed in a browser. Build, lint and
> dev server all pass, but that is not the same as the layout being right. This should be
> the first task of Phase 6.
