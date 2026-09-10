from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.features.feature_extractor import (
    FEATURE_NAMES,
    extract_features_at_time_t,
    feature_dict_to_vector,
)

logger = logging.getLogger(__name__)

# Default source directories
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data-integration" / "data" / "processed" / "ibtracs"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "training"


@dataclass
class DatasetSplit:
    name: str
    X: np.ndarray
    y: np.ndarray
    cyclone_ids: List[str]
    sample_metadata: List[Dict[str, Any]]


def parse_iso_time(timestamp_str: str) -> datetime:
    """Parses ISO timestamp string to datetime object."""
    clean_str = timestamp_str.replace("Z", "+00:00")
    # Some timestamps might not have timezone, handle consistently
    dt = datetime.fromisoformat(clean_str)
    return dt


def generate_intensity_dataset(
    observations_path: Optional[Path] = None,
    cyclones_path: Optional[Path] = None,
    forecast_horizon_hours: float = 24.0,
    horizon_tolerance_hours: float = 3.0,
    train_max_year: int = 2013,
    val_max_year: int = 2018,
) -> Tuple[DatasetSplit, DatasetSplit, DatasetSplit, Dict[str, Any]]:
    """
    Builds the cyclone intensity prediction dataset from real IBTrACS observations.

    Guarantees:
    1. Zero Future Leakage: Features at time t are strictly built from observations at or before t.
    2. Zero Cyclone Overlap: Train, Validation, and Test sets are split strictly by cyclone identity and season year.
    3. No Synthetic/Fabricated Values: Only genuine historical observations from the same storm are paired.

    Returns:
        (train_split, val_split, test_split, statistics_dict)
    """
    obs_file = observations_path or (DEFAULT_DATA_DIR / "observations.json")
    cyc_file = cyclones_path or (DEFAULT_DATA_DIR / "cyclones.json")

    if not obs_file.exists():
        raise FileNotFoundError(f"Observations file not found at: {obs_file}")
    if not cyc_file.exists():
        raise FileNotFoundError(f"Cyclones file not found at: {cyc_file}")

    with open(obs_file, "r", encoding="utf-8") as f:
        raw_obs: List[Dict[str, Any]] = json.load(f)

    with open(cyc_file, "r", encoding="utf-8") as f:
        raw_cycs: List[Dict[str, Any]] = json.load(f)

    cyclone_metadata = {c["id"]: c for c in raw_cycs}

    # Group observations by cyclone_id
    by_cyclone: Dict[str, List[Dict[str, Any]]] = {}
    for o in raw_obs:
        cid = o["cyclone_id"]
        if cid not in by_cyclone:
            by_cyclone[cid] = []
        by_cyclone[cid].append(o)

    # Sort each cyclone's track chronologically and pre-parse datetime
    for cid, track in by_cyclone.items():
        for o in track:
            o["_parsed_time"] = parse_iso_time(o["observed_at"])
        track.sort(key=lambda o: o["_parsed_time"])

    # Extract supervised samples (t -> t + horizon)
    train_samples: List[Tuple[np.ndarray, float, str, Dict[str, Any]]] = []
    val_samples: List[Tuple[np.ndarray, float, str, Dict[str, Any]]] = []
    test_samples: List[Tuple[np.ndarray, float, str, Dict[str, Any]]] = []

    train_cyclones = set()
    val_cyclones = set()
    test_cyclones = set()

    total_valid_obs_with_wind = 0

    for cid, track in by_cyclone.items():
        season_year = cyclone_metadata.get(cid, {}).get("season_year")
        if season_year is None and track:
            season_year = track[0]["_parsed_time"].year

        # Determine split for this entire cyclone
        if season_year <= train_max_year:
            target_split = "train"
        elif season_year <= val_max_year:
            target_split = "val"
        else:
            target_split = "test"

        for i in range(len(track)):
            curr = track[i]
            if curr.get("wind_speed_kmh") is None:
                continue

            total_valid_obs_with_wind += 1
            t_curr = curr["_parsed_time"]

            # Search forward in time strictly within the same cyclone
            target_wind_kts: Optional[float] = None
            target_time: Optional[datetime] = None
            best_dt_diff = float("inf")

            for j in range(i + 1, len(track)):
                fut = track[j]
                t_fut = fut["_parsed_time"]
                dt_hours = (t_fut - t_curr).total_seconds() / 3600.0

                if dt_hours > forecast_horizon_hours + horizon_tolerance_hours:
                    break

                if abs(dt_hours - forecast_horizon_hours) <= horizon_tolerance_hours:
                    if fut.get("wind_speed_kmh") is not None:
                        diff = abs(dt_hours - forecast_horizon_hours)
                        if diff < best_dt_diff:
                            best_dt_diff = diff
                            target_wind_kts = round(float(fut["wind_speed_kmh"]) / 1.852, 2)
                            target_time = t_fut

            if target_wind_kts is None or target_time is None:
                continue

            # NO LEAKAGE: history_obs strictly contains observations prior to index i
            history_obs = track[:i]
            feature_dict = extract_features_at_time_t(curr, history_obs, t_curr)
            feature_vec = feature_dict_to_vector(feature_dict)

            meta = {
                "cyclone_id": cid,
                "season_year": season_year,
                "t_time": t_curr.isoformat(),
                "target_time": target_time.isoformat(),
                "dt_hours": round((target_time - t_curr).total_seconds() / 3600.0, 2),
                "current_wind_kts": feature_dict["current_wind_kts"],
                "target_wind_kts": target_wind_kts,
            }

            sample_tuple = (feature_vec, target_wind_kts, cid, meta)

            if target_split == "train":
                train_samples.append(sample_tuple)
                train_cyclones.add(cid)
            elif target_split == "val":
                val_samples.append(sample_tuple)
                val_cyclones.add(cid)
            else:
                test_samples.append(sample_tuple)
                test_cyclones.add(cid)

    # Verification of zero overlap across cyclone identities
    assert len(train_cyclones & val_cyclones) == 0, f"Leakage detected: {train_cyclones & val_cyclones} overlap train/val!"
    assert len(train_cyclones & test_cyclones) == 0, f"Leakage detected: {train_cyclones & test_cyclones} overlap train/test!"
    assert len(val_cyclones & test_cyclones) == 0, f"Leakage detected: {val_cyclones & test_cyclones} overlap val/test!"

    def _pack_split(name: str, samples: list, cyc_ids: set) -> DatasetSplit:
        if not samples:
            return DatasetSplit(
                name=name,
                X=np.empty((0, len(FEATURE_NAMES)), dtype=np.float32),
                y=np.empty((0,), dtype=np.float32),
                cyclone_ids=[],
                sample_metadata=[]
            )
        X = np.stack([s[0] for s in samples], axis=0).astype(np.float32)
        y = np.array([s[1] for s in samples], dtype=np.float32)
        meta = [s[3] for s in samples]
        return DatasetSplit(
            name=name,
            X=X,
            y=y,
            cyclone_ids=sorted(list(cyc_ids)),
            sample_metadata=meta
        )

    train_split = _pack_split("train", train_samples, train_cyclones)
    val_split = _pack_split("val", val_samples, val_cyclones)
    test_split = _pack_split("test", test_samples, test_cyclones)

    total_samples = len(train_samples) + len(val_samples) + len(test_samples)
    all_targets = [s[1] for s in train_samples + val_samples + test_samples]

    stats = {
        "dataset_name": "IBTrACS_NorthIndianOcean_Intensity",
        "generated_at": datetime.utcnow().isoformat(),
        "total_raw_observations": len(raw_obs),
        "total_unique_cyclones": len(cyclone_metadata),
        "usable_observations_with_wind": total_valid_obs_with_wind,
        "forecast_horizon_hours": forecast_horizon_hours,
        "horizon_tolerance_hours": horizon_tolerance_hours,
        "feature_count": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "split_seasons": {
            "train": f"<= {train_max_year}",
            "validation": f"{train_max_year + 1} - {val_max_year}",
            "test": f">= {val_max_year + 1}"
        },
        "sample_counts": {
            "total": total_samples,
            "train": len(train_split.y),
            "validation": len(val_split.y),
            "test": len(test_split.y),
        },
        "cyclone_counts": {
            "total": len(train_cyclones | val_cyclones | test_cyclones),
            "train": len(train_cyclones),
            "validation": len(val_cyclones),
            "test": len(test_cyclones),
        },
        "target_distribution": {
            "min_kts": float(np.min(all_targets)) if all_targets else 0.0,
            "max_kts": float(np.max(all_targets)) if all_targets else 0.0,
            "mean_kts": float(np.mean(all_targets)) if all_targets else 0.0,
            "median_kts": float(np.median(all_targets)) if all_targets else 0.0,
            "std_kts": float(np.std(all_targets)) if all_targets else 0.0,
        },
        "missingness_handling": {
            "pressure_hpa": "Imputed with standard neutral 1010.0 hPa; accompanied by explicit binary flag pressure_available",
            "lag_6h": "Imputed with 0.0; accompanied by explicit binary flag lag_6h_available",
            "lag_12h": "Imputed with 0.0",
            "movement": "Imputed with 0.0 when prior track step does not exist (initial observation)",
            "environmental_data": "None fabricated; strictly observational and dynamic track derivation"
        }
    }

    return train_split, val_split, test_split, stats


