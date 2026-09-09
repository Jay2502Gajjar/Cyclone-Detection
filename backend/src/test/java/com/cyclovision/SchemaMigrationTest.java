package com.cyclovision;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

/**
 * Verifies the migrations against real PostgreSQL with PostGIS.
 *
 * <p>Opt-in, because it needs a live database:
 * {@code .\mvnw test "-Dcyclovision.db.it=true"} after {@code docker compose up -d postgres}.
 * H2 cannot stand in — the schema depends on PostGIS geography columns, a generated
 * column, and CHECK constraints that carry two of our architectural invariants.
 */
@SpringBootTest
@EnabledIfSystemProperty(named = "cyclovision.db.it", matches = "true")
class SchemaMigrationTest {

    @Autowired
    private JdbcTemplate jdbc;

    @Test
    @DisplayName("all eight tables exist after migration")
    void migrationsApply() {
        Integer tables = jdbc.queryForObject(
                "SELECT count(*) FROM information_schema.tables "
                        + "WHERE table_schema = 'public' AND table_name IN "
                        + "('storm','storm_frame','forecast_run','forecast_point',"
                        + "'analogue_match','model_registry','coastline_segment',"
                        + "'demo_scenario')",
                Integer.class);
        assertThat(tables).isEqualTo(8);
    }

    @Test
    @DisplayName("PostGIS is enabled and the generated geometry column works")
    void postgisGeneratedColumnWorks() {
        jdbc.update("INSERT INTO storm (sid, name, basin, season_year, start_time, end_time) "
                + "VALUES ('TEST_GEOM','TESTSTORM','NI',2019, now(), now()) "
                + "ON CONFLICT (sid) DO NOTHING");
        jdbc.update("INSERT INTO storm_frame (sid, obs_time, lat, lon) "
                + "VALUES ('TEST_GEOM', now(), 17.2, 85.1) "
                + "ON CONFLICT (sid, obs_time) DO NOTHING");

        Double lat = jdbc.queryForObject(
                "SELECT ST_Y(geom::geometry) FROM storm_frame WHERE sid = 'TEST_GEOM' LIMIT 1",
                Double.class);
        assertThat(lat).isCloseTo(17.2, org.assertj.core.api.Assertions.within(0.0001));

        jdbc.update("DELETE FROM storm WHERE sid = 'TEST_GEOM'");
    }

    @Test
    @DisplayName("invariant I4: the database refuses a demo storm in the training split")
    void demoStormCannotBeInTrainingSplit() {
        assertThatThrownBy(() -> jdbc.update(
                "INSERT INTO storm (sid, name, basin, season_year, start_time, end_time, "
                        + "is_demo, split) VALUES "
                        + "('TEST_LEAK','LEAKY','NI',2019, now(), now(), TRUE, 'train')"))
                .hasMessageContaining("demo_storms_must_be_held_out");
    }

    @Test
    @DisplayName("a model row cannot claim to be trained without evidence")
    void trainedModelsNeedEvidence() {
        assertThatThrownBy(() -> jdbc.update(
                "INSERT INTO model_registry (model_key, version, provenance, is_trained) "
                        + "VALUES ('bogus','v1','TRAINED_MODEL',TRUE)"))
                .hasMessageContaining("trained_models_need_evidence");
    }

    @Test
    @DisplayName("the Phase 0 registry seeds eight untrained components")
    void registryIsSeededUntrained() {
        Integer untrained = jdbc.queryForObject(
                "SELECT count(*) FROM model_registry WHERE is_trained = FALSE "
                        + "AND provenance = 'DEMO_DATA'", Integer.class);
        assertThat(untrained).isEqualTo(8);
    }
}
