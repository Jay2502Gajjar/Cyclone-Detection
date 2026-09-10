package com.cyclovision.ingestion.provider;

import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class IbtracsDataProvider implements CycloneDataProvider {

    private static final Logger logger = LoggerFactory.getLogger(IbtracsDataProvider.class);
    private final ObjectMapper objectMapper;

    private List<ExternalCycloneDto> cachedCyclones = new ArrayList<>();
    private Map<String, List<ExternalObservationDto>> observationsMap = new HashMap<>();
    private boolean loaded = false;

    public IbtracsDataProvider(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public String getProviderName() {
        return "IBTrACS";
    }

    private static final Map<String, Integer> CATEGORY_RANK = Map.of(
        "Unknown", 0,
        "Depression", 1,
        "Deep Depression", 2,
        "Cyclonic Storm", 3,
        "Severe Cyclonic Storm", 4,
        "Very Severe Cyclonic Storm", 5,
        "Extremely Severe Cyclonic Storm", 6,
        "Super Cyclonic Storm", 7
    );

    private InputStream getResourceStream(String filename) throws Exception {
        ClassPathResource res = new ClassPathResource("data/" + filename);
        if (res.exists()) {
            return res.getInputStream();
        }
        res = new ClassPathResource("data/ibtracs/" + filename);
        if (res.exists()) {
            return res.getInputStream();
        }
        java.io.File file = new java.io.File("backend/data/ibtracs/" + filename);
        if (file.exists()) {
            return new java.io.FileInputStream(file);
        }
        file = new java.io.File("data/ibtracs/" + filename);
        if (file.exists()) {
            return new java.io.FileInputStream(file);
        }
        throw new java.io.FileNotFoundException("Could not locate IBTrACS data file: " + filename);
    }

    private synchronized void ensureLoaded() {
        if (loaded) return;
        try {
            logger.info("Loading NOAA IBTrACS dataset into memory...");
            
            // 1. Load Cyclones
            try (InputStream is = getResourceStream("cyclones.json")) {
                JsonNode root = objectMapper.readTree(is);
                for (JsonNode node : root) {
                    ExternalCycloneDto dto = new ExternalCycloneDto();
                    dto.setExternalSource(getProviderName());
                    dto.setExternalId(node.path("id").asText());
                    dto.setName(node.path("name").asText());
                    dto.setBasin(node.path("basin").asText());
                    dto.setStatus(node.path("status").asText());
                    cachedCyclones.add(dto);
                }
            }

            // 2. Load Observations & compute peak intensity category per cyclone
            Map<String, String> peakCategoryMap = new HashMap<>();
            Map<String, Integer> peakRankMap = new HashMap<>();

            try (InputStream is = getResourceStream("observations.json")) {
                JsonNode root = objectMapper.readTree(is);
                for (JsonNode node : root) {
                    ExternalObservationDto dto = new ExternalObservationDto();
                    String cycloneId = node.path("cyclone_id").asText();
                    dto.setExternalCycloneId(cycloneId);
                    
                    String observedAtStr = node.path("observed_at").asText();
                    dto.setObservedAt(Instant.parse(observedAtStr));
                    
                    if (!node.path("latitude").isNull()) {
                        dto.setLatitude(node.path("latitude").asDouble());
                    }
                    if (!node.path("longitude").isNull()) {
                        dto.setLongitude(node.path("longitude").asDouble());
                    }
                    if (!node.path("wind_speed_kmh").isNull()) {
                        dto.setWindSpeedKph(node.path("wind_speed_kmh").asDouble());
                    }
                    if (!node.path("pressure_hpa").isNull()) {
                        dto.setPressureHpa(node.path("pressure_hpa").asDouble());
                    }
                    if (!node.path("movement_direction_deg").isNull()) {
                        dto.setMovementDirectionDegrees(node.path("movement_direction_deg").asDouble());
                    }
                    if (!node.path("movement_speed_kmh").isNull()) {
                        dto.setMovementSpeedKph(node.path("movement_speed_kmh").asDouble());
                    }
                    
                    dto.setSource(getProviderName());
                    dto.setSourceRecordId(cycloneId + "-" + observedAtStr);
                    
                    observationsMap.computeIfAbsent(cycloneId, k -> new ArrayList<>()).add(dto);

                    if (!node.path("intensity_category").isNull()) {
                        String category = node.path("intensity_category").asText();
                        int rank = CATEGORY_RANK.getOrDefault(category, 0);
                        int currentPeak = peakRankMap.getOrDefault(cycloneId, -1);
                        if (rank > currentPeak) {
                            peakRankMap.put(cycloneId, rank);
                            peakCategoryMap.put(cycloneId, category);
                        }
                    }
                }
            }

            // 3. Assign peak intensity category to each cyclone
            for (ExternalCycloneDto cyclone : cachedCyclones) {
                String peakCat = peakCategoryMap.get(cyclone.getExternalId());
                if (peakCat != null && !peakCat.isBlank()) {
                    cyclone.setCurrentCategory(peakCat);
                }
            }
            
            loaded = true;
            logger.info("Successfully loaded {} cyclones and {} observations from NOAA IBTrACS", 
                cachedCyclones.size(), 
                observationsMap.values().stream().mapToInt(List::size).sum());
                
        } catch (Exception e) {
            logger.error("Failed to load IBTrACS data", e);
        }
    }

    @Override
    public List<ExternalCycloneDto> fetchActiveCyclones() {
        ensureLoaded();
        return cachedCyclones;
    }

    @Override
    public List<ExternalObservationDto> fetchObservations(String externalCycloneId) {
        ensureLoaded();
        return observationsMap.getOrDefault(externalCycloneId, Collections.emptyList());
    }
}
