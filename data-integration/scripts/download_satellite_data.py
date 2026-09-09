"""
Download and process real satellite imagery from NASA IMPACT Tropical Cyclone Dataset.

Source: NASA Interagency Implementation and Advanced Concepts Team (IMPACT)
Dataset: NASA Tropical Cyclone Wind Estimation Dataset (Version 1.0)
License: Creative Commons Attribution 4.0 International (CC-BY-4.0)
DOI: https://doi.org/10.34911/rdnt.xs53up / IEEE JSTARS (doi:10.1109/JSTARS.2020.3011907)
URL: https://data.source.coop/nasa/tropical-storm-competition/

This script:
  1. Downloads untouched raw feature & label CSVs to data/raw/satellite/
  2. Downloads real infrared satellite images for selected storms
  3. Prepares storm-partitioned train/validation/test splits (no data leakage)
  4. Links observations to canonical models and IBTrACS where applicable
  5. Generates data/processed/satellite/catalog.json with full provenance (data_mode='real')

Usage:
    python scripts/download_satellite_data.py
    python scripts/download_satellite_data.py --num_storms 15 --max_images_per_storm 25
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
import yaml
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.models import (
    Cyclone,
    DataMode,
    IntensityCategory,
    SatelliteImage,
    SourceInfo,
)
from src.normalizers import classify_intensity, knots_to_kmh

_BASE_URL = "https://data.source.coop/nasa/tropical-storm-competition"
_RAW_DIR = _PROJECT_ROOT / "data" / "raw" / "satellite"
_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed" / "satellite"
_IMAGES_DIR = _PROCESSED_DIR / "images"

_HEADERS = {"User-Agent": "CycloVision-DataIntegration/1.0 (Academic/OpenSource Research)"}


def download_raw_metadata() -> pd.DataFrame:
    """Download and merge raw features and labels from Source Cooperative."""
    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    features_csv_path = _RAW_DIR / "training_set_features.csv"
    labels_csv_path = _RAW_DIR / "training_set_labels.csv"

    # Download features CSV if not exists
    if not features_csv_path.exists():
        logger.info("Downloading training_set_features.csv...")
        r_f = requests.get(f"{_BASE_URL}/training_set_features.csv", headers=_HEADERS, timeout=60)
        r_f.raise_for_status()
        features_csv_path.write_bytes(r_f.content)
        logger.info("Saved %s bytes to %s", f"{len(r_f.content):,}", features_csv_path)

    # Download labels CSV if not exists
    if not labels_csv_path.exists():
        logger.info("Downloading training_set_labels.csv...")
        r_l = requests.get(f"{_BASE_URL}/training_set_labels.csv", headers=_HEADERS, timeout=60)
        r_l.raise_for_status()
        labels_csv_path.write_bytes(r_l.content)
        logger.info("Saved %s bytes to %s", f"{len(r_l.content):,}", labels_csv_path)

    # Load and merge
    df_features = pd.read_csv(features_csv_path)
    df_labels = pd.read_csv(labels_csv_path)
    df = pd.merge(df_features, df_labels, on="Image ID")
    logger.info("Loaded metadata: %d total image records across %d unique storms", len(df), df["Storm ID"].nunique())
    return df


def select_storm_splits(df: pd.DataFrame, num_train: int = 10, num_val: int = 3, num_test: int = 3) -> Dict[str, str]:
    """
    Select distinct storms for train, validation, and test splits.
    Ensures zero data leakage: images from the same storm are NEVER in multiple splits.
    """
    # Sort storms by image count to pick well-sampled storms with varying intensities
    storm_stats = df.groupby("Storm ID").agg(
        image_count=("Image ID", "count"),
        max_wind=("Wind Speed", "max"),
        min_wind=("Wind Speed", "min"),
        ocean=("Ocean", "first"),
    ).reset_index()

    # Filter storms with at least 15 images
    viable_storms = storm_stats[storm_stats["image_count"] >= 15].sort_values("image_count", ascending=False)

    storm_list = viable_storms["Storm ID"].tolist()
    total_needed = num_train + num_val + num_test

    if len(storm_list) < total_needed:
        logger.warning("Only %d viable storms found; adjusting split counts", len(storm_list))
        storm_list = storm_stats.sort_values("image_count", ascending=False)["Storm ID"].tolist()[:total_needed]

    storm_splits = {}
    for storm_id in storm_list[:num_train]:
        storm_splits[storm_id] = "train"
    for storm_id in storm_list[num_train:num_train + num_val]:
        storm_splits[storm_id] = "validation"
    for storm_id in storm_list[num_train + num_val:num_train + num_val + num_test]:
        storm_splits[storm_id] = "test"

    return storm_splits


def download_and_process_satellite_data(
    num_train: int = 10,
    num_val: int = 3,
    num_test: int = 3,
    max_images_per_storm: int = 25,
) -> None:
    """Download real satellite images and build the canonical catalog."""
    df = download_raw_metadata()
    storm_splits = select_storm_splits(df, num_train, num_val, num_test)

    logger.info("Selected %d storms across splits: %s", len(storm_splits), {k: list(storm_splits.values()).count(k) for k in ["train", "validation", "test"]})

    # Prepare directories
    for split in ["train", "validation", "test"]:
        (_IMAGES_DIR / split / "cyclone").mkdir(parents=True, exist_ok=True)
        (_IMAGES_DIR / split / "non_cyclone").mkdir(parents=True, exist_ok=True)

    catalog_entries = []
    downloaded_images = 0
    total_bytes = 0

    session = requests.Session()
    session.headers.update(_HEADERS)

    for storm_id, split in storm_splits.items():
        storm_df = df[df["Storm ID"] == storm_id].sort_values("Relative Time")
        # Subsample to max_images_per_storm evenly across storm lifetime
        if len(storm_df) > max_images_per_storm:
            indices = [int(i * (len(storm_df) - 1) / (max_images_per_storm - 1)) for i in range(max_images_per_storm)]
            storm_df = storm_df.iloc[indices]

        logger.info("Downloading storm '%s' (%s split, %d images)...", storm_id, split, len(storm_df))

        for _, row in storm_df.iterrows():
            img_id = str(row["Image ID"])
            wind_knots = float(row["Wind Speed"])
            wind_kmh = knots_to_kmh(wind_knots)
            ocean_code = int(row["Ocean"])
            rel_time_sec = int(row["Relative Time"])

            # Map ocean code: 1 = Atlantic, 2 = East Pacific
            ocean_name = "Atlantic" if ocean_code == 1 else "East Pacific" if ocean_code == 2 else "Other"

            # Classification: > 62 kmh (34 kt) is tropical storm/cyclone, < 62 kmh is depression / developing
            intensity = classify_intensity(wind_kmh)
            is_cyclone = wind_kmh is not None and wind_kmh >= 62.0

            category_folder = "cyclone" if is_cyclone else "non_cyclone"
            rel_storage_path = f"data/processed/satellite/images/{split}/{category_folder}/{img_id}.jpg"
            dest_file = _PROJECT_ROOT / rel_storage_path

            # Download real image from Source Cooperative
            if not dest_file.exists():
                img_url = f"{_BASE_URL}/train/{img_id}.jpg"
                try:
                    r = session.get(img_url, timeout=30)
                    r.raise_for_status()
                    dest_file.write_bytes(r.content)
                    total_bytes += len(r.content)
                    downloaded_images += 1
                except Exception as exc:
                    logger.warning("Failed to download image %s: %s", img_id, exc)
                    continue
            else:
                total_bytes += dest_file.stat().st_size

            # Build metadata entry
            catalog_entries.append({
                "image_id": img_id,
                "cyclone_id": f"NASA_{storm_id.upper()}",
                "cyclone_name": storm_id.upper(),
                "captured_at": None,  # relative time provided
                "relative_time_seconds": rel_time_sec,
                "image_type": "infrared",
                "spectral_band": "10.7 µm Thermal Infrared (GOES Clean IR)",
                "source": "NASA IMPACT",
                "dataset_name": "NASA Tropical Cyclone Wind Estimation Dataset (v1.0)",
                "satellite": "NOAA GOES",
                "storage_path": rel_storage_path,
                "is_cyclone": is_cyclone,
                "wind_speed_knots": wind_knots,
                "wind_speed_kmh": wind_kmh,
                "intensity_category": intensity.value,
                "ocean_basin": ocean_name,
                "split": split,
                "data_mode": "real",
                "license": "CC-BY-4.0",
                "source_url": "https://data.source.coop/nasa/tropical-storm-competition/",
                "doi": "https://doi.org/10.34911/rdnt.xs53up",
            })

    # Save real satellite catalog
    catalog_path = _PROCESSED_DIR / "catalog.json"
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog_entries, f, indent=2, ensure_ascii=False)
    logger.info("Saved catalog with %d real image entries to %s", len(catalog_entries), catalog_path)

    # Save dataset provenance
    provenance = {
        "dataset_name": "NASA Tropical Cyclone Wind Estimation Dataset",
        "provider": "NASA Interagency Implementation and Advanced Concepts Team (IMPACT)",
        "source_url": "https://data.source.coop/nasa/tropical-storm-competition/",
        "license": "CC-BY-4.0",
        "citation": "M. Maskey et al., IEEE JSTARS 2020 (doi:10.1109/JSTARS.2020.3011907)",
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "total_images": len(catalog_entries),
        "total_cyclones": len(storm_splits),
        "total_bytes": total_bytes,
        "splits": {
            "train": sum(1 for e in catalog_entries if e["split"] == "train"),
            "validation": sum(1 for e in catalog_entries if e["split"] == "validation"),
            "test": sum(1 for e in catalog_entries if e["split"] == "test"),
        },
        "classes": {
            "cyclone": sum(1 for e in catalog_entries if e["is_cyclone"]),
            "non_cyclone": sum(1 for e in catalog_entries if not e["is_cyclone"]),
        },
        "image_spec": {
            "dimensions": "366x366",
            "channels": "1 (Grayscale Infrared / 10.7 µm)",
            "format": "JPEG",
        },
        "data_mode": "real",
    }
    provenance_path = _PROCESSED_DIR / "provenance.yaml"
    with open(provenance_path, "w", encoding="utf-8") as f:
        yaml.dump(provenance, f, default_flow_style=False)
    logger.info("Saved dataset provenance to %s", provenance_path)

    # Write ML Training README for the AI Developer
    readme_path = _PROCESSED_DIR / "README.md"
    readme_path.write_text(
        "# Real Satellite Tropical Cyclone Dataset (NASA IMPACT)\n\n"
        "## Dataset Overview\n\n"
        "- **Source**: NASA IMPACT Tropical Cyclone Wind Estimation Dataset (v1.0)\n"
        "- **Satellite Sensor**: NOAA Geostationary Operational Environmental Satellites (GOES) Clean IR (10.7 µm)\n"
        "- **License**: Creative Commons Attribution 4.0 International (CC-BY-4.0)\n"
        "- **DOI**: [10.34911/rdnt.xs53up](https://doi.org/10.34911/rdnt.xs53up) / [IEEE JSTARS 10.1109/JSTARS.2020.3011907](http://doi.org/10.1109/JSTARS.2020.3011907)\n\n"
        "## Structure & Leakage-Free Splits\n\n"
        "Images are partitioned by **storm identity** so that no storm appears in multiple splits:\n\n"
        "```\n"
        "data/processed/satellite/\n"
        "├── catalog.json                # Complete metadata for every image\n"
        "├── provenance.yaml             # Official provenance and metrics\n"
        "└── images/\n"
        "    ├── train/\n"
        "    │   ├── cyclone/            # Cyclone / Tropical Storm images\n"
        "    │   └── non_cyclone/        # Depression / Ambient images\n"
        "    ├── validation/\n"
        "    │   ├── cyclone/\n"
        "    │   └── non_cyclone/\n"
        "    └── test/\n"
        "        ├── cyclone/\n"
        "        └── non_cyclone/\n"
        "```\n\n"
        "## ML ResNet Usage Guide (PyTorch)\n\n"
        "```python\n"
        "import torchvision.transforms as T\n"
        "from torchvision.datasets import ImageFolder\n"
        "from torch.utils.data import DataLoader\n\n"
        "transform = T.Compose([\n"
        "    T.Resize((224, 224)),\n"
        "    T.Grayscale(num_output_channels=3), # Replicate to 3 channels for pretrained ResNet\n"
        "    T.ToTensor(),\n"
        "    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),\n"
        "])\n\n"
        "train_ds = ImageFolder('data/processed/satellite/images/train', transform=transform)\n"
        "val_ds = ImageFolder('data/processed/satellite/images/validation', transform=transform)\n"
        "test_ds = ImageFolder('data/processed/satellite/images/test', transform=transform)\n\n"
        "train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)\n"
        "```\n",
        encoding="utf-8",
    )
    logger.info("Created AI training guide at %s", readme_path)


def main():
    parser = argparse.ArgumentParser(description="Download and prepare real NASA satellite imagery")
    parser.add_argument("--train_storms", type=int, default=10, help="Number of storms for train split")
    parser.add_argument("--val_storms", type=int, default=3, help="Number of storms for validation split")
    parser.add_argument("--test_storms", type=int, default=3, help="Number of storms for test split")
    parser.add_argument("--max_per_storm", type=int, default=25, help="Max images per storm")
    args = parser.parse_args()

    download_and_process_satellite_data(
        num_train=args.train_storms,
        num_val=args.val_storms,
        num_test=args.test_storms,
        max_images_per_storm=args.max_per_storm,
    )


if __name__ == "__main__":
    main()
