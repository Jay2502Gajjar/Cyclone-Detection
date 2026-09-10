package com.cyclovision;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
public class ExecuteAndVerifyFlywayV4Test {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void executeAndVerifyV4Migration() {
        System.out.println("================================================================================");
        System.out.println("              VERIFYING FLYWAY V4 MIGRATION & POSTGIS ON SUPABASE               ");
        System.out.println("================================================================================");

        // 1. Verify Flyway Version is 4
        System.out.println("\n[1] FLYWAY SCHEMA HISTORY");
        List<Map<String, Object>> history = jdbcTemplate.queryForList(
                "SELECT installed_rank, version, description, type, script, execution_time, success, installed_on " +
                "FROM flyway_schema_history ORDER BY installed_rank"
        );
        for (Map<String, Object> row : history) {
            System.out.printf("Rank: %-2s | Version: %-2s | Description: %-35s | Time: %4dms | Success: %s\n",
                    row.get("installed_rank"), row.get("version"), row.get("description"), row.get("execution_time"), row.get("success"));
            assertTrue((Boolean) row.get("success"), "Migration " + row.get("version") + " should be successful");
        }
        assertEquals("4", String.valueOf(history.get(history.size() - 1).get("version")), "Latest Flyway version must be 4");

        // 2. Verify PostGIS Extension Exists
        System.out.println("\n[2] POSTGIS EXTENSION VERIFICATION");
        List<Map<String, Object>> postgisExt = jdbcTemplate.queryForList(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'postgis'"
        );
        assertFalse(postgisExt.isEmpty(), "PostGIS extension must be installed in pg_extension");
        String postgisVersion = (String) postgisExt.get(0).get("extversion");
        System.out.println("-> PostGIS installed successfully! Version: " + postgisVersion);

        // 3, 4, 5. Verify location columns on cyclone_observations, predicted_track_points, weather_data
        System.out.println("\n[3, 4, 5] SPATIAL GEOGRAPHY COLUMNS");
        String[] tables = {"cyclone_observations", "predicted_track_points", "weather_data"};
        for (String tbl : tables) {
            List<Map<String, Object>> colInfo = jdbcTemplate.queryForList(
                    "SELECT column_name, data_type, udt_name, is_generated " +
                    "FROM information_schema.columns " +
                    "WHERE table_schema = 'public' AND table_name = ? AND column_name = 'location'",
                    tbl
            );
            assertFalse(colInfo.isEmpty(), "Table " + tbl + " must have a 'location' column");
            System.out.printf("Table: %-25s | Column: %-10s | Type: %-15s | UDT: %-10s | Generated: %s\n",
                    tbl, colInfo.get(0).get("column_name"), colInfo.get(0).get("data_type"), colInfo.get(0).get("udt_name"), colInfo.get(0).get("is_generated"));
            assertEquals("geography", colInfo.get(0).get("udt_name"));
        }

        // 6. Verify GIST Indexes Exist
        System.out.println("\n[6] GIST SPATIAL INDEXES");
        String[] indexNames = {"idx_obs_spatial_location", "idx_pred_track_spatial_location", "idx_weather_spatial_location"};
        for (String idx : indexNames) {
            List<Map<String, Object>> idxInfo = jdbcTemplate.queryForList(
                    "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public' AND indexname = ?",
                    idx
            );
            assertFalse(idxInfo.isEmpty(), "Index " + idx + " must exist");
            System.out.println("Index: " + idx + " -> " + idxInfo.get(0).get("indexdef"));
            assertTrue(((String) idxInfo.get(0).get("indexdef")).toLowerCase().contains("gist"), "Index must be GIST");
        }

        // 7. Verify Row Count of cyclone_observations
        System.out.println("\n[7] ROW COUNT VERIFICATION");
        Long obsCount = jdbcTemplate.queryForObject("SELECT count(*) FROM cyclone_observations", Long.class);
        System.out.println("-> Total cyclone_observations: " + obsCount);
        assertEquals(12686L, obsCount, "Existing cyclone_observations row count must remain 12,686");

