package com.cyclovision;

import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import com.cyclovision.ingestion.provider.DataIntegrationClientProvider;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.client.RestClientTest;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;

import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

@RestClientTest(DataIntegrationClientProvider.class)
class DataIntegrationCompatibilityTests {

    @Autowired
    private DataIntegrationClientProvider provider;

    @Autowired
    private MockRestServiceServer mockServer;

    @Test
    @DisplayName("Verify Spring Boot deserializes Cyclone list from Python Data Integration API")
    void testFetchActiveCyclonesCompatibility() {
        String jsonPayload = """
            [
                {
                    "id": "2020136N10088",
                    "name": "AMPHAN",
                    "basin": "NI",
                    "season_year": 2020,
                    "status": "historical"
                },
                {
                    "id": "2019116N02090",
                    "name": "FANI",
                    "basin": "NI",
                    "season_year": 2019,
                    "status": "historical"
                }
            ]
            """;

        mockServer.expect(requestTo("http://localhost:8001/cyclones?limit=100"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess(jsonPayload, MediaType.APPLICATION_JSON));

        List<ExternalCycloneDto> cyclones = provider.fetchActiveCyclones();

        assertNotNull(cyclones);
        assertEquals(2, cyclones.size());

        // Verify AMPHAN mapping
        ExternalCycloneDto amphan = cyclones.get(0);
        assertEquals("DATA_INTEGRATION", amphan.getExternalSource());
        assertEquals("2020136N10088", amphan.getExternalId());
        assertEquals("AMPHAN", amphan.getName());
        assertEquals("NI", amphan.getBasin());
        assertEquals("historical", amphan.getStatus());

        // Verify FANI mapping
        ExternalCycloneDto fani = cyclones.get(1);
        assertEquals("2019116N02090", fani.getExternalId());
        assertEquals("FANI", fani.getName());

        mockServer.verify();
    }

    @Test
    @DisplayName("Verify Spring Boot maps Observation fields correctly for AMPHAN & FANI")
    void testFetchObservationsCompatibility() {
        String amphanObsPayload = """
            [
                {
                    "observed_at": "2020-05-16T12:00:00Z",
                    "latitude": 10.5,
                    "longitude": 86.4,
                    "wind_speed_kmh": 240.8,
                    "pressure_hpa": 920.0,
                    "movement_direction_deg": 350.0,
                    "movement_speed_kmh": 15.2,
                    "intensity_category": "Super Cyclonic Storm"
                },
                {
                    "observed_at": "2020-05-16T18:00:00Z",
                    "latitude": 11.2,
                    "longitude": 86.3,
                    "wind_speed_kmh": 250.0,
                    "pressure_hpa": 915.0,
                    "movement_direction_deg": 355.0,
                    "movement_speed_kmh": 16.0,
                    "intensity_category": "Super Cyclonic Storm"
                }
            ]
            """;

        mockServer.expect(requestTo("http://localhost:8001/cyclones/2020136N10088/observations"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess(amphanObsPayload, MediaType.APPLICATION_JSON));

        List<ExternalObservationDto> obsList = provider.fetchObservations("2020136N10088");

        assertNotNull(obsList);
        assertEquals(2, obsList.size());

        ExternalObservationDto obs1 = obsList.get(0);
        assertEquals("2020136N10088", obs1.getExternalCycloneId());
        assertEquals(Instant.parse("2020-05-16T12:00:00Z"), obs1.getObservedAt());
        assertEquals(10.5, obs1.getLatitude());
        assertEquals(86.4, obs1.getLongitude());
        assertEquals(240.8, obs1.getWindSpeedKph());
        assertEquals(920.0, obs1.getPressureHpa());
        assertEquals(15.2, obs1.getMovementSpeedKph());
        assertEquals(350.0, obs1.getMovementDirectionDegrees());
        assertEquals("IBTrACS", obs1.getSource());
        assertTrue(obs1.getSourceRecordId().startsWith("2020136N10088"));

        mockServer.verify();
    }

    @Test
    @DisplayName("Verify Spring Boot handles Data Integration API 500 error gracefully without breaking")
    void testApiErrorFallbackBehavior() {
        mockServer.expect(requestTo("http://localhost:8001/cyclones?limit=100"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withStatus(HttpStatus.INTERNAL_SERVER_ERROR));

        List<ExternalCycloneDto> cyclones = provider.fetchActiveCyclones();
        assertNotNull(cyclones);
        assertTrue(cyclones.isEmpty(), "Should return empty list gracefully on server error");

        mockServer.verify();
    }

    @Test
    @DisplayName("Verify Spring Boot handles 404 Not Found for non-existent cyclone observations")
    void testObservations404FallbackBehavior() {
        mockServer.expect(requestTo("http://localhost:8001/cyclones/UNKNOWN_ID/observations"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withStatus(HttpStatus.NOT_FOUND));

        List<ExternalObservationDto> obs = provider.fetchObservations("UNKNOWN_ID");
        assertNotNull(obs);
        assertTrue(obs.isEmpty(), "Should return empty list gracefully on 404 Not Found");

        mockServer.verify();
    }
}
