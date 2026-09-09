"""
Unit conversion and value normalization utilities.

All external data (IBTrACS, OpenWeather, satellite metadata) passes
through these functions to produce values in canonical units:
  - Wind speed: km/h
  - Pressure: hPa (= millibars)
  - Temperature: °C
  - Coordinates: decimal degrees (lat -90..90, lon -180..180)
  - Timestamps: UTC datetime
"""

from __future__ import annotations

import math
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from .models import IntensityCategory

logger = logging.getLogger(__name__)

# ── Wind Speed Conversion ─────────────────────────────────────────────

_KNOTS_TO_KMH = 1.852
_MS_TO_KMH = 3.6
_MPH_TO_KMH = 1.60934


def knots_to_kmh(knots: Optional[float]) -> Optional[float]:
    """Convert wind speed from knots to km/h."""
    if knots is None or math.isnan(knots):
        return None
    return round(knots * _KNOTS_TO_KMH, 1)


def ms_to_kmh(ms: Optional[float]) -> Optional[float]:
    """Convert wind speed from m/s to km/h."""
    if ms is None or math.isnan(ms):
        return None
    return round(ms * _MS_TO_KMH, 1)


def mph_to_kmh(mph: Optional[float]) -> Optional[float]:
    """Convert wind speed from mph to km/h."""
    if mph is None or math.isnan(mph):
        return None
    return round(mph * _MPH_TO_KMH, 1)


# ── Pressure ──────────────────────────────────────────────────────────

def normalize_pressure(value: Optional[float]) -> Optional[float]:
    """
    Normalize pressure to hPa.

    IBTrACS uses millibars, which are numerically identical to hPa.
    Returns None for missing or unreasonable values.
    """
    if value is None:
        return None
    try:
        val = float(value)
        if math.isnan(val) or val < 800 or val > 1100:
            return None
        return round(val, 1)
    except (TypeError, ValueError):
        return None


# ── Coordinates ───────────────────────────────────────────────────────

def normalize_latitude(lat: Optional[float]) -> Optional[float]:
    """Validate and normalize latitude to -90..90."""
    if lat is None:
        return None
    try:
        val = float(lat)
        if math.isnan(val) or val < -90 or val > 90:
            return None
        return round(val, 4)
    except (TypeError, ValueError):
        return None


def normalize_longitude(lon: Optional[float]) -> Optional[float]:
    """
    Validate and normalize longitude.

    IBTrACS uses 0..360 for some basins. We normalize to -180..180.
    """
    if lon is None:
        return None
    try:
        val = float(lon)
        if math.isnan(val):
            return None
        # Convert 0..360 → -180..180
        if val > 180:
            val = val - 360
        if val < -180 or val > 180:
            return None
        return round(val, 4)
    except (TypeError, ValueError):
        return None


def validate_coordinates(lat: Optional[float], lon: Optional[float]) -> bool:
    """Check whether lat/lon are within valid ranges."""
    if lat is None or lon is None:
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


# ── Timestamps ────────────────────────────────────────────────────────

_IBTRACS_DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M",
    "%Y%m%d%H",
]


def parse_timestamp(raw: Optional[str]) -> Optional[datetime]:
    """
    Parse a timestamp string into a UTC datetime.

    Tries multiple formats commonly found in IBTrACS and weather data.
    """
    if raw is None or str(raw).strip() in ("", "nan", "NaT"):
        return None
    raw_str = str(raw).strip()

    # Try ISO fromisoformat first (fast and supports +00:00 offsets)
    try:
        dt = datetime.fromisoformat(raw_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, AttributeError):
        pass

    for fmt in _IBTRACS_DATE_FORMATS:
        try:
            dt = datetime.strptime(raw_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    logger.warning("Could not parse timestamp: %s", raw_str)
    return None


# ── Movement Calculations ─────────────────────────────────────────────

def calculate_bearing(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate initial bearing (degrees) from point 1 to point 2.

    Uses the forward azimuth formula. Returns 0..360.
    """
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlon_r = math.radians(lon2 - lon1)

    x = math.sin(dlon_r) * math.cos(lat2_r)
    y = (math.cos(lat1_r) * math.sin(lat2_r) -
         math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r))

    bearing = math.degrees(math.atan2(x, y))
    return round(bearing % 360, 1)


def haversine_km(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """Calculate great-circle distance in km between two points."""
    R = 6371.0  # Earth radius in km
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def calculate_movement(
    lat1: float, lon1: float, time1: datetime,
    lat2: float, lon2: float, time2: datetime,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate movement direction (degrees) and speed (km/h)
    between two sequential observations.

    Returns (direction_deg, speed_kmh) or (None, None) if invalid.
    """
    dt_hours = (time2 - time1).total_seconds() / 3600.0
    if dt_hours <= 0:
        return None, None

    direction = calculate_bearing(lat1, lon1, lat2, lon2)
    distance = haversine_km(lat1, lon1, lat2, lon2)
    speed = round(distance / dt_hours, 1)

    return direction, speed


# ── Intensity Classification ──────────────────────────────────────────

_INTENSITY_THRESHOLDS = [
    (222, IntensityCategory.SUPER_CYCLONIC_STORM),
    (167, IntensityCategory.EXTREMELY_SEVERE_CYCLONIC_STORM),
    (118, IntensityCategory.VERY_SEVERE_CYCLONIC_STORM),
    (89,  IntensityCategory.SEVERE_CYCLONIC_STORM),
    (62,  IntensityCategory.CYCLONIC_STORM),
    (50,  IntensityCategory.DEEP_DEPRESSION),
    (31,  IntensityCategory.DEPRESSION),
]


def classify_intensity(wind_speed_kmh: Optional[float]) -> IntensityCategory:
    """Classify cyclone intensity based on sustained wind speed (km/h)."""
    if wind_speed_kmh is None:
        return IntensityCategory.UNKNOWN
    for threshold, category in _INTENSITY_THRESHOLDS:
        if wind_speed_kmh >= threshold:
            return category
    return IntensityCategory.UNKNOWN


# ── Temperature ───────────────────────────────────────────────────────

def kelvin_to_celsius(kelvin: Optional[float]) -> Optional[float]:
    """Convert Kelvin to Celsius."""
    if kelvin is None:
        return None
    try:
        val = float(kelvin)
        if math.isnan(val) or val < 0:
            return None
        return round(val - 273.15, 1)
    except (TypeError, ValueError):
        return None
