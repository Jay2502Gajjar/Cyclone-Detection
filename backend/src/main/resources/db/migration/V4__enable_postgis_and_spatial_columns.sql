-- ============================================================================
-- CycloVision Flyway Migration V4
-- Minimal Spatial Foundation (PostGIS + Geography Columns + GIST Indexes)
-- Non-destructive, Additive, and 100% Data-Preserving
-- ============================================================================

-- 1. Enable PostGIS Extension in Supabase PostgreSQL
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Add Geography Point to cyclone_observations
-- Generated automatically from existing longitude and latitude
ALTER TABLE cyclone_observations 
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(Point, 4326) 
GENERATED ALWAYS AS (
    CASE 
        WHEN longitude IS NOT NULL AND latitude IS NOT NULL 
        THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography 
        ELSE NULL 
    END
) STORED;

CREATE INDEX IF NOT EXISTS idx_obs_spatial_location 
ON cyclone_observations USING GIST(location);

-- 3. Add Geography Point to predicted_track_points (Canonical Forecast Trajectory)
-- Generated automatically from long_coord and lat
ALTER TABLE predicted_track_points 
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(Point, 4326) 
GENERATED ALWAYS AS (
    CASE 
        WHEN long_coord IS NOT NULL AND lat IS NOT NULL 
        THEN ST_SetSRID(ST_MakePoint(long_coord, lat), 4326)::geography 
        ELSE NULL 
    END
) STORED;

CREATE INDEX IF NOT EXISTS idx_pred_track_spatial_location 
ON predicted_track_points USING GIST(location);

-- 4. Add Geography Point to weather_data
-- Generated automatically from existing longitude and latitude
ALTER TABLE weather_data 
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(Point, 4326) 
GENERATED ALWAYS AS (
    CASE 
        WHEN longitude IS NOT NULL AND latitude IS NOT NULL 
        THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography 
        ELSE NULL 
    END
) STORED;

CREATE INDEX IF NOT EXISTS idx_weather_spatial_location 
ON weather_data USING GIST(location);
