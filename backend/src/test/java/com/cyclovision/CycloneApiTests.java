package com.cyclovision;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class CycloneApiTests {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void testGetCyclonesReturnsOnlyIbtracsRecords() {
        ResponseEntity<List> response = restTemplate.getForEntity("/api/cyclones", List.class);
        assertEquals(HttpStatus.OK, response.getStatusCode());
        List<?> cyclones = response.getBody();
        assertNotNull(cyclones);
        assertTrue(!cyclones.isEmpty(), "Should return real IBTrACS records");

        for (Object item : cyclones) {
            Map<?, ?> cyclone = (Map<?, ?>) item;
            String source = (String) cyclone.get("externalSource");
            assertNotNull(source, "externalSource must not be null for production cyclone API");
            assertEquals("IBTrACS", source, "externalSource must be IBTrACS");
            assertNotNull(cyclone.get("id"), "id must be present");
            assertNotNull(cyclone.get("name"), "name must be present");
            assertNotNull(cyclone.get("basin"), "basin must be present");
            assertNotNull(cyclone.get("status"), "status must be present");
        }
    }

    @Test
    void testGetActiveCyclonesReturnsEmptyListAndNoMockOrNull() {
        ResponseEntity<List> response = restTemplate.getForEntity("/api/cyclones/active", List.class);
        assertEquals(HttpStatus.OK, response.getStatusCode());
        List<?> active = response.getBody();
        assertNotNull(active);
        // Since real NOAA IBTrACS dataset has status = 'historical' for all storms,
        // and mock/demo records are excluded, active cyclones list must be empty []
        assertTrue(active.isEmpty(), "Active cyclone list must be empty when no IBTrACS storm is ACTIVE");
    }

    @Test
    void testGetCycloneByIdNotFound() {
        UUID randomId = UUID.randomUUID();
        ResponseEntity<Map> response = restTemplate.getForEntity("/api/cyclones/" + randomId, Map.class);
        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertEquals("Not Found", response.getBody().get("error"));
    }

    @Test
    void testGetCycloneObservationsNotFound() {
        UUID randomId = UUID.randomUUID();
        ResponseEntity<Map> response = restTemplate.getForEntity("/api/cyclones/" + randomId + "/observations", Map.class);
        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
    }
}
