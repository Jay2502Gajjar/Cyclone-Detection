"""
Unit tests for unit conversion and normalization in src/normalizers.py.
"""

from datetime import datetime, timezone
import math
from src.normalizers import (
    knots_to_kmh,
    ms_to_kmh,
    mph_to_kmh,
    normalize_pressure,
    normalize_latitude,
    normalize_longitude,
    validate_coordinates,
    parse_timestamp,
    calculate_bearing,
    haversine_km,
    calculate_movement,
    classify_intensity,
    kelvin_to_celsius,
)
from src.models import IntensityCategory


def test_wind_conversions():
    assert knots_to_kmh(100.0) == 185.2
    assert knots_to_kmh(0.0) == 0.0
    assert knots_to_kmh(None) is None
    assert knots_to_kmh(float("nan")) is None

    assert ms_to_kmh(10.0) == 36.0
    assert ms_to_kmh(None) is None

    assert mph_to_kmh(60.0) == 96.6
    assert mph_to_kmh(None) is None


def test_pressure_normalization():
    assert normalize_pressure(1013.25) == 1013.2
    assert normalize_pressure(920) == 920.0
    assert normalize_pressure(750) is None  # Out of range (< 800)
    assert normalize_pressure(1200) is None  # Out of range (> 1100)
    assert normalize_pressure(None) is None
    assert normalize_pressure("invalid") is None


def test_coordinate_normalization():
    assert normalize_latitude(15.54321) == 15.5432
    assert normalize_latitude(-45.0) == -45.0
    assert normalize_latitude(95.0) is None
    assert normalize_latitude(None) is None

    assert normalize_longitude(88.54321) == 88.5432
    # 0..360 normalization (e.g. 270 -> -90)
    assert normalize_longitude(270.0) == -90.0
    assert normalize_longitude(-75.0) == -75.0
    assert normalize_longitude(None) is None


def test_validate_coordinates():
    assert validate_coordinates(15.0, 85.0) is True
    assert validate_coordinates(-90.0, 180.0) is True
    assert validate_coordinates(91.0, 85.0) is False
    assert validate_coordinates(None, 85.0) is False


def test_parse_timestamp():
    dt = parse_timestamp("2020-05-18 06:00:00")
    assert dt == datetime(2020, 5, 18, 6, 0, 0, tzinfo=timezone.utc)

    dt_iso = parse_timestamp("2020-05-18T06:00:00Z")
    assert dt_iso == datetime(2020, 5, 18, 6, 0, 0, tzinfo=timezone.utc)

    assert parse_timestamp(None) is None
    assert parse_timestamp("nan") is None
    assert parse_timestamp("invalid_date_format") is None


def test_bearing_and_haversine():
    # Equator eastwards: (0, 0) to (0, 1) should be 90 deg bearing
    bearing = calculate_bearing(0.0, 0.0, 0.0, 1.0)
    assert bearing == 90.0

    # Distance along equator for 1 deg lon is approx 111.32 km
    dist = haversine_km(0.0, 0.0, 0.0, 1.0)
    assert 111.0 <= dist <= 112.0


def test_calculate_movement():
    t1 = datetime(2020, 5, 18, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2020, 5, 18, 6, 0, tzinfo=timezone.utc)
    direction, speed = calculate_movement(10.0, 80.0, t1, 11.0, 80.0, t2)
    assert direction == 0.0  # Due North
    assert speed is not None and speed > 0

    # Same timestamp should return None
    d, s = calculate_movement(10.0, 80.0, t1, 11.0, 80.0, t1)
    assert d is None and s is None


def test_classify_intensity():
    assert classify_intensity(230) == IntensityCategory.SUPER_CYCLONIC_STORM
    assert classify_intensity(180) == IntensityCategory.EXTREMELY_SEVERE_CYCLONIC_STORM
    assert classify_intensity(130) == IntensityCategory.VERY_SEVERE_CYCLONIC_STORM
    assert classify_intensity(100) == IntensityCategory.SEVERE_CYCLONIC_STORM
    assert classify_intensity(70) == IntensityCategory.CYCLONIC_STORM
    assert classify_intensity(55) == IntensityCategory.DEEP_DEPRESSION
    assert classify_intensity(40) == IntensityCategory.DEPRESSION
    assert classify_intensity(20) == IntensityCategory.UNKNOWN
    assert classify_intensity(None) == IntensityCategory.UNKNOWN


def test_kelvin_to_celsius():
    assert kelvin_to_celsius(300.15) == 27.0
    assert kelvin_to_celsius(273.15) == 0.0
    assert kelvin_to_celsius(None) is None
    assert kelvin_to_celsius(-10) is None
