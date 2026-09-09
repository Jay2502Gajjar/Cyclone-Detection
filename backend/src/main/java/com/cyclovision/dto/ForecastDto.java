package com.cyclovision.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

/**
 * The composite forecast payload.
 *
 * <p>This is the response the whole Command Center is built from: one call returns the
 * current state, structure, vision estimate, intensity and track forecasts, analogue
 * ensemble, risk, the narrative report and — when revealed — verification against
 * ground truth. There is deliberately no follow-up call for any of it.
 *
 * <p><b>Invariant I2:</b> {@link VerificationBlock} is assembled by
 * {@code VerificationService} from the database. The AI service has no field for it and
 * can never produce it.
 */
public final class ForecastDto {

    private ForecastDto() {
    }

    public record ShapFactor(String feature, double shap, String direction) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record IntensityForecast(
            Double deltaVmax24hKt,
            Double predictedVmax24hKt,
            String trend,               // INTENSIFYING | WEAKENING | STEADY
            Double confidence,
            Double riProbability,
            Double riBaseRate,
            List<ShapFactor> topFactors,
            Source source) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record TrackPointDto(
            int leadHours,              // 12 | 24 | 48
            double lat,
            double lon,
            Double coneRadiusP67Km,
            Double coneRadiusP90Km,
            Double predictedVmaxKt) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record TrackForecast(
            List<TrackPointDto> points,
            Source source,
            Source coneSource,
            String coneBasis) {
    }

    public record AnalogueOutcome(
            int intensifiedCount,
            int weakenedCount,
            Double meanDeltaVmax24hKt,
            int riCount,
            Double riFraction,
            Double riBaseRate) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record AnalogueMatchDto(
            int rank,
            String sid,
            String name,
            OffsetDateTime time,
            double similarity,
            Double outcomeDeltaVmax24hKt,
            Boolean wasRi,
            List<List<Double>> onwardTrack) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record AnalogueBlock(
            int k,
            AnalogueOutcome outcome,
            List<AnalogueMatchDto> matches,
            List<String> exclusions,
            Source source) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record RiskBlock(
            Double score,
            String level,               // LOW | MODERATE | HIGH | CRITICAL
            String formula,
            Map<String, Double> terms,
            String nearestCoast,
            Double landfallWindowHours,
            Source source) {
    }

    public record ReportBlock(String text, Source source) {
    }

    /** A single observed future position, used only for verification. */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record ObservedPoint(
            OffsetDateTime t,
            double lat,
            double lon,
            Double vmaxKt) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record VerificationBlock(
            boolean available,
            ObservedPoint observedAt24h,
            ObservedPoint observedAt48h,
            Double trackErrorKm24h,
            Double trackErrorKm48h,
            Double intensityErrorKt24h,
            Boolean insideConeP67,
            Boolean insideConeP90,
            Boolean riOccurred,
            Boolean riWarningIssued,
            Source source) {

        public static VerificationBlock unavailable() {
            return new VerificationBlock(false, null, null, null, null, null,
                    null, null, null, null, Source.observed());
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record ForecastResponse(
            String sid,
            OffsetDateTime issuedFor,
            String modelBundleVersion,
            FrameDto.ObservedBlock current,
            FrameDto.StructureBlock structure,
            FrameDto.VisionBlock vision,
            IntensityForecast intensityForecast,
            TrackForecast trackForecast,
            AnalogueBlock analogues,
            RiskBlock risk,
            ReportBlock report,
            VerificationBlock verification,
            boolean degraded,
            String servedFrom) {       // live | cache | demo

        public ForecastResponse withVerification(VerificationBlock v) {
            return new ForecastResponse(sid, issuedFor, modelBundleVersion, current,
                    structure, vision, intensityForecast, trackForecast, analogues,
                    risk, report, v, degraded, servedFrom);
        }

        public ForecastResponse withDelivery(boolean isDegraded, String source) {
            return new ForecastResponse(sid, issuedFor, modelBundleVersion, current,
                    structure, vision, intensityForecast, trackForecast, analogues,
                    risk, report, verification, isDegraded, source);
        }
    }
}
