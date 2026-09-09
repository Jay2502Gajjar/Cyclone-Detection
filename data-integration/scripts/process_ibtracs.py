"""
Process raw IBTrACS CSV into normalized JSON records.

Reads the raw IBTrACS CSV downloaded by download_ibtracs.py, normalizes
column names, units, coordinates, timestamps, calculates derived fields,
and outputs clean JSON files under data/processed/ibtracs/.

The raw CSV is NEVER modified.

Usage:
    python scripts/process_ibtracs.py
    python scripts/process_ibtracs.py --input data/raw/ibtracs/ibtracs.NI.list.v04r01.csv

Output:
    data/processed/ibtracs/cyclones.json     — cyclone metadata
    data/processed/ibtracs/observations.json — individual observations
    data/processed/ibtracs/provenance.yaml   — processing provenance
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.normalizers import (
    knots_to_kmh,
    normalize_pressure,
    normalize_latitude,
    normalize_longitude,
    parse_timestamp,
    calculate_movement,
    classify_intensity,
)
from src.models import IntensityCategory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_RAW_DIR = _PROJECT_ROOT / "data" / "raw" / "ibtracs"
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed" / "ibtracs"
_DEFAULT_INPUT = _RAW_DIR / "ibtracs.NI.list.v04r01.csv"


def _safe_float(val) -> Optional[float]:
    """Safely convert a value to float, returning None for invalid values."""
    if val is None:
        return None
    try:
        result = float(val)
        if np.isnan(result) or np.isinf(result):
            return None
        return result
    except (TypeError, ValueError):
        return None


def process_ibtracs(input_path: Path) -> None:
    """
    Process a raw IBTrACS CSV into normalized JSON records.

    Args:
        input_path: Path to the raw IBTrACS CSV file.
    """
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        logger.info("Run 'python scripts/download_ibtracs.py' first.")
        sys.exit(1)

    logger.info("Reading raw IBTrACS data from %s", input_path)

    # IBTrACS CSVs have a header row and a units row — skip the units row
    try:
        df = pd.read_csv(
            input_path,
            skiprows=[1],  # Skip the units row
            low_memory=False,
            na_values=[" ", "", "nan", "NaN"],
        )
    except Exception as exc:
        logger.error("Failed to read CSV: %s", exc)
        sys.exit(1)

    logger.info("Raw records: %d rows, %d columns", len(df), len(df.columns))

    # ── Identify available columns ────────────────────────────────────
    # IBTrACS column names vary slightly by version.
    # We look for the most common column names.
    col_map = {
        "SID": _find_column(df, ["SID"]),
        "NAME": _find_column(df, ["NAME"]),
        "BASIN": _find_column(df, ["BASIN"]),
        "SEASON": _find_column(df, ["SEASON"]),
        "ISO_TIME": _find_column(df, ["ISO_TIME"]),
        "LAT": _find_column(df, ["LAT"]),
        "LON": _find_column(df, ["LON"]),
        "WMO_WIND": _find_column(df, ["WMO_WIND", "USA_WIND"]),
        "WMO_PRES": _find_column(df, ["WMO_PRES", "USA_PRES"]),
    }

    missing = [k for k, v in col_map.items() if v is None and k not in ("WMO_WIND", "WMO_PRES")]
    if missing:
        logger.error("Missing required columns: %s", missing)
        logger.info("Available columns: %s", list(df.columns[:30]))
        sys.exit(1)

    # ── Process each row ──────────────────────────────────────────────
    cyclones_dict = {}
    observations = []
    skipped = 0

    for _, row in df.iterrows():
        sid = str(row.get(col_map["SID"], "")).strip()
        if not sid or sid == "nan":
            skipped += 1
            continue

        # Parse timestamp
        observed_at = parse_timestamp(row.get(col_map["ISO_TIME"]))
        if observed_at is None:
            skipped += 1
            continue

        # Normalize coordinates
        lat = normalize_latitude(_safe_float(row.get(col_map["LAT"])))
        lon = normalize_longitude(_safe_float(row.get(col_map["LON"])))
        if lat is None or lon is None:
            skipped += 1
            continue

        # Normalize wind (IBTrACS WMO_WIND is in knots)
        wind_knots = _safe_float(row.get(col_map["WMO_WIND"])) if col_map["WMO_WIND"] else None
        wind_kmh = knots_to_kmh(wind_knots)

        # Normalize pressure
        pres_raw = _safe_float(row.get(col_map["WMO_PRES"])) if col_map["WMO_PRES"] else None
        pressure = normalize_pressure(pres_raw)

        # Classify intensity
        category = classify_intensity(wind_kmh)

        # Build cyclone metadata (first occurrence wins)
        if sid not in cyclones_dict:
            name = str(row.get(col_map["NAME"], "UNNAMED")).strip()
            if name in ("nan", "", "NOT_NAMED", "UNNAMED"):
                name = "UNNAMED"
            basin = str(row.get(col_map["BASIN"], "NI")).strip()
            season = int(_safe_float(row.get(col_map["SEASON"])) or observed_at.year)

            cyclones_dict[sid] = {
                "id": sid,
                "name": name.upper(),
                "basin": basin,
                "season_year": season,
                "status": "historical",
            }

        # Build observation
        observations.append({
            "cyclone_id": sid,
            "observed_at": observed_at.isoformat(),
            "latitude": lat,
            "longitude": lon,
            "wind_speed_kmh": wind_kmh,
            "pressure_hpa": pressure,
            "movement_direction_deg": None,  # Calculated below
            "movement_speed_kmh": None,      # Calculated below
            "intensity_category": category.value,
        })

    logger.info(
        "Parsed %d observations for %d cyclones (%d rows skipped)",
        len(observations), len(cyclones_dict), skipped,
    )

    # ── Calculate movement direction and speed ────────────────────────
    logger.info("Calculating movement vectors...")
    obs_by_cyclone = {}
    for obs in observations:
        cid = obs["cyclone_id"]
        if cid not in obs_by_cyclone:
            obs_by_cyclone[cid] = []
        obs_by_cyclone[cid].append(obs)

    for cid, track in obs_by_cyclone.items():
        # Sort by time
        track.sort(key=lambda o: o["observed_at"])
        for i in range(1, len(track)):
            prev = track[i - 1]
            curr = track[i]
            t1 = parse_timestamp(prev["observed_at"])
            t2 = parse_timestamp(curr["observed_at"])
            if t1 and t2 and prev["latitude"] and curr["latitude"]:
                direction, speed = calculate_movement(
                    prev["latitude"], prev["longitude"], t1,
                    curr["latitude"], curr["longitude"], t2,
                )
                curr["movement_direction_deg"] = direction
                curr["movement_speed_kmh"] = speed

    # ── Save output ───────────────────────────────────────────────────
    _PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    cyclones_list = list(cyclones_dict.values())
    cyclones_path = _PROCESSED_DIR / "cyclones.json"
    with open(cyclones_path, "w", encoding="utf-8") as f:
        json.dump(cyclones_list, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d cyclones to %s", len(cyclones_list), cyclones_path)

    observations_path = _PROCESSED_DIR / "observations.json"
    with open(observations_path, "w", encoding="utf-8") as f:
        json.dump(observations, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d observations to %s", len(observations), observations_path)

    # Provenance
    provenance = {
        "source": "NOAA IBTrACS",
        "source_file": str(input_path.name),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "processing_script": "scripts/process_ibtracs.py",
        "processing_version": "0.1.0",
        "total_cyclones": len(cyclones_list),
        "total_observations": len(observations),
        "skipped_rows": skipped,
        "data_mode": "real",
    }
    provenance_path = _PROCESSED_DIR / "provenance.yaml"
    with open(provenance_path, "w", encoding="utf-8") as f:
        yaml.dump(provenance, f, default_flow_style=False)
    logger.info("Provenance saved to %s", provenance_path)


def _find_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """Find the first matching column name from a list of candidates."""
    for name in candidates:
        if name in df.columns:
            return name
        # Try case-insensitive
        for col in df.columns:
            if col.strip().upper() == name.upper():
                return col
    return None


def main():
    parser = argparse.ArgumentParser(description="Process raw IBTrACS data")
    parser.add_argument(
        "--input",
        type=Path,
        default=_DEFAULT_INPUT,
        help="Path to raw IBTrACS CSV",
    )
    args = parser.parse_args()
    process_ibtracs(args.input)


if __name__ == "__main__":
    main()
