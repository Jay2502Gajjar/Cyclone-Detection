package com.cyclovision.dto;

import com.cyclovision.domain.Provenance;
import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.OffsetDateTime;
import java.util.List;

/**
 * The credibility screen's payload.
 *
 * <p>Built from {@code models/metrics.json} plus the {@code model_registry} table. The
 * {@code notBuilt} list is not decoration: it pre-answers the hardest questions a
 * technical judge can ask, and it is the reason we can decline to overclaim elsewhere.
 */
public final class ModelCardDto {

    private ModelCardDto() {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record DatasetInfo(
            String name,
            String source,
            String licence,
            int stormCount,
            int frameCount,
            Double matchRatePct,
            String note) {
    }

    public record SplitInfo(
            String strategy,            // always "storm-wise"
            int train,
            int val,
            int test,
            boolean demoStormsInTest) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record ModelRow(
            String key,
            String version,
            Provenance provenance,
            boolean isTrained,
            String metric,
            Double value,
            String baseline,
            Double baselineValue,
            Integer n,
            String notes) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record AblationRow(
            String setting,             // track-only | image-only | fused
            Double maeKt,
            Integer n) {
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record ConeCalibrationRow(
            int leadHours,
            Double p67Km,
            Double p90Km,
            Double observedContainmentP67,
            Integer n) {
    }

    public record NotBuiltRow(String item, String reason) {
    }

    public record ModelCard(
            String bundleVersion,
            OffsetDateTime generatedAt,
            List<DatasetInfo> datasets,
            SplitInfo split,
            List<ModelRow> models,
            List<AblationRow> ablation,
            List<ConeCalibrationRow> coneCalibration,
            List<NotBuiltRow> notBuilt) {
    }
}
