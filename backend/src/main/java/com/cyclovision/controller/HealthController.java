package com.cyclovision.controller;

import com.cyclovision.client.AiServiceClient;
import com.cyclovision.dto.HealthDto.AiServiceHealth;
import com.cyclovision.dto.HealthDto.HealthResponse;
import com.cyclovision.repository.ModelRegistryRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Reports the truth about the stack, including whether any model is actually trained.
 *
 * <p>Phase 0 is expected to report {@code DEGRADED} with every model untrained. That is
 * the correct answer, not a bug.
 */
@RestController
public class HealthController {

    private final AiServiceClient aiServiceClient;
    private final ModelRegistryRepository registryRepository;
    private final boolean demoMode;
    private final String bundleVersion;

    public HealthController(AiServiceClient aiServiceClient,
            ModelRegistryRepository registryRepository,
            @Value("${cyclovision.demo-mode:false}") boolean demoMode,
            @Value("${cyclovision.bundle-version:phase0}") String bundleVersion) {
        this.aiServiceClient = aiServiceClient;
        this.registryRepository = registryRepository;
        this.demoMode = demoMode;
        this.bundleVersion = bundleVersion;
    }

    @GetMapping("/api/health")
    public HealthResponse health() {
        AiServiceHealth ai = aiServiceClient.health();

        String database = "DOWN";
        try {
            registryRepository.count();
            database = "UP";
        } catch (Exception ignored) {
            // reported as DOWN below
        }

        boolean anyTrained = ai.models() != null
                && ai.models().stream().anyMatch(m -> m.isTrained());
        String status = "UP".equals(ai.status()) && "UP".equals(database) && anyTrained
                ? "UP" : "DEGRADED";

        return new HealthResponse(status, ai, database, demoMode, bundleVersion);
    }
}
