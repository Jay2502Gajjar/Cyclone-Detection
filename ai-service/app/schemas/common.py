from enum import Enum
from pydantic import BaseModel, Field


class Basin(str, Enum):
    NI = "NI"   # North Indian Ocean (Bay of Bengal / Arabian Sea)
    SI = "SI"   # South Indian Ocean
    WP = "WP"   # Western Pacific
    EP = "EP"   # Eastern Pacific
    AL = "AL"   # North Atlantic
    SP = "SP"   # South Pacific
    NA = "NA"   # North Atlantic alias
    SA = "SA"   # South Atlantic


class IntensityCategory(str, Enum):
    DEPRESSION = "Depression"
    DEEP_DEPRESSION = "Deep Depression"
    CYCLONIC_STORM = "Cyclonic Storm"
    SEVERE_CYCLONIC_STORM = "Severe Cyclonic Storm"
    VERY_SEVERE_CYCLONIC_STORM = "Very Severe Cyclonic Storm"
    EXTREMELY_SEVERE_CYCLONIC_STORM = "Extremely Severe Cyclonic Storm"
    SUPER_CYCLONIC_STORM = "Super Cyclonic Storm"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"
    EXTREME = "EXTREME"


class GeoPoint(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
