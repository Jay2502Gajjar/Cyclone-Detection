"""
Download IBTrACS data from NOAA NCEI.

Downloads the North Indian Ocean basin CSV (default ~5 MB) and saves
the untouched source file under data/raw/ibtracs/.

Usage:
    python scripts/download_ibtracs.py
    python scripts/download_ibtracs.py --basin ALL  # ~200 MB global dataset

This script never overwrites processed data automatically.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config" / "sources.yaml"
_RAW_DIR = _PROJECT_ROOT / "data" / "raw" / "ibtracs"


def load_config() -> dict:
    """Load data source configuration."""
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def download_ibtracs(basin: str = "NI") -> Path:
    """
    Download IBTrACS CSV for the specified basin.

    Args:
        basin: Basin code ("NI" for North Indian Ocean, "ALL" for global).

    Returns:
        Path to the downloaded file.

    Raises:
        SystemExit on failure.
    """
    config = load_config()
    ibtracs_cfg = config["ibtracs"]

    basin_upper = basin.upper()
    if basin_upper not in ibtracs_cfg["basins"]:
        logger.error("Unknown basin: %s. Available: %s",
                     basin, list(ibtracs_cfg["basins"].keys()))
        sys.exit(1)

    basin_info = ibtracs_cfg["basins"][basin_upper]
    filename = basin_info["filename"]
    url = f"{ibtracs_cfg['base_url']}/{filename}"

    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _RAW_DIR / filename

    if output_path.exists():
        logger.info("File already exists: %s", output_path)
        logger.info("To re-download, delete it first.")
        return output_path

    logger.info("Downloading IBTrACS %s basin from %s", basin_upper, url)
    logger.info("Expected size: ~%s MB", basin_info["approximate_size_mb"])

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_bytes = 0
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total_bytes += len(chunk)

        logger.info("Downloaded %s bytes to %s", f"{total_bytes:,}", output_path)

        # Write provenance metadata
        provenance = {
            "source": "NOAA NCEI IBTrACS",
            "source_url": url,
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "basin": basin_upper,
            "filename": filename,
            "size_bytes": total_bytes,
            "data_mode": "real",
        }
        provenance_path = _RAW_DIR / f"{filename}.provenance.yaml"
        with open(provenance_path, "w", encoding="utf-8") as f:
            yaml.dump(provenance, f, default_flow_style=False)
        logger.info("Provenance saved to %s", provenance_path)

        return output_path

    except requests.exceptions.ConnectionError:
        logger.error("Connection failed. Check your internet connection.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        logger.error("Download timed out after 60 seconds.")
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Download failed: %s", exc)
        # Clean up partial download
        if output_path.exists():
            output_path.unlink()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Download IBTrACS data from NOAA")
    parser.add_argument(
        "--basin", default="NI",
        help="Basin code: NI (North Indian, ~5MB) or ALL (global, ~200MB). Default: NI",
    )
    args = parser.parse_args()
    download_ibtracs(args.basin)


if __name__ == "__main__":
    main()
