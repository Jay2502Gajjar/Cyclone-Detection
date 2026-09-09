# Demo flow

The four-minute demonstration. Rehearsed at least three times before presenting — once with
the network disabled, once with the AI service killed mid-run.

> **This describes the Phase 7 demo.** It is written now because it is the specification the
> build aims at: if a feature does not appear here, it is not worth the hours.
>
> **Phase 0 cannot run it.** Nothing is trained and no data is loaded.
>
> **Every number below is a placeholder**, written as `[MAE]`, `[N]`, `[error]`. Read the
> real values off the screen. **Never quote a figure the build cannot show.**

---

## Structure

| Time | Section | The point |
|---|---|---|
| 0:00–0:30 | Problem and product | Frame it as an instrument, not a dashboard |
| 0:30–1:15 | Evolution Replay | **The AI-is-real moment** |
| 1:15–2:00 | Structural Signature + intensity | The scientific core |
| 2:00–3:00 | **Rewind & Verify** | **The memorable moment** |
| 3:00–3:40 | Analogue Ensemble | Independent corroboration |
| 3:40–4:00 | Model Card | Credibility and limitations |

---

## 0:00–0:30 — Problem and product

**Show:** the app already open on a demo storm, mid-lifecycle. No login, no chooser, no
empty state.

**Say:**

> "The problem is identifying, classifying and predicting tropical cyclone patterns from
> multi-source satellite data.
>
> This is `[storm name]`, `[year]`. What you're seeing is real infrared satellite imagery
> from NOAA's HURSAT archive, georeferenced onto its real best track from IBTrACS.
>
> This isn't a weather map. It's a flight recorder — and the point of a flight recorder is
> that you can go back and check."

**Why this framing.** It sets the expectation that the product will be *checked*, which is
what the middle of the demo delivers. Opening on a live storm rather than a chooser saves
fifteen seconds and signals that the product is already doing something.

---

## 0:30–1:15 — Evolution Replay

**Show:** drag the timeline scrubber slowly across the storm's full lifetime. Everything
moves together — satellite frame, marker, structural readout, panel. Then stop and point at
the sparkline.

**Say:**

> "One control drives everything. The satellite image, the position, the structure the model
> reads, the intensity estimate — all synchronised, because the satellite record and the
> best track are joined on time.
>
> Now look at the bottom.
>
> **The solid line is the observed intensity from the best track. The dashed line is what
> our CNN estimated, frame by frame, from the satellite image alone — it never saw the wind
> speeds. That's `[N]` days of agreement. And this storm is in our held-out test set.**"

**Why this is the AI-is-real moment.** Two lines tracking each other across an entire
lifecycle is wordless proof, and it is visible before anyone clicks anything. It arrives 40
seconds in, before attention has drifted.

**Note the honest gaps.** Where the dashed line breaks, say so: *"the line breaks where
there's no matched satellite pass — we show the gap rather than drawing through it."* The
gap is a credibility asset, not a flaw to skate over.

---

## 1:15–2:00 — Structural Signature and intensity intelligence

**Show:** park the scrubber at a well-organised moment. Open the **Evidence** drawer. Toggle
Grad-CAM. Then close it and return to the intelligence panel.

**Say:**

> "At this instant the system identifies an eye — `[radius]` kilometres across, `[contrast]`
> Kelvin of contrast against the eyewall, symmetry `[value]`.
>
> Now watch the attention map. **The network is looking at exactly that eyewall ring** — the
> feature we located independently, without the network, straight from the brightness
> temperatures.
>
> And these numbers are tagged *Measured*, not *Trained model*. They're deterministic physics
> over the raw Kelvin field. Every number in this application tells you what produced it.
>
> One thing we're explicit about: **this is not a Dvorak classifier.** There's no free
> labelled Dvorak dataset at scale, so we don't claim one. We measure what a Dvorak analyst
> reads by eye, and classify with a rule engine whose thresholds are on screen."

