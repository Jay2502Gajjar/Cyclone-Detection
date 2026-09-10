package com.cyclovision;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {"cyclovision.mock-provider.enabled=true"})
class IngestionApiTests {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void testEndToEndIngestion() {
        // 1. Trigger Ingestion with MOCK provider
        ResponseEntity<Map> triggerResponse = restTemplate.postForEntity("/api/internal/ingest/trigger?provider=MOCK", null, Map.class);
        assertEquals(HttpStatus.OK, triggerResponse.getStatusCode());
        assertEquals(Boolean.TRUE, triggerResponse.getBody().get("success"));

        // 2. Fetch all cyclones and verify data is present
        ResponseEntity<List> getCyclonesResponse = restTemplate.getForEntity("/api/cyclones", List.class);
        assertEquals(HttpStatus.OK, getCyclonesResponse.getStatusCode());
        List<?> cyclones = getCyclonesResponse.getBody();
        assertNotNull(cyclones);
        assertTrue(cyclones.size() > 0);

        // Get the first one
        Map<String, Object> firstCyclone = (Map<String, Object>) cyclones.get(0);
        String cycloneId = (String) firstCyclone.get("id");
        assertNotNull(cycloneId);

        // 3. Fetch specific cyclone details
        ResponseEntity<Map> detailResponse = restTemplate.getForEntity("/api/cyclones/" + cycloneId, Map.class);
        assertEquals(HttpStatus.OK, detailResponse.getStatusCode());
        assertNotNull(detailResponse.getBody());
        assertNotNull(detailResponse.getBody().get("externalSource"));
        assertNotNull(detailResponse.getBody().get("name"));

        // 4. Fetch observations
        ResponseEntity<List> obsResponse = restTemplate.getForEntity("/api/cyclones/" + cycloneId + "/observations", List.class);
        assertEquals(HttpStatus.OK, obsResponse.getStatusCode());
        List<?> observations = obsResponse.getBody();
        assertNotNull(observations);
    }
}
