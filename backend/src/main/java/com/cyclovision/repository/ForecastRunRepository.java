package com.cyclovision.repository;

import com.cyclovision.entity.ForecastRun;
import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ForecastRunRepository extends JpaRepository<ForecastRun, UUID> {

    /** Cache lookup. Makes a forecast for a given (storm, T, bundle) idempotent. */
    Optional<ForecastRun> findBySidAndIssuedForAndModelBundleVersion(
            String sid, OffsetDateTime issuedFor, String modelBundleVersion);

    /** Fallback lookup when the AI service is down and the bundle version has moved on. */
    Optional<ForecastRun> findFirstBySidAndIssuedForOrderByCreatedAtDesc(
            String sid, OffsetDateTime issuedFor);
}
