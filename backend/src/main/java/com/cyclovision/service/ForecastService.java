package com.cyclovision.service;

import com.cyclovision.client.AiServiceClient;
import com.cyclovision.client.AiServiceUnavailableException;
import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.dto.ForecastDto.VerificationBlock;
import com.cyclovision.dto.InferDto.InferFullRequest;
import com.cyclovision.dto.InferDto.InferFullResponse;
import com.cyclovision.dto.InferDto.InferOptions;
import com.cyclovision.entity.StormFrame;
import com.cyclovision.exception.NotFoundException;
import com.cyclovision.repository.StormFrameRepository;
import com.cyclovision.repository.StormRepository;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * Orchestrates a forecast: mask, call, verify, degrade.
 *
 * <p>The order matters. The temporal mask is applied before anything else, verification
 * is applied after the AI service has already returned, and the fallback path exists so
 * that a dead AI service degrades the answer rather than breaking the page.
 *
 * <p>Phase 0 note: persistence of runs, points and analogue matches lands in Phase 3
 * alongside the real pipeline. Until then the cache lookup is wired but always misses,
 * which is honest — there is nothing worth caching from a placeholder.
 */
@Service
public class ForecastService {

    private static final Logger log = LoggerFactory.getLogger(ForecastService.class);

    private final StormRepository stormRepository;
    private final StormFrameRepository frameRepository;
    private final InferRequestBuilder requestBuilder;
    private final AiServiceClient aiServiceClient;
    private final VerificationService verificationService;
    private final DemoFallbackService demoFallbackService;
    private final boolean demoMode;

    public ForecastService(StormRepository stormRepository,
            StormFrameRepository frameRepository,
            InferRequestBuilder requestBuilder,
            AiServiceClient aiServiceClient,
            VerificationService verificationService,
            DemoFallbackService demoFallbackService,
            @Value("${cyclovision.demo-mode:false}") boolean demoMode) {
        this.stormRepository = stormRepository;
        this.frameRepository = frameRepository;
        this.requestBuilder = requestBuilder;
        this.aiServiceClient = aiServiceClient;
        this.verificationService = verificationService;
        this.demoFallbackService = demoFallbackService;
        this.demoMode = demoMode;
    }

    public ForecastResponse forecast(String sid, OffsetDateTime asOf, boolean reveal) {
        if (!stormRepository.existsById(sid)) {
            throw new NotFoundException("STORM_NOT_FOUND", "No storm with sid " + sid);
        }

        // 1. TEMPORAL MASK (invariant I1) — nothing after asOf is even loaded.
        List<StormFrame> masked =
                frameRepository.findBySidAndObsTimeLessThanEqualOrderByObsTimeAsc(sid, asOf);
        if (masked.isEmpty()) {
            throw new NotFoundException("FRAME_NOT_FOUND",
                    "No observations at or before " + asOf + " for storm " + sid);
        }

        // 2. Build the request. The builder re-applies the mask, deliberately.
        InferFullRequest request =
                requestBuilder.build(sid, asOf, masked, InferOptions.defaults());

        // 3. Call the AI service, or degrade.
        ForecastResponse response;
        if (demoMode) {
            response = demoFallbackService.forSid(sid, asOf)
                    .orElseThrow(() -> new NotFoundException("MODEL_NOT_LOADED",
                            "DEMO_MODE is on but no demo scenario exists for " + sid));
        } else {
            try {
                InferFullResponse inferred = aiServiceClient.inferFull(request);
                response = toForecastResponse(inferred, sid, asOf);
            } catch (AiServiceUnavailableException e) {
                log.warn("Falling back for sid={} asOf={}", sid, asOf);
                response = fallback(sid, asOf)
                        .orElseThrow(() -> new AiServiceUnavailableException(
                                "AI service unavailable and no cached or demo result exists",
                                e));
            }
        }

        // 4. Verification (invariant I2) — added here, from the database, never upstream.
        if (reveal) {
            VerificationBlock verification = verificationService.verify(response);
            response = response.withVerification(verification);
        } else {
            response = response.withVerification(null);
        }
        return response;
    }

    private Optional<ForecastResponse> fallback(String sid, OffsetDateTime asOf) {
        // Phase 3 will add the cached-run branch here; the demo scenario is the floor.
        return demoFallbackService.forSid(sid, asOf);
    }

    private static ForecastResponse toForecastResponse(InferFullResponse r, String sid,
            OffsetDateTime asOf) {
        return new ForecastResponse(
                r.sid() == null ? sid : r.sid(),
                r.issuedFor() == null ? asOf : r.issuedFor(),
                r.modelBundleVersion(),
                r.current(),
                r.structure(),
                r.vision(),
                r.intensityForecast(),
                r.trackForecast(),
                r.analogues(),
                r.risk(),
                r.report(),
                null,
                false,
                "live");
    }
}
