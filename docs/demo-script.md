# Demo script

Four minutes. Rehearsed at least three times before presenting — once with the network
disabled, once with the AI service killed mid-run.

**This script describes the Phase 4 demo.** It is written now because it is the
specification the build is aimed at: if a feature does not appear here, it is not worth
the hours. Phase 0 cannot run it — nothing is trained yet.

---

## The sequence

| Time | On screen | What you say |
|---|---|---|
| **0:00–0:20** | App already open on Fani 2019, mid-lifecycle. No login, no chooser. | "This is Cyclone Fani, May 2019. Real infrared satellite imagery from NOAA's HURSAT archive, georeferenced on its real best track. This isn't a weather map — it's a flight recorder." |
| **0:20–0:50** | **Drag the scrubber** across the full lifetime, then point at the sparkline. | "One control drives everything." → **"The solid line is the observed intensity. The dashed line is what our CNN estimated from the satellite image alone, frame by frame — it never saw the wind speeds. That's nine days of agreement, and Fani is in our held-out test set."** |
| **0:50–1:25** | Park at 2 May 06:00 UTC. Open **Evidence**. Toggle Grad-CAM. | "At this instant the system identifies an eye — 22 km radius, 41 K contrast against the eyewall, symmetry 0.89. And the network is attending to exactly that eyewall ring. Those structure numbers aren't a model output — they're measured directly from the brightness-temperature field, which is why they're tagged Measured. Every number here tells you what produced it." |
| **1:25–2:00** | Close the drawer. Intelligence panel. | "Fusing the image features with track kinematics: +8 knots over 24 hours, and a 34% probability of rapid intensification against a climatological base rate of 5%. SHAP says the top drivers are structural symmetry and the 12-hour trend — the image is carrying real signal." |
| **2:00–2:30** | Open **Analogues**. | "Independently, we search 40 years of cyclones for storms whose last 24 hours of evolution looked like this. Twenty matches. Fourteen intensified. Five underwent rapid intensification — 25% against 5%. The closest is the 1999 Odisha super cyclone. Two independent methods agreeing is evidence; one model asserting is not." |
| **2:30–3:20** | Switch to **Verify** → *Forecast from this moment* → **pause** → *Reveal what happened*. | "Everything so far was a prediction. Let's check it." → **"24-hour track error: 63 kilometres. Intensity error: 2 knots. Inside our 67% confidence cone — and that cone isn't a guess, its radius is the 67th percentile of our model's actual held-out errors across 1,204 forecasts."** → "You can pick any moment in this storm and we'll do that again." |
| **3:20–3:50** | `/model` — the Model Card. | "And here's our homework. Storm-wise splits, so no leakage. CNN intensity MAE 12.4 knots. The track model beats pure persistence at every horizon. And the ablation: track-only 11.6, image-only 14.2, fused 9.8 — that's what makes this genuinely multi-source rather than two datasets on one screen. We also list what we didn't build, and why." |
| **3:50–4:00** | Back to the Command Center. | "Identification, classification, prediction — across the whole lifecycle of the storm, with every claim measured. That's CycloVision." |

*Numbers above are illustrative. Read the real ones off the screen; never quote a figure
the build cannot show.*

## The two moments that matter

**0:40 — the sparkline.** Two lines tracking each other across a nine-day lifecycle is
wordless proof the vision model works, and it is visible before anyone clicks anything.

**2:30 — the reveal.** Let it breathe. Pause before clicking. This is the only moment in
the room where a prediction becomes a measured, checkable result, and inviting the judge
to pick their own moment T is what makes it un-cherry-picked.

## If you are asked a hard question

| Question | Answer |
|---|---|
| "How do I know you didn't train on this storm?" | The Model Card shows storm-wise splits and `demoStormsInTest`. The database physically refuses a demo storm in the training split. |
| "How do I know the forecast didn't see the future?" | The request schema has no field that can carry it, and the validator rejects it with a 422. Two independent filters, one in each service. |
| "Is that a Dvorak classification?" | No, and we don't claim it is. There's no free labelled Dvorak dataset at scale. We measure the physical quantities a Dvorak analyst reads by eye and classify with a transparent rule engine — the thresholds are on screen. |
| "Why not a deep sequence model for the track?" | We can't validate one in the time available. CLIPER is the operational benchmark forecasters measure themselves against, and we report our error against pure persistence. |
| "Is this better than IMD's forecast?" | No. Official forecasts are considerably better. We're demonstrating a methodology and reporting our error honestly. |

## Insurance

Everything except **Verify** runs on precomputed data, so the scrubber cannot be broken by
a model failure (invariant I5).

Before walking up:

```powershell
.\scripts\demo-check.ps1
```

It verifies the three services, counts storms and precomputed frames, confirms every demo
storm is still held out, and reports whether `DEMO_MODE` is on. Exit code 0 means safe to
present.

- **`DEMO_MODE=true`** serves stored scenarios, stamped `DEMO_DATA` and
  `servedFrom: "demo"`. It cannot masquerade as a live model.
- **Run on localhost.** Treat any cloud deployment as a bonus URL, not a dependency.
- **Full-screen screenshots** of all four views in a folder on the desktop.
- **Rehearse the AI service dying.** Kill it mid-demo once: the timeline keeps working and
  the forecast falls back with a visible `cached` chip. Knowing that is survivable is
  worth more than hoping it won't happen.
