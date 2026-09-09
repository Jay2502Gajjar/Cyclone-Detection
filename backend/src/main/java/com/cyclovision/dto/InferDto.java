package com.cyclovision.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.OffsetDateTime;
import java.util.List;

/**
 * The internal Spring Boot → FastAPI contract.
 *
 * <p><b>Invariant I1 (temporal masking):</b> {@link InferFullRequest} has no field
 * capable of carrying an observation later than {@link InferFullRequest#asOf()}. The
 * history list is filtered by {@code InferRequestBuilder} before it is constructed and
 * re-validated by a Pydantic validator on the FastAPI side, which returns 422 on any
 * violation. Two independent mistakes would be required to leak the future.
 *
 * <p><b>Invariant I2:</b> there is no verification field here, in either direction.
 */
public final class InferDto {

    private InferDto() {
    }

    /** One masked history point. Contains only what was observable at or before asOf. */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record HistoryPoint(
            OffsetDateTime t,
            double lat,
            double lon,
            Double vmaxKt,
            Double pressureHpa,
            Double translationSpeedKt,
            Double headingDeg,
            Double distToCoastKm) {
    }

    /** Reference to the satellite frame at asOf. Paths are resolved under FRAMES_DIR. */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record FrameRef(
            String btPath,
            String imageUrl,
            OffsetDateTime imageTime,
            String imageSource) {
    }

    public record InferOptions(
            int analogueK,
            boolean wantGradcam,
            boolean wantShap) {

        public static InferOptions defaults() {
            return new InferOptions(20, true, true);
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record InferFullRequest(
            String sid,
            OffsetDateTime asOf,
            List<HistoryPoint> history,
            FrameRef frameRef,
            InferOptions options) {
    }

    /**
     * The AI service response: {@code ForecastResponse} minus verification, degraded and
     * servedFrom. Those three are added by Spring Boot.
     */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record InferFullResponse(
            String sid,
            OffsetDateTime issuedFor,
            String modelBundleVersion,
            FrameDto.ObservedBlock current,
            FrameDto.StructureBlock structure,
            FrameDto.VisionBlock vision,
            ForecastDto.IntensityForecast intensityForecast,
            ForecastDto.TrackForecast trackForecast,
            ForecastDto.AnalogueBlock analogues,
            ForecastDto.RiskBlock risk,
            ForecastDto.ReportBlock report) {
    }
}
