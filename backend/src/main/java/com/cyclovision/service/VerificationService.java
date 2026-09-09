package com.cyclovision.service;

import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.dto.ForecastDto.ObservedPoint;
import com.cyclovision.dto.ForecastDto.TrackPointDto;
import com.cyclovision.dto.ForecastDto.VerificationBlock;
import com.cyclovision.dto.Source;
import com.cyclovision.entity.StormFrame;
import com.cyclovision.repository.StormFrameRepository;
import com.cyclovision.util.GeoUtil;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Service;

/**
 * Turns a forecast into a measured result by comparing it against what actually
 * happened. This is what makes Rewind &amp; Verify a demonstration rather than a claim.
 *
 * <p><b>Invariant I2:</b> the verification block is assembled here, from the database,
 * and nowhere else. The AI service has no field for it in either direction, so ground
 * truth cannot round-trip through inference.
 */
@Service
public class VerificationService {

    /** Rapid intensification: the standard operational definition, ≥30 kt in 24 h. */
    public static final double RI_THRESHOLD_KT = 30.0;

    /** A forecast is treated as warning of RI at or above this probability. */
    public static final double RI_WARNING_PROBABILITY = 0.25;

    private final StormFrameRepository frameRepository;

    public VerificationService(StormFrameRepository frameRepository) {
        this.frameRepository = frameRepository;
    }

    /**
     * Looks up ground truth for a forecast and returns the measured errors.
     *
     * @return an unavailable block when the storm record does not extend far enough past
     *         T — never a fabricated one
     */
    public VerificationBlock verify(ForecastResponse forecast) {
        OffsetDateTime t = forecast.issuedFor();
        Optional<StormFrame> at24 = frameRepository
                .findFirstBySidAndObsTimeGreaterThanEqualOrderByObsTimeAsc(
                        forecast.sid(), t.plusHours(24));
        Optional<StormFrame> at48 = frameRepository
                .findFirstBySidAndObsTimeGreaterThanEqualOrderByObsTimeAsc(
                        forecast.sid(), t.plusHours(48));

        Double vmaxAtT = forecast.current() == null ? null : forecast.current().vmaxKt();
        return compute(forecast, at24.orElse(null), at48.orElse(null), vmaxAtT);
    }

    /**
     * The measurement itself, as a pure function so it can be tested on fixtures.
     *
     * @param observed24 observed frame nearest T+24h, or null if the record ends first
     * @param observed48 observed frame nearest T+48h, or null
     * @param vmaxAtT    observed intensity at T, needed to decide whether RI occurred
     */
    public VerificationBlock compute(ForecastResponse forecast, StormFrame observed24,
            StormFrame observed48, Double vmaxAtT) {

        if (observed24 == null && observed48 == null) {
            return VerificationBlock.unavailable();
        }

        TrackPointDto predicted24 = pointAt(forecast, 24);
        TrackPointDto predicted48 = pointAt(forecast, 48);

        Double trackError24 = trackError(predicted24, observed24);
        Double trackError48 = trackError(predicted48, observed48);

        Double intensityError24 = null;
        if (observed24 != null && observed24.getVmaxKt() != null
                && forecast.intensityForecast() != null
                && forecast.intensityForecast().predictedVmax24hKt() != null) {
            intensityError24 = Math.abs(
                    forecast.intensityForecast().predictedVmax24hKt() - observed24.getVmaxKt());
        }

        Boolean insideP67 = containment(trackError24, predicted24 == null
                ? null : predicted24.coneRadiusP67Km());
        Boolean insideP90 = containment(trackError24, predicted24 == null
                ? null : predicted24.coneRadiusP90Km());

        Boolean riOccurred = null;
        if (vmaxAtT != null && observed24 != null && observed24.getVmaxKt() != null) {
            riOccurred = (observed24.getVmaxKt() - vmaxAtT) >= RI_THRESHOLD_KT;
        }

        Boolean riWarningIssued = null;
        if (forecast.intensityForecast() != null
                && forecast.intensityForecast().riProbability() != null) {
            riWarningIssued =
                    forecast.intensityForecast().riProbability() >= RI_WARNING_PROBABILITY;
        }

        return new VerificationBlock(
                true,
                toObservedPoint(observed24),
                toObservedPoint(observed48),
                trackError24,
                trackError48,
                intensityError24,
                insideP67,
                insideP90,
                riOccurred,
                riWarningIssued,
                Source.observed());
    }

    private static Double trackError(TrackPointDto predicted, StormFrame observed) {
        if (predicted == null || observed == null) {
            return null;
        }
        return GeoUtil.haversineKm(predicted.lat(), predicted.lon(),
                observed.getLat(), observed.getLon());
    }

    private static Boolean containment(Double errorKm, Double radiusKm) {
        if (errorKm == null || radiusKm == null) {
            return null;
        }
        return errorKm <= radiusKm;
    }

    private static TrackPointDto pointAt(ForecastResponse forecast, int leadHours) {
        if (forecast.trackForecast() == null || forecast.trackForecast().points() == null) {
            return null;
        }
        List<TrackPointDto> points = forecast.trackForecast().points();
        return points.stream().filter(p -> p.leadHours() == leadHours).findFirst().orElse(null);
    }

    private static ObservedPoint toObservedPoint(StormFrame f) {
        if (f == null) {
            return null;
        }
        return new ObservedPoint(f.getObsTime(), f.getLat(), f.getLon(), f.getVmaxKt());
    }
}
