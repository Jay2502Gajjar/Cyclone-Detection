"""
Data validation for processed CycloVision datasets.

Validates cyclone observations, track integrity, and data quality.
Produces a structured validation report.

Usage:
    python scripts/validate_data.py
    python scripts/validate_data.py --input data/processed/ibtracs
    python scripts/validate_data.py --demo   # validate demo scenarios
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed" / "ibtracs"
_DEMO_DIR = _PROJECT_ROOT / "data" / "demo" / "scenarios"
_REPORT_DIR = _PROJECT_ROOT / "docs"


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamp string."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def validate_observations(observations: list) -> dict:
    """Validate a list of observation records."""
    stats = {
        "total": len(observations),
        "valid": 0,
        "missing_coordinates": 0,
        "missing_wind": 0,
        "missing_pressure": 0,
        "invalid_timestamps": 0,
        "invalid_coordinates": 0,
        "duplicate_observations": 0,
        "issues": [],
    }

    seen_keys = set()

    for i, obs in enumerate(observations):
        issues_for_row = []

        # Timestamp
        observed_at = _parse_iso(obs.get("observed_at"))
        if observed_at is None:
            stats["invalid_timestamps"] += 1
            issues_for_row.append(f"Row {i}: invalid/missing timestamp")

        # Coordinates
        lat = obs.get("latitude")
        lon = obs.get("longitude")
        if lat is None or lon is None:
            stats["missing_coordinates"] += 1
            issues_for_row.append(f"Row {i}: missing coordinates")
        elif not (-90 <= lat <= 90):
            stats["invalid_coordinates"] += 1
            issues_for_row.append(f"Row {i}: invalid latitude {lat}")
        elif not (-180 <= lon <= 180):
            stats["invalid_coordinates"] += 1
            issues_for_row.append(f"Row {i}: invalid longitude {lon}")

        # Wind
        wind = obs.get("wind_speed_kmh")
        if wind is None:
            stats["missing_wind"] += 1
        elif wind < 0 or wind > 500:
            issues_for_row.append(f"Row {i}: unreasonable wind {wind} km/h")

        # Pressure
        pres = obs.get("pressure_hpa")
        if pres is None:
            stats["missing_pressure"] += 1
        elif pres < 800 or pres > 1100:
            issues_for_row.append(f"Row {i}: unreasonable pressure {pres} hPa")

        # Duplicate detection
        cid = obs.get("cyclone_id", "")
        key = f"{cid}_{obs.get('observed_at')}"
        if key in seen_keys:
            stats["duplicate_observations"] += 1
            issues_for_row.append(f"Row {i}: duplicate observation")
        seen_keys.add(key)

        if not issues_for_row:
            stats["valid"] += 1
        else:
            stats["issues"].extend(issues_for_row)

    return stats


def validate_tracks(observations: list) -> dict:
    """Validate track integrity across cyclone tracks."""
    tracks = {}
    for obs in observations:
        cid = obs.get("cyclone_id", "UNKNOWN")
        if cid not in tracks:
            tracks[cid] = []
        tracks[cid].append(obs)

    stats = {
        "total_tracks": len(tracks),
        "valid_tracks": 0,
        "tracks_with_issues": 0,
        "issues": [],
    }

    for cid, track in tracks.items():
        track_issues = []

        # Check chronological ordering
        times = [_parse_iso(o.get("observed_at")) for o in track]
        valid_times = [t for t in times if t is not None]
        if len(valid_times) >= 2:
            for j in range(1, len(valid_times)):
                if valid_times[j] < valid_times[j - 1]:
                    track_issues.append(f"Track {cid}: non-chronological at position {j}")

        # Check track has at least 2 points
        if len(track) < 2:
            track_issues.append(f"Track {cid}: only {len(track)} point(s)")

        # Check movement calculations
        for obs in track:
            mv_dir = obs.get("movement_direction_deg")
            mv_spd = obs.get("movement_speed_kmh")
            if mv_dir is not None and (mv_dir < 0 or mv_dir > 360):
                track_issues.append(f"Track {cid}: invalid direction {mv_dir}")
            if mv_spd is not None and (mv_spd < 0 or mv_spd > 200):
                track_issues.append(f"Track {cid}: unreasonable movement speed {mv_spd}")

        if track_issues:
            stats["tracks_with_issues"] += 1
            stats["issues"].extend(track_issues[:5])  # Limit per track
        else:
            stats["valid_tracks"] += 1

    return stats


def validate_demo_scenarios(scenarios_dir: Path) -> dict:
    """Validate demo scenario files."""
    stats = {
        "total_scenarios": 0,
        "valid_scenarios": 0,
        "issues": [],
    }

    if not scenarios_dir.exists():
        stats["issues"].append(f"Scenarios directory not found: {scenarios_dir}")
        return stats

    for scenario_dir in sorted(scenarios_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue

        scenario_file = scenario_dir / "scenario.json"
        if not scenario_file.exists():
            stats["issues"].append(f"Missing scenario.json in {scenario_dir.name}")
            continue

        stats["total_scenarios"] += 1

        try:
            with open(scenario_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            issues = []

            # Required fields
            for field in ["scenario_id", "title", "cyclone", "latest_observation"]:
                if field not in data:
                    issues.append(f"{scenario_dir.name}: missing required field '{field}'")

            # Validate cyclone
            cyc = data.get("cyclone", {})
            if not cyc.get("id"):
                issues.append(f"{scenario_dir.name}: cyclone missing 'id'")
            if not cyc.get("name"):
                issues.append(f"{scenario_dir.name}: cyclone missing 'name'")

            # Validate latest observation
            obs = data.get("latest_observation", {})
            if not obs.get("observed_at"):
                issues.append(f"{scenario_dir.name}: observation missing 'observed_at'")
            if obs.get("latitude") is None:
                issues.append(f"{scenario_dir.name}: observation missing 'latitude'")

            # Validate source marking
            source = data.get("source", {})
            if source.get("mode") != "demo":
                issues.append(f"{scenario_dir.name}: source.mode should be 'demo'")

            if not issues:
                stats["valid_scenarios"] += 1
            else:
                stats["issues"].extend(issues)

        except json.JSONDecodeError as exc:
            stats["issues"].append(f"{scenario_dir.name}: invalid JSON — {exc}")
        except Exception as exc:
            stats["issues"].append(f"{scenario_dir.name}: error — {exc}")

    return stats


def validate_satellite_catalog(catalog_path: Path) -> dict:
    """Validate satellite catalog entries and image existence on disk."""
    stats = {
        "total_images": 0,
        "valid_images": 0,
        "missing_files": 0,
        "cyclone_images": 0,
        "non_cyclone_images": 0,
        "issues": [],
    }

    if not catalog_path.exists():
        return stats

    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            entries = json.load(f)

        stats["total_images"] = len(entries)
        for i, entry in enumerate(entries):
            img_id = entry.get("image_id", f"idx_{i}")
            storage_path = entry.get("storage_path", "")
            full_path = _PROJECT_ROOT / storage_path

            if not full_path.exists():
                stats["missing_files"] += 1
                stats["issues"].append(f"Image {img_id}: file not found at {storage_path}")
            else:
                stats["valid_images"] += 1

            if entry.get("is_cyclone"):
                stats["cyclone_images"] += 1
            else:
                stats["non_cyclone_images"] += 1

    except Exception as exc:
        stats["issues"].append(f"Error reading {catalog_path.name}: {exc}")

    return stats


def run_validation(processed_dir: Path, demo_dir: Path) -> str:
    """Run full validation and return a formatted report."""
    report_lines = [
        "=" * 60,
        "CycloVision Data Validation Report",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "=" * 60,
        "",
    ]

    # ── Processed IBTrACS ─────────────────────────────────────────
    obs_file = processed_dir / "observations.json"
    cyc_file = processed_dir / "cyclones.json"

    if obs_file.exists():
        with open(obs_file, "r", encoding="utf-8") as f:
            observations = json.load(f)

        report_lines.append("-- IBTrACS Observations --")
        obs_stats = validate_observations(observations)
        report_lines.append(f"Total observations:      {obs_stats['total']}")
        report_lines.append(f"Valid observations:       {obs_stats['valid']}")
        report_lines.append(f"Missing coordinates:     {obs_stats['missing_coordinates']}")
        report_lines.append(f"Missing wind:            {obs_stats['missing_wind']}")
        report_lines.append(f"Missing pressure:        {obs_stats['missing_pressure']}")
        report_lines.append(f"Invalid timestamps:      {obs_stats['invalid_timestamps']}")
        report_lines.append(f"Invalid coordinates:     {obs_stats['invalid_coordinates']}")
        report_lines.append(f"Duplicate observations:  {obs_stats['duplicate_observations']}")
        obs_pass = obs_stats["valid"] > 0 and obs_stats["invalid_coordinates"] == 0
        report_lines.append(f"Validation status:       {'PASS' if obs_pass else 'FAIL'}")
        if obs_stats["issues"][:10]:
            report_lines.append("")
            report_lines.append("Sample issues:")
            for issue in obs_stats["issues"][:10]:
                report_lines.append(f"  - {issue}")
        report_lines.append("")

        # Track validation
        report_lines.append("-- Track Integrity --")
        track_stats = validate_tracks(observations)
        report_lines.append(f"Total tracks:            {track_stats['total_tracks']}")
        report_lines.append(f"Valid tracks:            {track_stats['valid_tracks']}")
        report_lines.append(f"Tracks with issues:      {track_stats['tracks_with_issues']}")
        track_pass = track_stats["valid_tracks"] > 0
        report_lines.append(f"Validation status:       {'PASS' if track_pass else 'FAIL'}")
        if track_stats["issues"][:10]:
            report_lines.append("")
            report_lines.append("Sample issues:")
            for issue in track_stats["issues"][:10]:
                report_lines.append(f"  - {issue}")
        report_lines.append("")
    else:
        report_lines.append("-- IBTrACS --")
        report_lines.append("No processed observations found. Run process_ibtracs.py first.")
        report_lines.append("")

    if cyc_file.exists():
        with open(cyc_file, "r", encoding="utf-8") as f:
            cyclones = json.load(f)
        report_lines.append(f"Total cyclones:          {len(cyclones)}")
        report_lines.append("")

    # -- Real Satellite Dataset ------------------------------------
    real_sat_catalog = _PROJECT_ROOT / "data" / "processed" / "satellite" / "catalog.json"
    if real_sat_catalog.exists():
        report_lines.append("-- Real Satellite Dataset (NASA IMPACT) --")
        sat_stats = validate_satellite_catalog(real_sat_catalog)
        report_lines.append(f"Total satellite images:  {sat_stats['total_images']}")
        report_lines.append(f"Valid image files:       {sat_stats['valid_images']}")
        report_lines.append(f"Cyclone images:          {sat_stats['cyclone_images']}")
        report_lines.append(f"Non-cyclone images:      {sat_stats['non_cyclone_images']}")
        report_lines.append(f"Missing image files:     {sat_stats['missing_files']}")
        sat_pass = sat_stats["valid_images"] > 0 and sat_stats["missing_files"] == 0
        report_lines.append(f"Validation status:       {'PASS' if sat_pass else 'FAIL'}")
        report_lines.append("")

    # -- Demo Scenarios --------------------------------------------
    report_lines.append("-- Demo Scenarios --")
    demo_stats = validate_demo_scenarios(demo_dir)
    report_lines.append(f"Total scenarios:         {demo_stats['total_scenarios']}")
    report_lines.append(f"Valid scenarios:         {demo_stats['valid_scenarios']}")
    demo_pass = demo_stats["valid_scenarios"] == demo_stats["total_scenarios"]
    report_lines.append(f"Validation status:       {'PASS' if demo_pass else 'FAIL'}")
    if demo_stats["issues"]:
        report_lines.append("")
        report_lines.append("Issues:")
        for issue in demo_stats["issues"]:
            report_lines.append(f"  - {issue}")
    report_lines.append("")

    # -- Summary ---------------------------------------------------
    report_lines.append("=" * 60)
    report_lines.append("OVERALL VALIDATION: " + ("PASS" if demo_pass else "FAIL"))
    report_lines.append("=" * 60)

    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(description="Validate CycloVision datasets")
    parser.add_argument(
        "--input", type=Path, default=_PROCESSED_DIR,
        help="Path to processed IBTrACS directory",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Validate demo scenarios",
    )
    args = parser.parse_args()

    report = run_validation(args.input, _DEMO_DIR)
    print(report)

    # Save report
    _REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = _REPORT_DIR / "validation_report.txt"
    report_path.write_text(report, encoding="utf-8")
    logger.info("Report saved to %s", report_path)


if __name__ == "__main__":
    main()
