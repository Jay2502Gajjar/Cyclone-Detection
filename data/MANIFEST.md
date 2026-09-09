# Data manifest

The bulk of `data/` is gitignored because it is large and regenerable. This file is not:
it records exactly what was downloaded, from where, under what licence, and how much of
it survived the join. Reproducibility depends on it, and so does the Model Card's dataset
table.

**Status: nothing ingested yet.** Phase 0 builds the runnable architecture; Phase 1 fills
this in.

## Planned sources

### NOAA IBTrACS v4 — best track (the numerical backbone)

- **What it provides:** the canonical storm identifier (`SID`, e.g. `2019114N06084`),
  3/6-hourly position, maximum sustained wind, central pressure, storm name and basin.
- **Role:** supervision labels for the vision model, the entire track model, the
  kinematic half of the fused feature vector, and every `OBSERVED` value in the UI.
- **Download:** basin subsets only (`ibtracs.NI.list.v04r00.csv` for North Indian). A few
  megabytes rather than the >100 MB global file, and the North Indian basin is what the
  problem statement is framed around.
- **Licence:** US Government work, public domain. NOAA NCEI.

### NOAA HURSAT-B1 — storm-centred infrared imagery

- **What it provides:** `IRWIN` brightness temperature in Kelvin on a storm-centred grid,
  roughly 8 km resolution, 3-hourly, 1978–2015.
- **Role:** the satellite half of the fusion. Structural metrics are measured from the
  raw Kelvin field; the CNN is trained on normalised renderings of it.
- **Verify before bulk parsing:** grid shape, resolution, BT units and the SID/time
  attribute names, on **one** file. The whole pipeline shape depends on these, and
  assuming them is the single most expensive mistake available in Phase 1.
- **Licence:** US Government work, public domain. NOAA NCEI.

### Natural Earth — coastlines

- **Role:** `dist_to_coast_km` per observation, precomputed offline with shapely, and the
  landfall-proximity term of the risk score.
- **Licence:** public domain.

## The join

```
(SID, nearest best-track observation within ±90 minutes)
```

One satellite frame per `(sid, obs_time)`. Where several satellites cover one time, prefer
the most complete grid.

Best-track rows with no matching frame are kept, with `image_path` null. The timeline must
have no holes; the UI simply shows no imagery at those instants, and the structural block
reports absence rather than zeros.

**Match rate must be recorded here and reported on the Model Card.** "8,412 of 11,033
track points had a matched IR frame (76%)" is the kind of accounting that makes the rest
of the numbers credible.

## Storage

| Path | Contents | Committed? |
|---|---|---|
| `raw/` | untouched downloads | no |
| `interim/joined.parquet` | the join output | no |
| `processed/features.parquet` | the fused feature matrix | no |
| `frames/{sid}/{ts}.png` | 8-bit render for display, fixed 180–300 K scale | no |
| `frames/{sid}/{ts}.npy` | raw Kelvin, what the metrics actually measure | no |
| `gradcam/{sid}/{ts}.png` | attention overlays | no |
| `MANIFEST.md` | this file | **yes** |

Both the PNG and the `.npy` are kept per frame on purpose. Quantising to 8 bits for
display costs roughly half a Kelvin per level, which is enough to move the eye-contrast
and CDO-fraction thresholds — so the metrics read the array, and only the browser reads
the picture.

## Fallback

If HURSAT proves slow or awkward to obtain, the pre-agreed substitute for **CNN training
only** is the DrivenData / NASA-IMPACT tropical storm wind-speed dataset (curated
single-band IR with wind labels and storm identifiers). HURSAT would still be used for the
geolocated demo storms, since that dataset carries no latitude/longitude and cannot be
mapped. Mixing the two introduces a domain shift between sensors and renderings, which
must be stated on the Model Card rather than glossed over.

**Decision point: hour 8 of Phase 1.** Not later.
