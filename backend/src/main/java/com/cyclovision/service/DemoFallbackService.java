package com.cyclovision.service;

import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.entity.DemoScenario;
import com.cyclovision.repository.DemoScenarioRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.OffsetDateTime;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Last line of defence: a stored, fully-formed response for a known demo moment.
 *
 * <p>Anything served from here is stamped {@code servedFrom = "demo"} and
 * {@code degraded = true}, so the UI shows it as demo data rather than passing it off as
 * a live prediction. That labelling is the whole reason this fallback is acceptable.
 */
@Service
public class DemoFallbackService {

    private static final Logger log = LoggerFactory.getLogger(DemoFallbackService.class);

    private final DemoScenarioRepository repository;
    private final ObjectMapper objectMapper;

    public DemoFallbackService(DemoScenarioRepository repository, ObjectMapper objectMapper) {
        this.repository = repository;
        this.objectMapper = objectMapper;
    }

    public Optional<ForecastResponse> forSid(String sid, OffsetDateTime asOf) {
        Optional<DemoScenario> scenario = repository.findBySidAndIssuedFor(sid, asOf)
                .or(() -> repository.findFirstBySidOrderByIssuedForAsc(sid));
        return scenario.flatMap(this::parse)
                .map(r -> r.withDelivery(true, "demo"));
    }

    private Optional<ForecastResponse> parse(DemoScenario scenario) {
        try {
            return Optional.of(
                    objectMapper.readValue(scenario.getPayloadJson(), ForecastResponse.class));
        } catch (Exception e) {
            log.error("Demo scenario {} has an unreadable payload: {}",
                    scenario.getId(), e.toString());
            return Optional.empty();
        }
    }
}
