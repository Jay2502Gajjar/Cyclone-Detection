package com.cyclovision.dto;

import com.cyclovision.domain.Provenance;
import java.util.List;

/** Health payloads. Mirrors {@code HealthResponse} in API_CONTRACT.md. */
public final class HealthDto {

    private HealthDto() {
    }

    public record HealthResponse(
            String status,          // "UP" | "DEGRADED"
            AiServiceHealth aiService,
            String database,        // "UP" | "DOWN"
            boolean demoMode,
            String bundleVersion) {
    }

    public record AiServiceHealth(
            String status,          // "UP" | "DOWN"
            List<ModelInfo> models) {
    }

    public record ModelInfo(
            String key,
            String version,
            Provenance provenance,
            boolean isTrained) {
    }
}
