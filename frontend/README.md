# CycloVision frontend

The Command Center. Two routes, two drawers, one primary control.

```
/         CommandCenter   map · storm rail · intelligence panel · timeline scrubber
/model    ModelCard       datasets, held-out metrics, ablation, what we did not build
```

The map is the page background at full bleed; everything else floats on it as glass. That
decision is what keeps the map the centrepiece and stops the layout reading as an admin
dashboard.

Global state is three fields in `store/timeline.ts` (`selectedSid`, `cursorTime`, `mode`).
Everything else is TanStack Query server state or local component state.

`types/api.ts` mirrors [`../API_CONTRACT.md`](../API_CONTRACT.md). `tsc -b` is the check
that the frontend has not drifted from the backend.

## Running

```powershell
npm run dev      # :5173, proxies /api and /media to the backend on :8090
npm run build    # typecheck + production build
npm run lint
```