        // 8 & 9. Sample Coordinate Verification: ST_X(location::geometry) = longitude, ST_Y(location::geometry) = latitude
        System.out.println("\n[8 & 9] SPATIAL ACCURACY VERIFICATION (ST_X, ST_Y vs Longitude, Latitude)");
        List<Map<String, Object>> samples = jdbcTemplate.queryForList(
                "SELECT id, latitude, longitude, " +
                "       ST_AsText(location) AS geom_text, " +
                "       ST_X(location::geometry) AS geom_x, " +
                "       ST_Y(location::geometry) AS geom_y " +
                "FROM cyclone_observations " +
                "WHERE latitude IS NOT NULL AND longitude IS NOT NULL " +
                "ORDER BY observed_at DESC LIMIT 5"
        );
        for (Map<String, Object> sample : samples) {
            Double lat = ((Number) sample.get("latitude")).doubleValue();
            Double lon = ((Number) sample.get("longitude")).doubleValue();
            Double geomX = ((Number) sample.get("geom_x")).doubleValue();
            Double geomY = ((Number) sample.get("geom_y")).doubleValue();
            String geomText = (String) sample.get("geom_text");

            System.out.printf("Obs ID: %s | (Lat, Lon): (%7.2f, %7.2f) | WKT: %-25s | Check: X=%.2f, Y=%.2f\n",
                    sample.get("id"), lat, lon, geomText, geomX, geomY);

            assertEquals(lon, geomX, 0.0001, "ST_X must match longitude");
            assertEquals(lat, geomY, 0.0001, "ST_Y must match latitude");
        }

        // 10. Verify NULL Handling
        System.out.println("\n[10] NULL COORDINATE HANDLING VERIFICATION");
        // Test query with ST_MakePoint and NULL
        Long nullLocCount = jdbcTemplate.queryForObject(
                "SELECT count(*) FROM cyclone_observations WHERE location IS NULL", Long.class
        );
        System.out.println("-> Total observations with NULL location: " + nullLocCount);

        // 11. Real PostGIS Query Verification (ST_DWithin & ST_Distance)
        System.out.println("\n[11] REAL POSTGIS SPATIAL QUERIES (ST_DWithin & ST_Distance)");
        // Query cyclones within 500km of Puri, Odisha (19.8135° N, 85.8312° E)
        double puriLat = 19.8135;
        double puriLon = 85.8312;
        double radiusMeters = 500000.0; // 500 km

        List<Map<String, Object>> nearbyPoints = jdbcTemplate.queryForList(
                "SELECT co.id, co.cyclone_id, co.observed_at, co.latitude, co.longitude, co.wind_speed_kph, " +
                "       ST_Distance(co.location, ST_SetSRID(ST_MakePoint(?, ?), 4326)::geography) / 1000.0 AS distance_km " +
                "FROM cyclone_observations co " +
                "WHERE ST_DWithin(co.location, ST_SetSRID(ST_MakePoint(?, ?), 4326)::geography, ?) " +
                "ORDER BY distance_km ASC LIMIT 5",
                puriLon, puriLat, puriLon, puriLat, radiusMeters
        );

        System.out.printf("-> Found %d observations within 500km of Puri (%.4f N, %.4f E):\n", nearbyPoints.size(), puriLat, puriLon);
        for (Map<String, Object> pt : nearbyPoints) {
            System.out.printf("   Obs ID: %s | Distance: %6.1f km | Point: (%.2f N, %.2f E) | Wind: %.1f kph | Time: %s\n",
                    pt.get("id"), pt.get("distance_km"), pt.get("latitude"), pt.get("longitude"), pt.get("wind_speed_kph"), pt.get("observed_at"));
        }
        assertFalse(nearbyPoints.isEmpty(), "Spatial query ST_DWithin should return observations near Bay of Bengal");

        System.out.println("================================================================================");
        System.out.println("                   ALL V4 & POSTGIS VERIFICATIONS PASSED!                       ");
        System.out.println("================================================================================");
    }
}
