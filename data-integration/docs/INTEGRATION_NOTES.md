# CycloVision — Future Integration Notes

This document identifies the prospective changes, database schemas, cron schedules, and architectural adjustments required when the project team decides to merge the `data-integration` module into the core application stack.

---

## 1. Database Schema Migrations (Flyway / PostgreSQL)

When integrating into Spring Boot, the following Flyway migration (`V2__create_data_integration_tables.sql`) can be added to `backend/src/main/resources/db/migration/`:

```sql
-- Cyclones table
CREATE TABLE IF NOT EXISTS cyclones (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(100) NOT NULL DEFAULT 'UNNAMED',
    basin VARCHAR(10) NOT NULL DEFAULT 'NI',
    season_year INT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'historical',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Observations track table
CREATE TABLE IF NOT EXISTS observations (
    id BIGSERIAL PRIMARY KEY,
    cyclone_id VARCHAR(64) NOT NULL REFERENCES cyclones(id) ON DELETE CASCADE,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    latitude NUMERIC(7, 4) NOT NULL,
    longitude NUMERIC(7, 4) NOT NULL,
    wind_speed_kmh NUMERIC(6, 2),
    pressure_hpa NUMERIC(6, 2),
    movement_direction_deg NUMERIC(5, 2),
    movement_speed_kmh NUMERIC(6, 2),
    intensity_category VARCHAR(64) NOT NULL DEFAULT 'Unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cyclone_observation UNIQUE (cyclone_id, observed_at)
);

CREATE INDEX idx_observations_cyclone_time ON observations(cyclone_id, observed_at DESC);
CREATE INDEX idx_observations_lat_lon ON observations(latitude, longitude);

-- Weather snapshots
CREATE TABLE IF NOT EXISTS weather_readings (
    id BIGSERIAL PRIMARY KEY,
    latitude NUMERIC(7, 4) NOT NULL,
    longitude NUMERIC(7, 4) NOT NULL,
    wind_speed_kmh NUMERIC(6, 2),
    pressure_hpa NUMERIC(6, 2),
    temperature_c NUMERIC(5, 2),
    sea_surface_temp_c NUMERIC(5, 2),
    source VARCHAR(64) NOT NULL DEFAULT 'openweather',
    observed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Ingestion Pipeline & Scheduled Sync

For active hurricane/cyclone season monitoring:
1. **Cron Job Schedule**:
   - Every 3 hours: Poll NOAA / IMD RSS/bulletins for active North Indian Ocean depressions.
   - Every 1 hour: Fetch OpenWeather conditions for active coordinates.
2. **Spring Boot Integration**:
   - Create `@Scheduled(fixedRate = 10800000)` runner in a new `DataIngestionScheduler.java` service.
   - Run Python ingestion script via container subprocess or consume the REST API `http://data-integration:8001`.

---

## 3. Docker Compose Unification

When combining all microservices into root `docker-compose.yml`:
```yaml
  data-integration:
    build:
      context: ./data-integration
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    environment:
      - DEMO_MODE=${DEMO_MODE:-true}
      - OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY:-}
      - DATA_API_PORT=8001
    volumes:
      - ./data-integration/data:/app/data
    restart: unless-stopped
```

---

## 4. Environment Variables Overview

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `DEMO_MODE` | `true` | When `true`, all requests use bundled offline scenarios. Set to `false` for live NOAA/OpenWeather ingestion. |
| `OPENWEATHER_API_KEY` | `""` | API key for live OpenWeather API queries. |
| `REQUEST_TIMEOUT_SECONDS` | `3` | Max HTTP timeout for upstream weather API queries. |
| `DATA_API_PORT` | `8001` | Listening port for standalone FastAPI service. |
