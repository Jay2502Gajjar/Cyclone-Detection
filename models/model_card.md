# CycloVision model card

**Bundle: `phase0`. Nothing is trained.**

This file is committed alongside `metrics.json` because the two are the project's
credibility artefacts. It is written before there is anything flattering to put on it: a
model card that only appears once the numbers are good is a marketing page, whereas one
that reports an untrained bundle honestly is an audit trail.

The live version of this is served at `/api/model-card` and rendered at `/model`.

---

## Components

| Key | Declared | Effective | Trained | Metric | Baseline |
|---|---|---|---|---|---|
| `ir_intensity` | `TRAINED_MODEL` | `DEMO_DATA` | no | — | — |
| `dvmax_ri` | `TRAINED_MODEL` | `DEMO_DATA` | no | — | — |
| `track_cliper` | `TRAINED_MODEL` | `DEMO_DATA` | no | — | — |
| `track_cone` | `STATISTICAL_BASELINE` | `DEMO_DATA` | n/a | — | — |
| `analogue` | `ANALOGUE_ENSEMBLE` | `DEMO_DATA` | n/a | — | — |
| `structure` | `DERIVED_MEASUREMENT` | per-frame | n/a | unit-tested on synthetic fields | — |
| `regime_rules` | `RULE_ENGINE` | `DEMO_DATA` | n/a | thresholds not yet tuned | — |
| `risk_rules` | `RULE_ENGINE` | `DEMO_DATA` | n/a | — | — |
| `report_template` | `RULE_ENGINE` | `RULE_ENGINE` | n/a | deterministic | — |

`structure` is real, tested code; whether its output can claim `DERIVED_MEASUREMENT` is
decided per request by whether the frame actually has a brightness-temperature array to
measure.

## Datasets

None ingested. Phase 1 imports IBTrACS and joins HURSAT-B1 on
`(SID, |Δt| ≤ 90 min)`. Sources, licences and the resulting match rate go in
[`../data/MANIFEST.md`](../data/MANIFEST.md).

## Split

Storm-wise, never frame-wise — frames within a storm are heavily autocorrelated and a
random split would leak and inflate every metric. Demo storms are always in `test`,
enforced by an assertion in `ml/train/splits.py`, a database CHECK constraint, and a flag
on this card.

## Planned evaluation

Each trained model reports a held-out metric **and** the baseline it is compared against.
A metric without a baseline is not an auditable claim, and the registry refuses to
register one.

| Model | Metric | Baseline |
|---|---|---|
| `ir_intensity` | MAE (kt) | mean predictor |
| `dvmax_ri` — ΔVmax | MAE (kt) | persistence |
| `dvmax_ri` — RI | PR-AUC | climatological base rate (~5%) |
| `track_cliper` | mean track error (km) at 12/24/48 h | pure persistence |
| `track_cone` | observed containment vs nominal p67/p90 | — |

RI is reported as PR-AUC and lift over the base rate, never as accuracy: at a ~5% base
rate, a model that always predicts "no" scores 95% and is useless.

## The ablation

The multi-source claim is tested, not asserted. `ml/eval/ablation.py` reports track-only,
image-only and fused error on identical held-out storms. **We do not claim fusion until
that table says so** — if the imagery adds nothing, this card will say the imagery adds
nothing.

| Feature set | MAE (kt) | n |
|---|---|---|
| track-only | not measured | — |
| image-only | not measured | — |
| fused | not measured | — |

## What we did not build, and why

- **A trained Dvorak-pattern classifier.** No free labelled Dvorak dataset exists at
  scale. We measure the physical quantities a Dvorak analyst reads by eye and classify the
  regime with a transparent rule engine whose thresholds are shown in the UI. The regimes
  are Dvorak-*inspired* names for morphologies we can measure; we do not claim agreement
  with the Dvorak technique.
- **Wide-field cyclone detection with bounding boxes.** No labelled detection data
  available in the time budget. Our imagery is storm-centred, so detection is not
  required for what we do.
- **A deep sequence trajectory model (GRU/LSTM/Transformer).** Cannot be trained and
  validated reliably in the window. We use a CLIPER-style model — the operational
  benchmark — and report our error against pure persistence.
- **Live satellite ingestion.** The product is historical replay and hindcast
  verification. A live feed would add a demo-time network dependency for no scientific
  gain.
- **Observed sea-surface temperature and wind shear.** Reanalysis downloads are too heavy
  for the window. A feature-vector slot is reserved. Anything used before then would be
  climatology, and would be labelled as such.

## Known limitations

- The satellite footprint on the map is an approximate placement of a storm-centred tile,
  not a reprojection. Adequate at basin zoom; stated rather than hidden.
- Structural thresholds are documented starting points, not tuned results, until Phase 2.
- If HURSAT is substituted for CNN training (see `docs/data-sources.md`), the resulting
  sensor and rendering domain shift will be stated here.
