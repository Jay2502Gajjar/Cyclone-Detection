"""
Satellite image metadata catalog and utilities.

Manages the metadata catalog for satellite images used in cyclone
detection/classification. Supports:
  1. Real satellite imagery from NASA IMPACT / NOAA GOES (data/processed/satellite/)
  2. Bundled demo placeholder imagery (data/demo/images/)

NOTE: This module does NOT train any ML model. It prepares and
catalogs imagery data for consumption by the ML developer.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import DataMode, SatelliteImage, SourceInfo

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent
_DEMO_IMAGES_DIR = _PROJECT_ROOT / "data" / "demo" / "images"
_DEMO_CATALOG_PATH = _DEMO_IMAGES_DIR / "catalog.json"

_REAL_IMAGES_DIR = _PROJECT_ROOT / "data" / "processed" / "satellite"
_REAL_CATALOG_PATH = _REAL_IMAGES_DIR / "catalog.json"


class SatelliteCatalog:
    """
    In-memory catalog of satellite image metadata.

    Supports loading:
      - 'real': Real NASA IMPACT satellite observations (366x366 infrared GOES)
      - 'demo': Bundled synthetic placeholder images
      - 'auto': Loads real catalog if present, falls back to demo
    """

    def __init__(
        self,
        images_dir: Optional[Path] = None,
        catalog_path: Optional[Path] = None,
    ):
        self._images_dir = images_dir
        self._catalog_path = catalog_path
        self._images: Dict[str, SatelliteImage] = {}
        self._loaded = False
        self._is_real_data = False

    def load(self, catalog_type: str = "auto") -> bool:
        """
        Load satellite catalog from disk.

        Args:
            catalog_type: 'auto' (prefers real if exists), 'real', or 'demo'.

        Returns:
            True if loaded successfully, False otherwise.
        """
        # Determine paths if not explicitly provided
        if self._catalog_path:
            target_path = self._catalog_path
        elif catalog_type == "real":
            target_path = _REAL_CATALOG_PATH
        elif catalog_type == "demo":
            target_path = _DEMO_CATALOG_PATH
        else:  # 'auto'
            target_path = _REAL_CATALOG_PATH if _REAL_CATALOG_PATH.exists() else _DEMO_CATALOG_PATH

        if not target_path.exists():
            logger.warning("Satellite catalog not found: %s", target_path)
            return False

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                entries = json.load(f)

            self._images = {}
            for entry in entries:
                img = SatelliteImage(**entry)
                self._images[img.image_id] = img

            self._loaded = len(self._images) > 0
            self._is_real_data = "processed" in str(target_path) or any(
                img.source != "demo" for img in self._images.values()
            )
            logger.info(
                "Loaded %d satellite image entries from %s (real=%s)",
                len(self._images),
                target_path.name,
                self._is_real_data,
            )
            return self._loaded

        except Exception as exc:
            logger.error("Failed to load satellite catalog: %s", exc)
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def is_real(self) -> bool:
        return self._is_real_data

    def get_image(self, image_id: str) -> Optional[SatelliteImage]:
        """Get satellite image metadata by ID."""
        return self._images.get(image_id)

    def get_images_for_cyclone(self, cyclone_id: str) -> List[SatelliteImage]:
        """Get all satellite images associated with a cyclone."""
        return [
            img for img in self._images.values()
            if img.cyclone_id == cyclone_id
        ]

    def list_images(
        self,
        image_type: Optional[str] = None,
        is_cyclone: Optional[bool] = None,
        limit: int = 500,
    ) -> List[SatelliteImage]:
        """List images with optional filtering."""
        results = list(self._images.values())

        if image_type:
            results = [i for i in results if i.image_type == image_type]
        if is_cyclone is not None:
            results = [i for i in results if i.is_cyclone == is_cyclone]

        return results[:limit]

    def get_image_path(self, image_id: str) -> Optional[Path]:
        """Resolve the absolute filesystem path for a satellite image."""
        img = self._images.get(image_id)
        if img is None:
            return None

        # 1. Try relative to project root (e.g. data/processed/satellite/images/...)
        path = _PROJECT_ROOT / img.storage_path
        if path.exists():
            return path

        # 2. Try relative to images_dir if custom provided
        if self._images_dir:
            path = self._images_dir / Path(img.storage_path).name
            if path.exists():
                return path

        return None

    def get_source_info(self) -> SourceInfo:
        """Return provenance info for the loaded satellite catalog."""
        if self._is_real_data:
            return SourceInfo(
                mode=DataMode.REAL,
                provider="NASA IMPACT / NOAA GOES",
                source_url="https://data.source.coop/nasa/tropical-storm-competition/",
                processing_script="scripts/download_satellite_data.py",
                processing_version="1.0.0",
            )
        return SourceInfo(
            mode=DataMode.DEMO,
            provider="CycloVision Demo",
            processing_script="scripts/prepare_satellite_data.py",
            processing_version="0.1.0",
        )
