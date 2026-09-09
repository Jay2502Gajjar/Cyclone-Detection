package com.cyclovision.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.OffsetDateTime;
import java.util.List;

/**
 * Per-frame analysis payloads.
 *
 * <p>{@link StructureBlock} carries two separate provenance stamps on purpose: the
 * seven metrics are {@code DERIVED_MEASUREMENT} (deterministic physics over the raw
 * brightness-temperature field), while the regime label on top of them is
 * {@code RULE_ENGINE}. Collapsing them into one stamp would overstate the regime.
 */
public final class FrameDto {

    private FrameDto() {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record ObservedBlock(
            double lat,
            double lon,
            Double vmaxKt,
            Double pressureHpa,
            String category,
            Double distToCoastKm,
            Source source) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record StructureBlock(
            String regime,
            String regimeLabel,
            Boolean eyePresent,
            Double eyeRadiusKm,
            Double eyeRingBtContrastK,
            Double minBtK,
            Double cdoFraction100km,
            Double axisymmetry,
            Double convectiveRingRadiusKm,
            Double coldCloudOffsetKm,
            List<String> rulesApplied,
            Source metricsSource,
            Source regimeSource) {

        /** No imagery for this frame: metrics are absent, not guessed. */
        public static StructureBlock empty(Source metricsSource, Source regimeSource) {
            return new StructureBlock(null, null, null, null, null, null, null, null,
                    null, null, List.of(), metricsSource, regimeSource);
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record VisionBlock(
            Double vmaxKt,
            String category,
            Double confidence,
            String gradcamUrl,
            Source source) {

        public static VisionBlock empty(Source source) {
            return new VisionBlock(null, null, null, null, source);
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record FrameAnalysis(
            String sid,
            OffsetDateTime t,
            ObservedBlock observed,
            String imageUrl,
            OffsetDateTime imageTime,
            String imageSource,
            StructureBlock structure,
            VisionBlock vision,
            String analysisVersion) {
    }
}
