package com.cyclovision.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

/**
 * Storm list and detail payloads.
 *
 * <p>{@link StormDetail#frames()} is deliberately thin: it carries exactly what the
 * timeline scrubber and the intensity sparkline need, for the storm's whole lifetime,
 * in one call. Full per-frame analysis is fetched separately from
 * {@code /api/storms/{sid}/frames/{t}} so the scrubber never waterfalls.
 */
public final class StormDto {

    private StormDto() {
    }

    public record StormSummary(
            String sid,
            String name,
            String basin,
            int seasonYear,
            OffsetDateTime startTime,
            OffsetDateTime endTime,
            Double peakVmaxKt,
            String peakCategory,
            int frameCount,
            int framesWithImagery,
            boolean isDemo,
            String split) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record Landfall(
            OffsetDateTime time,
            double lat,
            double lon,
            String place) {
    }

    /** One point on the scrubber. Kept small — a whole storm is a few hundred of these. */
    public record TrackFrame(
            OffsetDateTime t,
            double lat,
            double lon,
            Double vmaxKt,
            Double pressureHpa,
            String category,
            String imageUrl,
            boolean hasAnalysis,
            Double cnnVmaxKt,
            String regime) {
    }

    public record StormDetail(
            String sid,
            String name,
            String basin,
            int seasonYear,
            OffsetDateTime startTime,
            OffsetDateTime endTime,
            Double peakVmaxKt,
            String peakCategory,
            int frameCount,
            int framesWithImagery,
            boolean isDemo,
            String split,
            Landfall landfall,
            List<TrackFrame> frames,
            Map<String, Source> sources) {
    }
}