def save_dataset_artifacts(
    train_split: DatasetSplit,
    val_split: DatasetSplit,
    test_split: DatasetSplit,
    stats: Dict[str, Any],
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Serializes training matrices and schema/manifest artifacts into output_dir.
    """
    out = output_dir or DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    # Save numpy matrices
    np.save(out / "X_train.npy", train_split.X)
    np.save(out / "y_train.npy", train_split.y)
    np.save(out / "X_val.npy", val_split.X)
    np.save(out / "y_val.npy", val_split.y)
    np.save(out / "X_test.npy", test_split.X)
    np.save(out / "y_test.npy", test_split.y)

    # Compute feature ranges on training set for schema documentation
    train_X = train_split.X
    feature_ranges = {}
    for idx, name in enumerate(FEATURE_NAMES):
        col = train_X[:, idx] if len(train_X) > 0 else np.array([0])
        feature_ranges[name] = {
            "index": idx,
            "min": float(np.min(col)),
            "max": float(np.max(col)),
            "mean": round(float(np.mean(col)), 4),
            "std": round(float(np.std(col)), 4),
        }

    feature_schema = {
        "dataset": stats["dataset_name"],
        "forecast_horizon_hours": stats["forecast_horizon_hours"],
        "feature_count": len(FEATURE_NAMES),
        "features": [
            {
                "name": "latitude",
                "unit": "degrees",
                "type": "float32",
                "description": "Storm center latitude (-90 to 90)",
                "train_stats": feature_ranges["latitude"]
            },
            {
                "name": "longitude",
                "unit": "degrees",
                "type": "float32",
                "description": "Storm center longitude (-180 to 180)",
                "train_stats": feature_ranges["longitude"]
            },
            {
                "name": "current_wind_kts",
                "unit": "knots",
                "type": "float32",
                "description": "Maximum sustained surface wind at time t",
                "train_stats": feature_ranges["current_wind_kts"]
            },
            {
                "name": "current_pressure_hpa",
                "unit": "hPa",
                "type": "float32",
                "description": "Central pressure at time t (1010.0 if missing)",
                "train_stats": feature_ranges["current_pressure_hpa"]
            },
            {
                "name": "pressure_available",
                "unit": "binary_flag",
                "type": "float32",
                "description": "1.0 if central pressure was recorded, 0.0 if imputed",
                "train_stats": feature_ranges["pressure_available"]
            },
            {
                "name": "translation_speed_kmh",
                "unit": "km/h",
                "type": "float32",
                "description": "Forward movement speed derived from prior observation",
                "train_stats": feature_ranges["translation_speed_kmh"]
            },
            {
                "name": "translation_heading_deg",
                "unit": "degrees",
                "type": "float32",
                "description": "Forward movement direction from true North (0 to 360)",
                "train_stats": feature_ranges["translation_heading_deg"]
            },
            {
                "name": "coriolis_param",
                "unit": "s^-1",
                "type": "float32",
                "description": "Planetary vorticity (2 * Omega * sin(latitude))",
                "train_stats": feature_ranges["coriolis_param"]
            },
            {
                "name": "lag_6h_wind_change_kts",
                "unit": "knots",
                "type": "float32",
                "description": "Rate of wind speed change over prior 6 hours (V_t - V_t-6h)",
                "train_stats": feature_ranges["lag_6h_wind_change_kts"]
            },
            {
                "name": "lag_6h_available",
                "unit": "binary_flag",
                "type": "float32",
                "description": "1.0 if historical 6h observation exists, 0.0 if missing",
                "train_stats": feature_ranges["lag_6h_available"]
            },
            {
                "name": "lag_6h_lat_change",
                "unit": "degrees",
                "type": "float32",
                "description": "Meridional displacement over prior 6 hours (lat_t - lat_t-6h)",
                "train_stats": feature_ranges["lag_6h_lat_change"]
            },
            {
                "name": "lag_6h_lon_change",
                "unit": "degrees",
                "type": "float32",
                "description": "Zonal displacement over prior 6 hours (lon_t - lon_t-6h)",
                "train_stats": feature_ranges["lag_6h_lon_change"]
            },
            {
                "name": "lag_12h_wind_change_kts",
                "unit": "knots",
                "type": "float32",
                "description": "Rate of wind speed change over prior 12 hours (V_t - V_t-12h)",
                "train_stats": feature_ranges["lag_12h_wind_change_kts"]
            },
            {
                "name": "season_month",
                "unit": "month_number",
                "type": "float32",
                "description": "Calendar month of observation (1 to 12) for seasonal climatology",
                "train_stats": feature_ranges["season_month"]
            },
        ]
    }

    with open(out / "feature_schema.json", "w", encoding="utf-8") as f:
        json.dump(feature_schema, f, indent=2)

    with open(out / "dataset_manifest.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    logger.info("Saved dataset artifacts cleanly to %s", out)
    return out
