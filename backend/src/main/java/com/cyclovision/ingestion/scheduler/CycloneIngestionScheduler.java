package com.cyclovision.ingestion.scheduler;

import com.cyclovision.ingestion.service.CycloneIngestionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Automated scheduler for NOAA IBTrACS cyclone data ingestion.
 * Runs on a configurable fixed delay and delegates solely to CycloneIngestionService.
 */
@Component
@ConditionalOnProperty(
        name = "cyclovision.ingestion.scheduler.enabled",
        havingValue = "true",
        matchIfMissing = true
)
public class CycloneIngestionScheduler {

    private static final Logger logger = LoggerFactory.getLogger(CycloneIngestionScheduler.class);
    private static final String TARGET_PROVIDER = "IBTrACS";

    private final CycloneIngestionService ingestionService;

    public CycloneIngestionScheduler(CycloneIngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @Scheduled(
            fixedDelayString = "${cyclovision.ingestion.scheduler.fixed-delay-ms:21600000}",
            initialDelayString = "${cyclovision.ingestion.scheduler.initial-delay-ms:60000}"
    )
    public void scheduleIngestion() {
        logger.info("Triggering scheduled IBTrACS cyclone ingestion");
        try {
            Map<String, Object> result = ingestionService.runIngestion(TARGET_PROVIDER);

            if (Boolean.TRUE.equals(result.get("skipped"))) {
                logger.warn("Scheduled IBTrACS ingestion skipped: concurrent ingestion already in progress");
            } else if (Boolean.TRUE.equals(result.get("success"))) {
                logger.info("Scheduled IBTrACS ingestion completed successfully in {} ms: {}", result.get("durationMs"), result);
            } else {
                logger.warn("Scheduled IBTrACS ingestion completed with errors (failures: {}): {}", result.get("failures"), result);
            }
        } catch (Exception e) {
            // Catching all exceptions ensures future scheduled runs remain active
            logger.error("Unexpected failure during scheduled IBTrACS ingestion execution", e);
        }
    }
}
