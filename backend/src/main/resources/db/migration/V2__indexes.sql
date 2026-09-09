-- Indexes chosen for the two hot paths: the timeline scrubber and forecast cache lookup.

-- The scrubber query: "every frame of this storm, in order".
CREATE INDEX idx_frame_sid_time ON storm_frame (sid, obs_time);

-- Frames that actually have imagery — the CNN training set and the IR overlay.
CREATE INDEX idx_frame_with_image ON storm_frame (sid, obs_time)
    WHERE image_path IS NOT NULL;

-- PostGIS requires a GiST index for any performant spatial query.
CREATE INDEX idx_frame_geom ON storm_frame USING GIST (geom);
CREATE INDEX idx_coastline_geom ON coastline_segment USING GIST (geom);

-- The storm rail lists demo storms first.
CREATE INDEX idx_storm_demo ON storm (is_demo) WHERE is_demo;

-- Forecast cache / fallback lookup.
CREATE INDEX idx_run_sid_issued ON forecast_run (sid, issued_for DESC);

-- Child lookups for a run.
CREATE INDEX idx_point_run ON forecast_point (run_id);
CREATE INDEX idx_analogue_run ON analogue_match (run_id);
