package com.cyclovision;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.within;

import com.cyclovision.domain.Provenance;
import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.dto.ForecastDto.VerificationBlock;
import com.cyclovision.dto.InferDto.InferFullResponse;
import com.cyclovision.entity.StormFrame;
import com.cyclovision.service.VerificationService;
import java.lang.reflect.RecordComponent;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Invariant I2 — verification is produced here, from observed data, and never by the AI
 * service. Also checks the arithmetic, because the error figures are the numbers we put
 * on screen and claim as a measured result.
 */
class VerificationServiceTest {

    private final VerificationService service = new VerificationService(null);

    @Test
    @DisplayName("the AI service response type has no verification field")
    void inferResponseCannotCarryVerification() {
        List<String> fields = Arrays.stream(InferFullResponse.class.getRecordComponents())
                .map(RecordComponent::getName)
                .toList();

        assertThat(fields)
                .as("ground truth must not be able to round-trip through inference")
                .doesNotContain("verification")
                .doesNotContain("degraded")
                .doesNotContain("servedFrom");
    }

    @Test
    @DisplayName("track error is the great-circle distance to the observed position")
    void computesTrackError() {
        // Predicted 19.4N 85.7E, observed 19.6N 85.8E — roughly 24 km apart.
        ForecastResponse forecast = TestFixtures.forecastWithTrack(
                TestFixtures.T0, 19.4, 85.7, 104.0, 178.0, 133.0, 0.34);
        StormFrame observed24 =
                TestFixtures.frame(TestFixtures.T0.plusHours(24), 19.6, 85.8, 135.0);

        VerificationBlock v = service.compute(forecast, observed24, null, 125.0);

        assertThat(v.available()).isTrue();
        assertThat(v.trackErrorKm24h()).isCloseTo(24.6, within(2.0));
        assertThat(v.observedAt24h().vmaxKt()).isEqualTo(135.0);
        assertThat(v.source().provenance()).isEqualTo(Provenance.OBSERVED);
    }

    @Test
    @DisplayName("intensity error is the absolute difference in knots")
    void computesIntensityError() {
        ForecastResponse forecast = TestFixtures.forecastWithTrack(
                TestFixtures.T0, 19.4, 85.7, 104.0, 178.0, 133.0, 0.34);
        StormFrame observed24 =
                TestFixtures.frame(TestFixtures.T0.plusHours(24), 19.4, 85.7, 135.0);

        VerificationBlock v = service.compute(forecast, observed24, null, 125.0);

        assertThat(v.intensityErrorKt24h()).isCloseTo(2.0, within(0.001));
    }

    @Test
    @DisplayName("cone containment compares the actual error against the cone radius")
    void computesConeContainment() {
        ForecastResponse tightCone = TestFixtures.forecastWithTrack(
                TestFixtures.T0, 19.4, 85.7, 10.0, 20.0, 133.0, 0.34);
        StormFrame observed24 =
                TestFixtures.frame(TestFixtures.T0.plusHours(24), 19.6, 85.8, 135.0);

        VerificationBlock v = service.compute(tightCone, observed24, null, 125.0);

        assertThat(v.insideConeP67()).isFalse();   // ~24 km error vs a 10 km p67 radius
        assertThat(v.insideConeP90()).isFalse();   // ...and a 20 km p90 radius
    }

    @Test
    @DisplayName("rapid intensification uses the standard 30 kt in 24 h definition")
    void detectsRapidIntensification() {
        ForecastResponse forecast = TestFixtures.forecastWithTrack(
                TestFixtures.T0, 19.4, 85.7, 104.0, 178.0, 155.0, 0.34);

        StormFrame ri = TestFixtures.frame(TestFixtures.T0.plusHours(24), 19.4, 85.7, 155.0);
        assertThat(service.compute(forecast, ri, null, 125.0).riOccurred()).isTrue();

        StormFrame noRi = TestFixtures.frame(TestFixtures.T0.plusHours(24), 19.4, 85.7, 150.0);
        assertThat(service.compute(forecast, noRi, null, 125.0).riOccurred()).isFalse();
    }

    @Test
    @DisplayName("an RI warning is recorded whenever probability crosses the threshold")
    void recordsRiWarning() {
        ForecastResponse warned = TestFixtures.forecastWithTrack(
                TestFixtures.T0, 19.4, 85.7, 104.0, 178.0, 133.0, 0.34);
        ForecastResponse quiet = TestFixtures.forecastWithTrack(
                TestFixtures.T0, 19.4, 85.7, 104.0, 178.0, 133.0, 0.05);
        StormFrame observed24 =
                TestFixtures.frame(TestFixtures.T0.plusHours(24), 19.4, 85.7, 135.0);

        assertThat(service.compute(warned, observed24, null, 125.0).riWarningIssued()).isTrue();
        assertThat(service.compute(quiet, observed24, null, 125.0).riWarningIssued()).isFalse();
    }

    @Test
    @DisplayName("reports unavailable rather than inventing a result when truth is missing")
    void reportsUnavailableWhenRecordEndsEarly() {
        ForecastResponse forecast = TestFixtures.forecastWithTrack(
                TestFixtures.T0, 19.4, 85.7, 104.0, 178.0, 133.0, 0.34);

        VerificationBlock v = service.compute(forecast, null, null, 125.0);

        assertThat(v.available()).isFalse();
        assertThat(v.trackErrorKm24h()).isNull();
        assertThat(v.riOccurred()).isNull();
    }
}
