"""
Unit tests for SatelliteCatalog in src/satellite.py.
"""

from pathlib import Path
import pytest
from src.satellite import SatelliteCatalog
from src.models import DataMode


def test_demo_satellite_catalog_load():
    """Verify demo catalog loads 5 demo placeholder images."""
    catalog = SatelliteCatalog()
    assert catalog.load(catalog_type="demo") is True
    assert catalog.is_loaded is True
    assert catalog.is_real is False

    images = catalog.list_images()
    assert len(images) == 5

    # Cyclone vs Non-cyclone filtering
    cyclone_imgs = catalog.list_images(is_cyclone=True)
    assert len(cyclone_imgs) == 3

    non_cyclone_imgs = catalog.list_images(is_cyclone=False)
    assert len(non_cyclone_imgs) == 2

    # Source info
    source_info = catalog.get_source_info()
    assert source_info.mode == DataMode.DEMO
    assert "scripts/prepare_satellite_data.py" in source_info.processing_script


def test_real_satellite_catalog_load():
    """Verify real NASA IMPACT catalog loads real satellite imagery."""
    catalog = SatelliteCatalog()
    assert catalog.load(catalog_type="real") is True
    assert catalog.is_loaded is True
    assert catalog.is_real is True

    # Check total image count
    images = catalog.list_images()
    assert len(images) == 320

    # Cyclone vs Non-cyclone filtering
    cyclone_imgs = catalog.list_images(is_cyclone=True)
    non_cyclone_imgs = catalog.list_images(is_cyclone=False)
    assert len(cyclone_imgs) == 209
    assert len(non_cyclone_imgs) == 111

    # Fetch a specific real image
    sample = images[0]
    img = catalog.get_image(sample.image_id)
    assert img is not None
    assert img.source == "NASA IMPACT"
    assert "images" in img.storage_path

    # Verify physical file existence
    img_path = catalog.get_image_path(sample.image_id)
    assert img_path is not None
    assert img_path.exists()
    assert img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]

    # Source info for real data
    source_info = catalog.get_source_info()
    assert source_info.mode == DataMode.REAL
    assert "NASA IMPACT" in source_info.provider
