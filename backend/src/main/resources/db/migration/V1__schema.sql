-- CycloVision schema, spec-1.0.
--
-- Eight tables. storm_frame is the central timeline table: one row per (storm,
-- observation time), carrying observed truth, the satellite frame reference, and the
-- precomputed analysis the scrubber reads. Everything else hangs off it.

CREATE EXTENSION IF NOT EXISTS postgis;

-- ---------------------------------------------------------------------------
-- storm
-- ---------------------------------------------------------------------------
CREATE TABLE storm (
    sid             TEXT PRIMARY KEY,               -- IBTrACS SID, e.g. '2019114N06084'
    name            TEXT        NOT NULL,
    basin           TEXT        NOT NULL,           -- NI | SI | WP | EP | NA | SP
    season_year     INT         NOT NULL,
    start_time      TIMESTAMPTZ NOT NULL,
    end_time        TIMESTAMPTZ NOT NULL,
    peak_vmax_kt    REAL,
    peak_category   TEXT,
    landfall_time   TIMESTAMPTZ,
    landfall_lat    DOUBLE PRECISION,
    landfall_lon    DOUBLE PRECISION,
    landfall_place  TEXT,
    is_demo         BOOLEAN     NOT NULL DEFAULT FALSE,
    split           TEXT        NOT NULL DEFAULT 'test'
                                CHECK (split IN ('train', 'val', 'test')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Invariant I4, enforced by the database rather than by discipline: a storm we
    -- demonstrate on can never be one we trained on. Every verification number the
    -- product reports depends on this holding.
    CONSTRAINT demo_storms_must_be_held_out CHECK (NOT is_demo OR split = 'test')
);

-- ---------------------------------------------------------------------------
-- storm_frame  — the central timeline table
-- ---------------------------------------------------------------------------
CREATE TABLE storm_frame (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sid                  TEXT        NOT NULL REFERENCES storm (sid) ON DELETE CASCADE,
    obs_time             TIMESTAMPTZ NOT NULL,

    -- OBSERVED (IBTrACS best track)
    lat                  DOUBLE PRECISION NOT NULL,
    lon                  DOUBLE PRECISION NOT NULL,
    geom                 GEOGRAPHY(POINT, 4326)
                             GENERATED ALWAYS AS
                             (ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography) STORED,
    vmax_kt              REAL,
    pressure_hpa         REAL,
    category             TEXT,
    translation_speed_kt REAL,
    heading_deg          REAL,
    dist_to_coast_km     REAL,      -- precomputed offline (Natural Earth + shapely)

    -- SATELLITE (nullable: not every track point has a matched frame)
    image_path           TEXT,      -- 8-bit PNG for display
    bt_path              TEXT,      -- raw brightness temperature in Kelvin (.npy);
                                    -- PNG quantisation would corrupt the structural metrics
    image_time           TIMESTAMPTZ,
    image_source         TEXT,      -- 'HURSAT-B1' | 'INSAT-3D'
    gradcam_path         TEXT,

    -- PRECOMPUTED ANALYSIS (invariant I5: the scrubber reads only this)
    analysis_json        JSONB,
    analysis_version     TEXT,

    CONSTRAINT uq_storm_frame UNIQUE (sid, obs_time)
);

-- ---------------------------------------------------------------------------
-- forecast_run  — one row per live forecast invocation
-- ---------------------------------------------------------------------------
CREATE TABLE forecast_run (
    id                    UUID PRIMARY KEY,
    sid                   TEXT        NOT NULL REFERENCES storm (sid) ON DELETE CASCADE,
    issued_for            TIMESTAMPTZ NOT NULL,     -- T, the temporal-mask boundary
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    model_bundle_version  TEXT        NOT NULL,

    delta_vmax_24h_kt     REAL,
    predicted_vmax_24h_kt REAL,
    intensity_trend       TEXT CHECK (intensity_trend IN
                              ('INTENSIFYING', 'WEAKENING', 'STEADY')),
    intensity_confidence  REAL,
    ri_probability        REAL,
    ri_base_rate          REAL,

    structure_json        JSONB,
    vision_json           JSONB,
    shap_json             JSONB,
    analogue_summary_json JSONB,

    risk_score            REAL,
    risk_level            TEXT CHECK (risk_level IN
                              ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
    risk_terms_json       JSONB,

    report_text           TEXT,
    provenance_json       JSONB       NOT NULL,
    degraded              BOOLEAN     NOT NULL DEFAULT FALSE,

    -- Makes a run idempotent, which is what allows a dead AI service to degrade to a
    -- cached answer instead of an error page.
    CONSTRAINT uq_forecast_run UNIQUE (sid, issued_for, model_bundle_version)
);

-- ---------------------------------------------------------------------------
-- forecast_point
-- ---------------------------------------------------------------------------
CREATE TABLE forecast_point (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id              UUID NOT NULL REFERENCES forecast_run (id) ON DELETE CASCADE,
    lead_hours          INT  NOT NULL CHECK (lead_hours IN (12, 24, 48)),
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    -- Empirical percentiles of the track model's own held-out error, not chosen radii.
    cone_radius_p67_km  REAL,
    cone_radius_p90_km  REAL,
    predicted_vmax_kt   REAL,

    CONSTRAINT uq_forecast_point UNIQUE (run_id, lead_hours)
);

-- ---------------------------------------------------------------------------
-- analogue_match  — the analogue ensemble is a second forecast, so outcomes are stored
-- ---------------------------------------------------------------------------
CREATE TABLE analogue_match (
    id                        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id                    UUID NOT NULL REFERENCES forecast_run (id) ON DELETE CASCADE,
    rank                      INT  NOT NULL,
    match_sid                 TEXT NOT NULL REFERENCES storm (sid),
    match_time                TIMESTAMPTZ NOT NULL,
    similarity                REAL NOT NULL,
    outcome_delta_vmax_24h_kt REAL,
    outcome_was_ri            BOOLEAN,
    onward_track_json         JSONB,

    CONSTRAINT uq_analogue_match UNIQUE (run_id, rank)
);

-- ---------------------------------------------------------------------------
-- model_registry  — what produced what; drives the Model Card and provenance
-- ---------------------------------------------------------------------------
CREATE TABLE model_registry (
    id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_key    TEXT NOT NULL,
    version      TEXT NOT NULL,
    provenance   TEXT NOT NULL CHECK (provenance IN
                     ('OBSERVED', 'TRAINED_MODEL', 'DERIVED_MEASUREMENT',
                      'STATISTICAL_BASELINE', 'ANALOGUE_ENSEMBLE', 'RULE_ENGINE',
                      'LLM_NARRATION', 'DEMO_DATA')),
    is_trained   BOOLEAN NOT NULL DEFAULT FALSE,
    trained_at   TIMESTAMPTZ,
    metrics_json JSONB,   -- {metric, value, baseline, baselineValue, n}
    notes        TEXT,

    -- A trained model must say when it was trained and how it scored against a
    -- baseline. Without both, the claim is not auditable.
    CONSTRAINT trained_models_need_evidence
        CHECK (NOT is_trained OR (trained_at IS NOT NULL AND metrics_json IS NOT NULL)),

    CONSTRAINT uq_model_registry UNIQUE (model_key, version)
);

-- ---------------------------------------------------------------------------
-- coastline_segment  — the only genuine PostGIS dependency (landfall proximity)
-- ---------------------------------------------------------------------------
CREATE TABLE coastline_segment (
    id      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country TEXT,
    geom    GEOGRAPHY(LINESTRING, 4326) NOT NULL
);

-- ---------------------------------------------------------------------------
-- demo_scenario  — offline safety net; always served as DEMO_DATA
-- ---------------------------------------------------------------------------
CREATE TABLE demo_scenario (
    id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sid          TEXT NOT NULL,
    issued_for   TIMESTAMPTZ NOT NULL,
    label        TEXT NOT NULL,
    payload_json JSONB NOT NULL,

    CONSTRAINT uq_demo_scenario UNIQUE (sid, issued_for)
);