Close the drawer.

> "Fusing those image features with the track kinematics: `[ΔVmax]` knots over 24 hours, and
> a `[P]`% probability of rapid intensification — against a climatological base rate of
> about `[base]`%."

**Why the pairing matters.** Grad-CAM alone is easy and everyone has one. It earns its place
because the structural metrics found the same feature independently — that agreement is a
validation signal, not a heatmap.

**The Dvorak disclaimer is deliberate.** Volunteering the limitation before anyone asks is
what buys credibility for everything else.

---

## 2:00–3:00 — Rewind & Verify

**The centrepiece. Do not rush it.**

**Show:** switch to Verify. **Invite the judge to choose the moment.** Click "Forecast from
this moment". Let the cone and dashed track draw. **Pause.** Then click "Reveal what
happened".

**Say:**

> "Everything so far has been a prediction, and predictions are unfalsifiable in a four-minute
> demo. So let's check one.
>
> Pick a moment — any moment in this storm."

*(Forecast draws.)*

> "The system has now forecast from that instant using **only** data available at or before
> it. The future is masked in two independent places: the backend filters it out, and the
> inference service rejects the request outright if anything later slips through.
>
> That's the prediction."

**Pause. Two seconds. Let it stand alone.**

> "Now — what actually happened."

*(Reveal.)*

> "**Track error at 24 hours: `[error]` kilometres. Intensity error: `[error]` knots.**
>
> Inside our 67% cone — and that cone isn't a guess. Its radius is the 67th percentile of
> this model's *actual held-out errors* across `[N]` forecasts.
>
> Pick another moment and we'll do it again."

**Why this is the memorable moment.** It is the only point in the room where a prediction
becomes a measured, checkable result — on an input the judge chose.

**Choreography notes:**

- **The pause before Reveal is the feature.** Do not fill it.
- **Let them pick T.** It is what makes the result un-cherry-picked, and offering it is more
  persuasive than any number.
- If the error is large, say so plainly and note what a large error at that lead time means.
  A demonstrated miss is still a demonstrated *measurement*, and reacting calmly to it is
  more convincing than a good result.

---

## 3:00–3:40 — Analogue Ensemble

**Show:** open the **Analogues** drawer. Outcome distribution first, then the matches. Toggle
onward tracks onto the map.

**Say:**

> "One model asserting something isn't evidence. So we do it a second way, independently.
>
> We search the historical record for storms whose **last 24 hours of evolution** looked like
> this one's — not a snapshot, an evolution — excluding this storm and anything from the same
> season.
>
> Twenty matches. `[N]` intensified. `[N]` underwent rapid intensification: `[P]`% against a
> `[base]`% base rate.
>
> The closest is `[storm name]`, `[year]`. Those faint lines are where each of those storms
> actually went next.
>
> **This method shares no parameters with the model that produced the earlier forecast.** When
> two independent methods agree, that's evidence. When they disagree, that's information about
> confidence — and we show that too."

**If the two disagree during the demo, lead with it.** *"Interesting — they disagree here,
and that itself tells you something."* That reads as confidence in the method rather than
hoping nobody noticed.

**Be precise about what an analogue means.** If asked: *"it's not 'this storm will behave like
that one'. It's 'storms whose recent evolution resembled this one went on to do the
following'."*

---

## 3:40–4:00 — Model Card, credibility, limitations

**Show:** navigate to `/model`.

**Say:**

> "And here's our homework.
>
> Storm-wise splits — never frame-wise, because consecutive observations of one cyclone are
> nearly identical and a random split would leak. Every demo storm is in the held-out set,
> and the database physically refuses to store one that isn't.
>
> Every model reports a held-out metric **and** the baseline it beats. CNN intensity MAE
> `[value]` against `[baseline]`. The track model against pure persistence.
>
> And the ablation — track-only `[value]`, image-only `[value]`, fused `[value]`. **That's
> what makes this genuinely multi-source rather than two datasets on one screen.**
>
> And here's what we didn't build, and why."

