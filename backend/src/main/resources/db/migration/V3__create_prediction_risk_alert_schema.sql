-- ============================================================
-- 1. ALERTS
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR PRIMARY KEY,
    cyclone_id VARCHAR,
    cyclone_name VARCHAR,
    severity VARCHAR,
    message VARCHAR(2000),
    issued_at TIMESTAMPTZ,
    affected_regions_json VARCHAR(1000)
);

-- ============================================================
-- 2. HISTORICAL CYCLONES
-- ============================================================
CREATE TABLE IF NOT EXISTS historical_cyclones (
    id VARCHAR PRIMARY KEY,
    name VARCHAR,
    season_year INTEGER,
    final_intensity VARCHAR,
    final_landfall_location VARCHAR,
    impact_summary VARCHAR(2000),
    max_wind_speed_kmh DOUBLE PRECISION,
    min_pressure_hpa DOUBLE PRECISION
);

-- ============================================================
-- 3. PREDICTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS predictions (
    id VARCHAR PRIMARY KEY,
    cyclone_id VARCHAR,
    generated_at TIMESTAMPTZ,
    model_version VARCHAR,
    predicted_intensity_trend VARCHAR,
    confidence_score DOUBLE PRECISION,
    explanation VARCHAR(2000)
);

-- ============================================================
-- 4. PREDICTED TRACK POINTS
-- ============================================================
CREATE TABLE IF NOT EXISTS predicted_track_points (
    id VARCHAR PRIMARY KEY,
    prediction_id VARCHAR REFERENCES predictions(id) ON DELETE CASCADE,
    forecast_hour INTEGER,
    lat DOUBLE PRECISION,
    long_coord DOUBLE PRECISION,
    confidence_radius_km DOUBLE PRECISION
);

-- ============================================================
-- 5. RISK ASSESSMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS risk_assessments (
    id VARCHAR PRIMARY KEY,
    cyclone_id VARCHAR,
    risk_level VARCHAR,
    risk_score DOUBLE PRECISION,
    at_risk_regions_json VARCHAR(1000),
    landfall_probability48h DOUBLE PRECISION,
    computed_at TIMESTAMPTZ
);

-- ============================================================
-- 6. SIMILARITY RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS similarity_results (
    id VARCHAR PRIMARY KEY,
    cyclone_id VARCHAR,
    historical_cyclone_id VARCHAR REFERENCES historical_cyclones(id) ON DELETE CASCADE,
    similarity_score DOUBLE PRECISION,
    rank_order INTEGER
);

-- ============================================================
-- 7. AI ANALYSIS RESULTS
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id VARCHAR PRIMARY KEY,
    cyclone_id VARCHAR,
    model_name VARCHAR,
    cyclone_detected BOOLEAN,
    eye_formed BOOLEAN,
    structure_score DOUBLE PRECISION,
    classification VARCHAR,
    confidence DOUBLE PRECISION,
    gradcam_image_url VARCHAR(1000),
    generated_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_alerts_issued ON alerts(issued_at DESC);
CREATE INDEX IF NOT EXISTS idx_pred_cyclone ON predictions(cyclone_id);
CREATE INDEX IF NOT EXISTS idx_risk_cyclone ON risk_assessments(cyclone_id);
CREATE INDEX IF NOT EXISTS idx_sim_cyclone ON similarity_results(cyclone_id, rank_order ASC);
