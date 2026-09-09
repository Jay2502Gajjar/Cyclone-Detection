package com.cyclovision;

import static org.assertj.core.api.Assertions.assertThat;

import com.cyclovision.domain.Provenance;
import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.dto.FrameDto.FrameAnalysis;
import com.cyclovision.dto.Source;
import java.lang.reflect.RecordComponent;
import java.util.Arrays;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * The provenance system, checked on the Spring side.
 *
 * <p>The AI service's registry is the primary enforcement point for invariant I3, but a
 * mislabelled response must not be able to reach the browser either, so the rule is
 * applied defensively here as well.
 */
class ProvenanceTest {

    @Test
    @DisplayName("an untrained model cannot claim TRAINED_MODEL")
    void downgradesUntrainedTrainedModelClaims() {
        Source dishonest = new Source(Provenance.TRAINED_MODEL, "ir_intensity", "phase0",
                false, null);

        assertThat(dishonest.enforceTrainedFlag().provenance())
                .isEqualTo(Provenance.DEMO_DATA);
    }

    @Test
    @DisplayName("a genuinely trained model keeps its claim")
    void keepsHonestTrainedModelClaims() {
        Source honest = new Source(Provenance.TRAINED_MODEL, "ir_intensity", "v1.2", true,
                new Source.MetricInfo("MAE (kt)", 12.4, "mean predictor", 24.1, 1204));

        assertThat(honest.enforceTrainedFlag().provenance())
                .isEqualTo(Provenance.TRAINED_MODEL);
    }

    @Test
    @DisplayName("non-model provenance tags pass through untouched")
    void leavesOtherProvenanceAlone() {
        for (Provenance p : Provenance.values()) {
            if (p == Provenance.TRAINED_MODEL) {
                continue;
            }
            Source s = new Source(p, "structure", "phase0", false, null);
            assertThat(s.enforceTrainedFlag().provenance()).isEqualTo(p);
        }
    }

    @Test
    @DisplayName("every analysis block in the forecast response carries a provenance stamp")
    void everyBlockIsStamped() {
        // Blocks that represent an analysis result must be stampable. If a new block is
        // added without a Source, this test names it.
        assertHasSource(com.cyclovision.dto.FrameDto.ObservedBlock.class, "source");
        assertHasSource(com.cyclovision.dto.FrameDto.VisionBlock.class, "source");
        assertHasSource(com.cyclovision.dto.ForecastDto.IntensityForecast.class, "source");
        assertHasSource(com.cyclovision.dto.ForecastDto.AnalogueBlock.class, "source");
        assertHasSource(com.cyclovision.dto.ForecastDto.RiskBlock.class, "source");
        assertHasSource(com.cyclovision.dto.ForecastDto.ReportBlock.class, "source");
        assertHasSource(com.cyclovision.dto.ForecastDto.VerificationBlock.class, "source");

        // Structure carries two stamps: the measurements and the rule-based label on top
        // of them have different standing and must not be conflated.
        assertHasSource(com.cyclovision.dto.FrameDto.StructureBlock.class, "metricsSource");
        assertHasSource(com.cyclovision.dto.FrameDto.StructureBlock.class, "regimeSource");

        // The track forecast separates the prediction from the empirical cone.
        assertHasSource(com.cyclovision.dto.ForecastDto.TrackForecast.class, "source");
        assertHasSource(com.cyclovision.dto.ForecastDto.TrackForecast.class, "coneSource");
    }

    @Test
    @DisplayName("delivery metadata is present so demo and cached answers are visible")
    void responseCarriesDeliveryMetadata() {
        var fields = Arrays.stream(ForecastResponse.class.getRecordComponents())
                .map(RecordComponent::getName).toList();
        assertThat(fields).contains("degraded", "servedFrom", "verification");

        var frameFields = Arrays.stream(FrameAnalysis.class.getRecordComponents())
                .map(RecordComponent::getName).toList();
        assertThat(frameFields).contains("structure", "vision", "observed");
    }

    private static void assertHasSource(Class<?> recordType, String fieldName) {
        var names = Arrays.stream(recordType.getRecordComponents())
                .map(RecordComponent::getName).toList();
        assertThat(names)
                .as("%s must carry a provenance stamp called '%s'",
                        recordType.getSimpleName(), fieldName)
                .contains(fieldName);
    }
}
