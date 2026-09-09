package com.cyclovision.ingestion.provider;

import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Spring Boot integration client provider for the Python Data Integration REST API.
 * Connects over HTTP to port 8001 by default, with built-in timeout, error handling,
 * and mapping to canonical Spring Boot DTOs (ExternalCycloneDto, ExternalObservationDto).
 */
@Component
public class DataIntegrationClientProvider implements CycloneDataProvider {

    private static final Logger logger = LoggerFactory.getLogger(DataIntegrationClientProvider.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final boolean enabled;

    public DataIntegrationClientProvider(
            RestTemplateBuilder restTemplateBuilder,
            @Value("${data.integration.url:http://localhost:8001}") String baseUrl,
            @Value("${data.integration.enabled:true}") boolean enabled) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.enabled = enabled;
        this.restTemplate = restTemplateBuilder
                .setConnectTimeout(Duration.ofSeconds(3))
                .setReadTimeout(Duration.ofSeconds(5))
                .build();
    }

    @Override
    public String getProviderName() {
        return "DATA_INTEGRATION";
    }

    @Override
    public List<ExternalCycloneDto> fetchActiveCyclones() {
        if (!enabled) {
            return Collections.emptyList();
        }

        try {
            String url = baseUrl + "/cyclones?limit=100";
            ResponseEntity<List<Map<String, Object>>> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    null,
                    new ParameterizedTypeReference<>() {}
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                List<ExternalCycloneDto> cyclones = new ArrayList<>();
                for (Map<String, Object> map : response.getBody()) {
                    ExternalCycloneDto dto = new ExternalCycloneDto();
                    dto.setExternalSource(getProviderName());
                    dto.setExternalId((String) map.get("id"));
                    dto.setName((String) map.get("name"));
                    dto.setBasin((String) map.get("basin"));
                    dto.setStatus((String) map.getOrDefault("status", "ACTIVE"));
                    dto.setCurrentCategory((String) map.get("current_category"));
                    cyclones.add(dto);
                }
                return cyclones;
            }
        } catch (RestClientException e) {
            logger.warn("Could not fetch cyclones from Data Integration API ({}/cyclones): {}. Falling back gracefully.", baseUrl, e.getMessage());
        } catch (Exception e) {
            logger.error("Unexpected error fetching cyclones from Data Integration API", e);
        }
        return Collections.emptyList();
    }

    @Override
    public List<ExternalObservationDto> fetchObservations(String externalCycloneId) {
        if (!enabled || externalCycloneId == null || externalCycloneId.isBlank()) {
            return Collections.emptyList();
        }

        try {
            String url = baseUrl + "/cyclones/" + externalCycloneId + "/observations";
            ResponseEntity<List<Map<String, Object>>> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    null,
                    new ParameterizedTypeReference<>() {}
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                List<ExternalObservationDto> observations = new ArrayList<>();
                for (Map<String, Object> map : response.getBody()) {
                    ExternalObservationDto dto = new ExternalObservationDto();
                    dto.setExternalCycloneId(externalCycloneId);
                    
                    String observedAtStr = (String) map.get("observed_at");
                    if (observedAtStr != null) {
                        dto.setObservedAt(Instant.parse(observedAtStr.endsWith("Z") ? observedAtStr : observedAtStr + "Z"));
                    }
                    
                    dto.setLatitude(map.get("latitude") != null ? ((Number) map.get("latitude")).doubleValue() : null);
                    dto.setLongitude(map.get("longitude") != null ? ((Number) map.get("longitude")).doubleValue() : null);
                    dto.setWindSpeedKph(map.get("wind_speed_kmh") != null ? ((Number) map.get("wind_speed_kmh")).doubleValue() : null);
                    dto.setPressureHpa(map.get("pressure_hpa") != null ? ((Number) map.get("pressure_hpa")).doubleValue() : null);
                    dto.setMovementSpeedKph(map.get("movement_speed_kmh") != null ? ((Number) map.get("movement_speed_kmh")).doubleValue() : null);
                    dto.setMovementDirectionDegrees(map.get("movement_direction_deg") != null ? ((Number) map.get("movement_direction_deg")).doubleValue() : null);
                    dto.setSource("IBTrACS");
                    dto.setSourceRecordId(externalCycloneId + "_" + (observedAtStr != null ? observedAtStr.replaceAll("[:\\-]", "") : "0"));
                    
                    observations.add(dto);
                }
                return observations;
            }
        } catch (RestClientException e) {
            logger.warn("Could not fetch observations for cyclone {} from Data Integration API: {}. Returning empty list.", externalCycloneId, e.getMessage());
        } catch (Exception e) {
            logger.error("Unexpected error fetching observations for cyclone " + externalCycloneId, e);
        }
        return Collections.emptyList();
    }
}
