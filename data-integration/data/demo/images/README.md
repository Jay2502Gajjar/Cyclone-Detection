# Satellite Image Dataset

## ⚠️ Demo Images

The images in this directory are **synthetic demo placeholders**.
They are NOT real satellite data and should NOT be used for scientific analysis.

## Obtaining Real Satellite Data

### ISRO MOSDAC (recommended for North Indian Ocean)
1. Register at https://mosdac.gov.in/
2. Navigate to Data → Satellite → INSAT-3D
3. Download TIR1 (thermal IR), VIS, or WV products
4. Place images in `cyclone/` or `non_cyclone/` as appropriate

### NOAA CLASS
1. Visit https://www.avl.class.noaa.gov/
2. Search for GOES imagery
3. Download and convert to PNG/JPEG

## Directory Structure

```
images/
  cyclone/        — Images containing cyclones
  non_cyclone/    — Images without cyclones
  catalog.json    — Metadata for all images
```

## After Adding Real Images

Run `python scripts/prepare_satellite_data.py` to regenerate the catalog.