*(Scroll to the omissions.)*

> "No Dvorak classifier, because the labels don't exist. No deep sequence track model, because
> we couldn't validate one in the time. No live ingestion, because it would add a demo-time
> network dependency for no scientific gain.
>
> Identification, classification and prediction — across a storm's whole lifecycle, with every
> claim measured."

**Why end here.** It answers the hardest question in the room before it is asked, and it
leaves the last impression as rigour rather than flourish.

---

## Hard questions, and the answers

| Question | Answer |
|---|---|
| *"How do I know you didn't train on this storm?"* | The Model Card shows storm-wise splits and `demoStormsInTest`. The database has a CHECK constraint that physically refuses a demo storm in the training split. |
| *"How do I know the forecast didn't see the future?"* | The request type has no field that can carry it, and the inference service returns 422 if the history contains anything later than the as-of time. Two independent filters, in two services. |
| *"Is that a Dvorak classification?"* | No, and we don't claim it is. There's no free labelled Dvorak dataset at scale. We measure the physical quantities a Dvorak analyst reads by eye and classify with a transparent rule engine — the thresholds are on screen. |
| *"Why not a deep learning track model?"* | We can't validate one in the time available, and an under-trained sequence model is worse than useless. CLIPER is the operational benchmark forecasters measure themselves against, and we report our error against pure persistence. |
| *"Is this better than IMD's forecast?"* | No. Official forecasts are considerably better. We're demonstrating a methodology and reporting our error honestly. |
| *"Why is everything greyed out / why does it say Placeholder?"* | *(If demoing an untrained build)* Because nothing is trained yet. The system reports absent values rather than estimating them — that labelling is deliberate. |
| *"What's the RI skill?"* | PR-AUC `[value]` against a `[base]`% base rate. We never report RI as accuracy: at a 5% base rate, always saying "no" scores 95% and is useless. |

---

## Preflight

```powershell
.\scripts\demo-check.ps1
```

**Run this immediately before presenting, every time.** It verifies the three services,
counts storms and precomputed frames, confirms every demo storm is still in the `test` split,
and reports whether `DEMO_MODE` is on. Exit code 0 means safe to present.

---

## Insurance

| Risk | Mitigation |
|---|---|
| AI service dies mid-demo | Everything except Verify runs on **precomputed** data (invariant I5). The scrubber keeps working. |
| Forecast fails | Falls back to a cached run or a stored scenario with a visible `cached` / `demo` chip |
| Venue network fails | Runs entirely on localhost. Zero external calls in the demo path — the reason live ingestion was cut. |
| Everything fails | Full-screen screenshots of all four views in a folder on the desktop |
| Something looks wrong live | `DEMO_MODE=true` serves stored scenarios, stamped `DEMO_DATA`. It cannot masquerade as a live model. |

**Rehearse the AI service dying.** Kill it mid-run once during practice: the timeline keeps
working and the forecast falls back visibly. Knowing that is survivable is worth more than
hoping it will not happen.

---

## Timing discipline

| Section | Budget | If running long |
|---|---|---|
| Problem and product | 0:30 | Cut to two sentences |
| Evolution Replay | 0:45 | **Never cut.** This is the AI-is-real moment. |
| Structure + intensity | 0:45 | Drop the intensity paragraph, keep Grad-CAM |
| **Rewind & Verify** | **1:00** | **Never cut. Never rush.** |
| Analogues | 0:40 | Give the aggregate only, skip the matches list |
| Model Card | 0:20 | Show the ablation and the omissions only |

**The two that never get cut are the sparkline and the reveal.** Everything else is
negotiable.

---

## What is deliberately not demonstrated

- The API, Swagger, or any code
- The database schema
- The architecture diagram
- Anything requiring an explanation longer than one sentence

Judges evaluate the product and the evidence behind it. Architecture belongs in the
documentation, not the four minutes.
