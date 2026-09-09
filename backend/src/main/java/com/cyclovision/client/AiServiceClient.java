package com.cyclovision.client;

import com.cyclovision.dto.HealthDto.AiServiceHealth;
import com.cyclovision.dto.InferDto.InferFullRequest;
import com.cyclovision.dto.InferDto.InferFullResponse;
import java.time.Duration;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * The single point at which Spring Boot talks to the AI service.
 *
 * <p>Centralising it means timeout and failure handling exist in exactly one place. The
 * timeout is short and there is no retry: a demo that hangs for thirty seconds is worse
 * than one that falls back to a cached run in eight.
 */
@Component
public class AiServiceClient {

    private static final Logger log = LoggerFactory.getLogger(AiServiceClient.class);

    private final WebClient webClient;
    private final Duration timeout;

    public AiServiceClient(WebClient aiWebClient,
            @org.springframework.beans.factory.annotation.Value(
                    "${cyclovision.ai-service.timeout-seconds:8}") long timeoutSeconds) {
        this.webClient = aiWebClient;
        this.timeout = Duration.ofSeconds(timeoutSeconds);
    }

    /**
     * Runs the full inference pipeline.
     *
     * <p>The request carries only observations at or before {@code asOf} (invariant I1),
     * and the response type has no verification field (invariant I2).
     */
    public InferFullResponse inferFull(InferFullRequest request) {
        try {
            return webClient.post()
                    .uri("/infer/full")
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(InferFullResponse.class)
                    .timeout(timeout)
                    .block();
        } catch (Exception e) {
            log.warn("AI service /infer/full failed for sid={} asOf={}: {}",
                    request.sid(), request.asOf(), e.toString());
            throw new AiServiceUnavailableException("AI service unavailable", e);
        }
    }

    /**
     * Never throws: health is reported, not enforced.
     *
     * <p>The status returned here means <em>reachability</em> — UP or DOWN — which is a
     * different question from the one the AI service answers about itself. The AI service
     * reports DEGRADED when its bundle has no trained models; that is a fact about the
     * bundle, and it is already visible in the per-model list. Passing it through as the
     * connection status would conflate "we cannot reach it" with "it is reachable and
     * honest about being untrained".
     */
    public AiServiceHealth health() {
        try {
            AiServiceHealth health = webClient.get()
                    .uri("/health")
                    .retrieve()
                    .bodyToMono(AiServiceHealth.class)
                    .timeout(Duration.ofSeconds(3))
                    .block();
            if (health == null) {
                return down();
            }
            return new AiServiceHealth("UP",
                    health.models() == null ? List.of() : health.models());
        } catch (Exception e) {
            log.debug("AI service health check failed: {}", e.toString());
            return down();
        }
    }

    private static AiServiceHealth down() {
        return new AiServiceHealth("DOWN", List.of());
    }
}
