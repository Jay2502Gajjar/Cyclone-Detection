package com.cyclovision.service;

import com.cyclovision.dto.InferDto.FrameRef;
import com.cyclovision.dto.InferDto.HistoryPoint;
import com.cyclovision.dto.InferDto.InferFullRequest;
import com.cyclovision.dto.InferDto.InferOptions;
import com.cyclovision.entity.StormFrame;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Component;

/**
 * Builds the request sent to the AI service, and is the place invariant I1 is enforced.
 *
 * <p>This is a pure function of (frames, asOf) with no repository or network access, so
 * {@code TemporalMaskTest} can assert the mask directly without a database.
 *
 * <p>The repository query already filters to {@code obs_time <= asOf}. This class
 * filters <em>again</em>, deliberately. The redundancy is the point: leaking the future
 * into a hindcast would silently invalidate every verification number the product
 * reports, and that failure would be invisible in a demo. Two independent filters mean
 * two independent mistakes are required.
 */
@Component
public class InferRequestBuilder {

    /**
     * @param frames candidate frames, in any order; anything after {@code asOf} is dropped
     * @param asOf   the temporal-mask boundary T
     * @throws IllegalArgumentException if no observation exists at or before {@code asOf}
     */
    public InferFullRequest build(String sid, OffsetDateTime asOf, List<StormFrame> frames,
            InferOptions options) {

        List<HistoryPoint> history = frames.stream()
                .filter(f -> f.getObsTime() != null && !f.getObsTime().isAfter(asOf))
                .sorted(java.util.Comparator.comparing(StormFrame::getObsTime))
                .map(InferRequestBuilder::toHistoryPoint)
                .toList();

        if (history.isEmpty()) {
            throw new IllegalArgumentException(
                    "No observations at or before " + asOf + " for storm " + sid);
        }

        FrameRef frameRef = frames.stream()
                .filter(f -> f.getObsTime() != null && !f.getObsTime().isAfter(asOf))
                .filter(f -> f.getBtPath() != null || f.getImagePath() != null)
                .max(java.util.Comparator.comparing(StormFrame::getObsTime))
                .map(InferRequestBuilder::toFrameRef)
                .orElse(null);

        return new InferFullRequest(sid, asOf, history, frameRef,
                Optional.ofNullable(options).orElseGet(InferOptions::defaults));
    }

    private static HistoryPoint toHistoryPoint(StormFrame f) {
        return new HistoryPoint(
                f.getObsTime(),
                f.getLat(),
                f.getLon(),
                f.getVmaxKt(),
                f.getPressureHpa(),
                f.getTranslationSpeedKt(),
                f.getHeadingDeg(),
                f.getDistToCoastKm());
    }

    private static FrameRef toFrameRef(StormFrame f) {
        return new FrameRef(
                f.getBtPath(),
                f.getImagePath() == null ? null : "/media/" + f.getImagePath(),
                f.getImageTime(),
                f.getImageSource());
    }
}
