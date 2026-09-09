"""
Prepare satellite image dataset for cyclone detection.

Creates the directory structure, generates small demo placeholder images
(clearly labeled as synthetic/demo — NOT mislabeled as real satellite data),
and builds a metadata catalog.

For real satellite data, this script documents how to obtain images from:
  - ISRO MOSDAC (INSAT-3D/3DR)
  - NOAA CLASS (GOES)

Usage:
    python scripts/prepare_satellite_data.py

The ML developer will use the prepared dataset for training — this script
does NOT train any model.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_IMAGES_DIR = _PROJECT_ROOT / "data" / "demo" / "images"
_CATALOG_PATH = _IMAGES_DIR / "catalog.json"

# Demo image specifications — small synthetic placeholders
_DEMO_IMAGES = [
    {
        "image_id": "demo_ir_cyclone_01",
        "cyclone_id": "DEMO_AMPHAN_2020",
        "captured_at": "2020-05-18T06:00:00Z",
        "image_type": "infrared",
        "source": "demo",
        "storage_path": "data/demo/images/cyclone/demo_ir_cyclone_01.png",
        "is_cyclone": True,
        "description": "Demo infrared image — synthetic placeholder (NOT real satellite data)",
    },
    {
        "image_id": "demo_vis_cyclone_02",
        "cyclone_id": "DEMO_BIPARJOY_2023",
        "captured_at": "2023-06-12T09:00:00Z",
        "image_type": "visible",
        "source": "demo",
        "storage_path": "data/demo/images/cyclone/demo_vis_cyclone_02.png",
        "is_cyclone": True,
        "description": "Demo visible-band image — synthetic placeholder (NOT real satellite data)",
    },
    {
        "image_id": "demo_wv_cyclone_03",
        "cyclone_id": "DEMO_MOCHA_2023",
        "captured_at": "2023-05-13T12:00:00Z",
        "image_type": "water_vapor",
        "source": "demo",
        "storage_path": "data/demo/images/cyclone/demo_wv_cyclone_03.png",
        "is_cyclone": True,
        "description": "Demo water vapor image — synthetic placeholder (NOT real satellite data)",
    },
    {
        "image_id": "demo_ir_noncyclone_01",
        "cyclone_id": None,
        "captured_at": "2023-01-15T06:00:00Z",
        "image_type": "infrared",
        "source": "demo",
        "storage_path": "data/demo/images/non_cyclone/demo_ir_noncyclone_01.png",
        "is_cyclone": False,
        "description": "Demo non-cyclone infrared image — synthetic placeholder",
    },
    {
        "image_id": "demo_vis_noncyclone_02",
        "cyclone_id": None,
        "captured_at": "2023-03-20T09:00:00Z",
        "image_type": "visible",
        "source": "demo",
        "storage_path": "data/demo/images/non_cyclone/demo_vis_noncyclone_02.png",
        "is_cyclone": False,
        "description": "Demo non-cyclone visible image — synthetic placeholder",
    },
]


def _create_demo_image(path: Path, image_type: str, is_cyclone: bool) -> None:
    """
    Create a small synthetic demo image.

    These are simple gradient images to serve as structural placeholders.
    They are clearly NOT real satellite data.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed — creating empty placeholder file at %s", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return

    size = (128, 128)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Color schemes per image type
    if image_type == "infrared":
        base_color = (20, 20, 80) if is_cyclone else (60, 60, 100)
    elif image_type == "water_vapor":
        base_color = (10, 50, 10) if is_cyclone else (40, 80, 40)
    else:  # visible
        base_color = (100, 100, 100) if is_cyclone else (150, 150, 150)

    img = Image.new("RGB", size, base_color)
    draw = ImageDraw.Draw(img)

    # Draw a simple spiral pattern for cyclone images
    if is_cyclone:
        cx, cy = 64, 64
        import math
        for t in range(0, 360 * 3, 2):
            r = t / 30
            x = int(cx + r * math.cos(math.radians(t)))
            y = int(cy + r * math.sin(math.radians(t)))
            if 0 <= x < size[0] and 0 <= y < size[1]:
                draw.point((x, y), fill=(200, 200, 255))

    # Watermark
    draw.text((4, 4), "DEMO", fill=(255, 100, 100))
    draw.text((4, 112), image_type[:3].upper(), fill=(200, 200, 200))

    img.save(path, "PNG")
    logger.info("Created demo image: %s", path)


def prepare_satellite_data() -> None:
    """Prepare the satellite image dataset structure and demo images."""
    logger.info("Preparing satellite image dataset...")

    # Create directory structure
    (_IMAGES_DIR / "cyclone").mkdir(parents=True, exist_ok=True)
    (_IMAGES_DIR / "non_cyclone").mkdir(parents=True, exist_ok=True)

    # Create demo images
    for entry in _DEMO_IMAGES:
        img_path = _PROJECT_ROOT / entry["storage_path"]
        _create_demo_image(img_path, entry["image_type"], entry["is_cyclone"])

    # Write catalog
    catalog_entries = []
    for entry in _DEMO_IMAGES:
        catalog_entries.append({
            "image_id": entry["image_id"],
            "cyclone_id": entry["cyclone_id"],
            "captured_at": entry["captured_at"],
            "image_type": entry["image_type"],
            "source": entry["source"],
            "storage_path": entry["storage_path"],
            "is_cyclone": entry["is_cyclone"],
        })

    with open(_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog_entries, f, indent=2)
    logger.info("Satellite catalog saved to %s (%d entries)", _CATALOG_PATH, len(catalog_entries))

    # Write README for the images directory
    readme_path = _IMAGES_DIR / "README.md"
    readme_path.write_text(
        "# Satellite Image Dataset\n\n"
        "## ⚠️ Demo Images\n\n"
        "The images in this directory are **synthetic demo placeholders**.\n"
        "They are NOT real satellite data and should NOT be used for scientific analysis.\n\n"
        "## Obtaining Real Satellite Data\n\n"
        "### ISRO MOSDAC (recommended for North Indian Ocean)\n"
        "1. Register at https://mosdac.gov.in/\n"
        "2. Navigate to Data → Satellite → INSAT-3D\n"
        "3. Download TIR1 (thermal IR), VIS, or WV products\n"
        "4. Place images in `cyclone/` or `non_cyclone/` as appropriate\n\n"
        "### NOAA CLASS\n"
        "1. Visit https://www.avl.class.noaa.gov/\n"
        "2. Search for GOES imagery\n"
        "3. Download and convert to PNG/JPEG\n\n"
        "## Directory Structure\n\n"
        "```\n"
        "images/\n"
        "  cyclone/        — Images containing cyclones\n"
        "  non_cyclone/    — Images without cyclones\n"
        "  catalog.json    — Metadata for all images\n"
        "```\n\n"
        "## After Adding Real Images\n\n"
        "Run `python scripts/prepare_satellite_data.py` to regenerate the catalog.\n",
        encoding="utf-8",
    )

    logger.info("Satellite data preparation complete.")
    logger.info(
        "NOTE: These are demo placeholders. See %s for instructions on obtaining real data.",
        readme_path,
    )


if __name__ == "__main__":
    prepare_satellite_data()
