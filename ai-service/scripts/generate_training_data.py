#!/usr/bin/env python3
"""
Generate Reproducible XGBoost Intensity Training Dataset from IBTrACS.

Usage:
    python scripts/generate_training_data.py
    python scripts/generate_training_data.py --horizon 24
"""

import argparse
import logging
from pathlib import Path
import sys

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.features.intensity_dataset import (
    generate_intensity_dataset,
    save_dataset_artifacts,
    DEFAULT_DATA_DIR,
    DEFAULT_OUTPUT_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate cyclone intensity training dataset.")
    parser.add_argument("--horizon", type=float, default=24.0, help="Forecast horizon lead time in hours (default: 24.0)")
    parser.add_argument("--tolerance", type=float, default=3.0, help="Window tolerance around horizon in hours (default: 3.0)")
    parser.add_argument("--train-year", type=int, default=2013, help="Max season year for training split (default: 2013)")
    parser.add_argument("--val-year", type=int, default=2018, help="Max season year for validation split (default: 2018)")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_DATA_DIR), help="Path to processed IBTrACS data")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Path to output artifacts directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)

    logger.info("Generating intensity dataset: Horizon=%s h (tol=+-%s h)", args.horizon, args.tolerance)
    logger.info("Source data directory: %s", data_dir)
    logger.info("Destination directory: %s", output_dir)

    train_split, val_split, test_split, stats = generate_intensity_dataset(
        observations_path=data_dir / "observations.json",
        cyclones_path=data_dir / "cyclones.json",
        forecast_horizon_hours=args.horizon,
        horizon_tolerance_hours=args.tolerance,
        train_max_year=args.train_year,
        val_max_year=args.val_year,
    )

    save_dataset_artifacts(
        train_split=train_split,
        val_split=val_split,
        test_split=test_split,
        stats=stats,
        output_dir=output_dir,
    )

    logger.info("Dataset generation complete!")
    logger.info("  Train samples: %d (%d cyclones)", len(train_split.y), len(train_split.cyclone_ids))
    logger.info("  Val samples:   %d (%d cyclones)", len(val_split.y), len(val_split.cyclone_ids))
    logger.info("  Test samples:  %d (%d cyclones)", len(test_split.y), len(test_split.cyclone_ids))
    logger.info("  Total samples: %d", stats["sample_counts"]["total"])


if __name__ == "__main__":
    main()
