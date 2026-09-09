# CycloVision Data Dictionary

This document defines all canonical data structures, fields, units, and validation rules used across the CycloVision Data Integration layer.

---

## 1. Cyclone Metadata (`Cyclone`)

Represents the core identification and lifecycle metadata for a tropical cyclone.

| Field Name | Type | Nullable | Units / Allowed Values | Description |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `string` | No | e.g. `"2020139N11086"`, `"DEMO_MAHA_2019"` | Unique cyclone identifier (IBTrACS SID or DEMO ID). |
| `name` | `string` | No | Default: `"UNNAMED"` | Assigned cyclone name (uppercase). |
| `basin` | `string` | No | `"NI"` (North Indian Ocean), `"SI"`, `"WP"`, etc. | Ocean basin code. |
| `season_year` | `integer` | No | Year (e.g. `2020`, `2024`) | Cyclone season year. |
| `status` | `string` | No | `"active"`, `"historical"`, `"demo"` | Current lifecycle status of the record. |

---

## 2. Cyclone Observation (`Observation`)

A single chronological point-in-time observation along a cyclone's track.

| Field Name | Type | Nullable | Units / Range | Description |
| :--- | :--- | :---: | :--- | :--- |
| `observed_at` | `string` (ISO 8601) | No | UTC (`YYYY-MM-DDTHH:MM:SS+00:00`) | UTC timestamp of observation. |
| `latitude` | `float` | No | Decimal degrees (`-90.0` to `90.0`) | Latitude position. |
| `longitude` | `float` | No | Decimal degrees (`-180.0` to `180.0`) | Longitude position (normalized from 0..360 if needed). |
| `wind_speed_kmh` | `float` | Yes | `km/h` (`≥ 0.0`) | 3-minute or 10-minute sustained maximum wind speed in km/h. |
| `pressure_hpa` | `float` | Yes | `hPa` (`800.0` to `1100.0`) | Central minimum barometric pressure. |
| `movement_direction_deg` | `float` | Yes | Degrees (`0.0` to `360.0`) | Direction towards which cyclone is moving (0° = North). |
| `movement_speed_kmh` | `float` | Yes | `km/h` (`≥ 0.0`) | Forward translational movement speed. |
| `intensity_category` | `string` (Enum) | No | IMD Scale (see section 7) | Official IMD classification based on sustained wind speed. |

---

## 3. Weather Data (`WeatherData`)

Environmental atmospheric readings at or near the cyclone coordinate.

| Field Name | Type | Nullable | Units / Range | Description |
| :--- | :--- | :---: | :--- | :--- |
| `latitude` | `float` | No | Decimal degrees (`-90.0` to `90.0`) | Observation latitude. |
| `longitude` | `float` | No | Decimal degrees (`-180.0` to `180.0`) | Observation longitude. |
| `wind_speed_kmh` | `float` | Yes | `km/h` (`≥ 0.0`) | Ambient wind speed. |
| `pressure_hpa` | `float` | Yes | `hPa` (`800.0` to `1100.0`) | Sea-level pressure. |
| `temperature_c` | `float` | Yes | `°C` | Ambient air temperature (converted from Kelvin). |
| `sea_surface_temp_c` | `float` | Yes | `°C` (Default: `null`) | Sea Surface Temperature. Explicitly `null` unless provided by dedicated ocean model. |
| `observed_at` | `string` (ISO 8601) | Yes | UTC timestamp | Timestamp of meteorological reading. |
| `source` | `string` | No | e.g. `"openweather"`, `"demo"` | Data source provider tag. |

---

## 4. Satellite Imagery Metadata (`SatelliteImage`)

Metadata cataloging remote sensing imagery.

| Field Name | Type | Nullable | Allowed Values | Description |
| :--- | :--- | :---: | :--- | :--- |
| `image_id` | `string` | No | e.g. `"demo_ir_cyclone_01"` | Unique image identifier. |
| `cyclone_id` | `string` | Yes | Cyclone ID or `null` | Associated cyclone ID if image depicts a storm. |
| `captured_at` | `string` (ISO 8601) | Yes | UTC timestamp | Satellite scan timestamp. |
| `image_type` | `string` | No | `"infrared"`, `"visible"`, `"water_vapor"` | Spectral band of imagery. |
| `source` | `string` | No | `"demo"`, `"mosdac"`, `"noaa"` | Imagery provider. |
| `storage_path` | `string` | No | File path | Relative file path in workspace/storage. |
| `is_cyclone` | `boolean` | No | `true`, `false` | Ground truth label (cyclone present vs. non-cyclone). |

---

## 5. Provenance Information (`SourceInfo`)

Lineage tracking attached to every canonical data envelope.

| Field Name | Type | Nullable | Allowed Values | Description |
| :--- | :--- | :---: | :--- | :--- |
| `mode` | `string` (Enum) | No | `"real"`, `"cached"`, `"demo"`, `"synthetic"` | Operational provenance mode. |
| `provider` | `string` | No | e.g. `"NOAA IBTrACS"`, `"OpenWeather"`, `"demo"` | Primary data provider name. |
| `source_url` | `string` | Yes | URL | Remote download URL if applicable. |
| `downloaded_at` | `string` (ISO 8601) | Yes | UTC timestamp | Ingestion timestamp. |
| `processing_script` | `string` | Yes | Script path | Script responsible for normalization. |
| `processing_version` | `string` | Yes | e.g. `"0.1.0"` | Pipeline release version. |

---

## 6. Composite Data Envelope (`DataEnvelope`)

Top-level object returned by the data integration facade and API server.

| Field Name | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `cyclone` | `Cyclone` | Yes | Cyclone core metadata. |
| `observation` | `Observation` | Yes | Latest/current observation record. |
| `weather` | `WeatherData` | No | Live or synthetic weather reading. |
| `satellite` | `SatelliteImage` | No | Associated satellite imagery metadata. |
| `source` | `SourceInfo` | Yes | Complete provenance info. |

---

## 7. IMD Cyclone Intensity Scale Mapping

The India Meteorological Department (IMD) classification criteria implemented in `src/normalizers.py`:

| Category Name | Sustained Wind Speed (km/h) | Sustained Wind Speed (knots) | Typical Central Pressure Deficit |
| :--- | :---: | :---: | :--- |
| **Depression** | `31 – 49 km/h` | `17 – 27 kt` | ~2 – 3 hPa |
| **Deep Depression** | `50 – 61 km/h` | `28 – 33 kt` | ~4 – 6 hPa |
| **Cyclonic Storm** | `62 – 88 km/h` | `34 – 47 kt` | ~7 – 10 hPa |
| **Severe Cyclonic Storm** | `89 – 117 km/h` | `48 – 63 kt` | ~11 – 15 hPa |
| **Very Severe Cyclonic Storm** | `118 – 166 km/h` | `64 – 89 kt` | ~16 – 30 hPa |
| **Extremely Severe Cyclonic Storm** | `167 – 221 km/h` | `90 – 119 kt` | ~31 – 55 hPa |
| **Super Cyclonic Storm** | `≥ 222 km/h` | `≥ 120 kt` | `> 55 hPa` (central < 920 hPa) |
| **Unknown** | `None / < 31 km/h` | `None / < 17 kt` | - |
