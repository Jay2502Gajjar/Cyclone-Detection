package com.cyclovision;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.cyclovision.client.AiServiceClient;
import com.cyclovision.client.AiServiceUnavailableException;
import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.entity.StormFrame;
import com.cyclovision.repository.StormFrameRepository;
import com.cyclovision.repository.StormRepository;
import com.cyclovision.service.DemoFallbackService;
import com.cyclovision.service.ForecastService;
import com.cyclovision.service.InferRequestBuilder;
import com.cyclovision.service.VerificationService;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * A dead AI service must degrade the answer, not break the page.
 *
 * <p>This is rehearsed deliberately: killing the AI service mid-demo is a realistic
 * failure, and the correct behaviour is a labelled fallback rather than a stack trace on
 * a projector.
 */
class ForecastFallbackTest {

    private StormRepository stormRepository;
    private StormFrameRepository frameRepository;
    private AiServiceClient aiServiceClient;
    private DemoFallbackService demoFallbackService;
    private VerificationService verificationService;

    @BeforeEach
    void setUp() {
        stormRepository = mock(StormRepository.class);
        frameRepository = mock(StormFrameRepository.class);
        aiServiceClient = mock(AiServiceClient.class);
        demoFallbackService = mock(DemoFallbackService.class);
        verificationService = mock(VerificationService.class);

        when(stormRepository.existsById(TestFixtures.SID)).thenReturn(true);
        List<StormFrame> masked = TestFixtures.sequenceAround(TestFixtures.T0, 8, 0);
        when(frameRepository.findBySidAndObsTimeLessThanEqualOrderByObsTimeAsc(
                eq(TestFixtures.SID), any(OffsetDateTime.class))).thenReturn(masked);
    }

    private ForecastService service(boolean demoMode) {
        return new ForecastService(stormRepository, frameRepository,
                new InferRequestBuilder(), aiServiceClient, verificationService,
                demoFallbackService, demoMode);
    }

    @Test
    @DisplayName("AI service failure falls back to a demo scenario, labelled as such")
    void degradesToDemoScenario() {
        when(aiServiceClient.inferFull(any()))
                .thenThrow(new AiServiceUnavailableException("connection refused"));
        when(demoFallbackService.forSid(anyString(), any()))
                .thenReturn(Optional.of(TestFixtures
                        .forecastWithTrack(TestFixtures.T0, 19.4, 85.7, 104.0, 178.0,
                                133.0, 0.34)
                        .withDelivery(true, "demo")));

        ForecastResponse response = service(false).forecast(TestFixtures.SID, TestFixtures.T0,
                false);

        assertThat(response.degraded()).isTrue();
        assertThat(response.servedFrom()).isEqualTo("demo");
        assertThat(response.verification()).isNull();
    }

    @Test
    @DisplayName("with no fallback available it fails loudly instead of fabricating output")
    void failsRatherThanFabricate() {
        when(aiServiceClient.inferFull(any()))
                .thenThrow(new AiServiceUnavailableException("connection refused"));
        when(demoFallbackService.forSid(anyString(), any())).thenReturn(Optional.empty());

        assertThatThrownBy(() ->
                service(false).forecast(TestFixtures.SID, TestFixtures.T0, false))
                .isInstanceOf(AiServiceUnavailableException.class);
    }

    @Test
    @DisplayName("DEMO_MODE never reaches the AI service at all")
    void demoModeBypassesAiService() {
        when(demoFallbackService.forSid(anyString(), any()))
                .thenReturn(Optional.of(TestFixtures
                        .forecastWithTrack(TestFixtures.T0, 19.4, 85.7, 104.0, 178.0,
                                133.0, 0.34)
                        .withDelivery(true, "demo")));

        ForecastResponse response = service(true).forecast(TestFixtures.SID, TestFixtures.T0,
                false);

        assertThat(response.servedFrom()).isEqualTo("demo");
        org.mockito.Mockito.verify(aiServiceClient, org.mockito.Mockito.never())
                .inferFull(any());
    }

    @Test
    @DisplayName("a storm with no observations before T is a 404, not an empty forecast")
    void rejectsUnobservableTime() {
        when(frameRepository.findBySidAndObsTimeLessThanEqualOrderByObsTimeAsc(
                eq(TestFixtures.SID), any(OffsetDateTime.class))).thenReturn(List.of());

        assertThatThrownBy(() ->
                service(false).forecast(TestFixtures.SID, TestFixtures.T0, false))
                .isInstanceOf(com.cyclovision.exception.NotFoundException.class);
    }
}
