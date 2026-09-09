package com.cyclovision.dto;

import com.cyclovision.domain.Provenance;
import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * Provenance stamp attached to every analysis block in the API.
 *
 * <p>Mirrors the {@code Source} interface in {@code API_CONTRACT.md}.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Source(
        Provenance provenance,
        String model,
        String version,
        Boolean isTrained,
        MetricInfo metric) {

    /** A held-out metric together with the baseline it is compared against. */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record MetricInfo(
            String name,
            Double value,
            String baseline,
            Double baselineValue,
            Integer n) {
    }

    public static Source observed() {
        return new Source(Provenance.OBSERVED, null, null, null, null);
    }

    public static Source demoData(String model, String version) {
        return new Source(Provenance.DEMO_DATA, model, version, false, null);
    }

    public static Source ruleEngine(String model, String version) {
        return new Source(Provenance.RULE_ENGINE, model, version, false, null);
    }

    /**
     * Mirrors the AI service's registry rule: a model that is not trained can never
     * claim {@link Provenance#TRAINED_MODEL}. Applied defensively on this side too, so
     * a mislabelled upstream response cannot reach the browser.
     */
    public Source enforceTrainedFlag() {
        if (provenance == Provenance.TRAINED_MODEL && !Boolean.TRUE.equals(isTrained)) {
            return new Source(Provenance.DEMO_DATA, model, version, false, metric);
        }
        return this;
    }
}
