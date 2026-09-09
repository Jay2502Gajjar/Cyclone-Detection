package com.cyclovision.repository;

import com.cyclovision.entity.StormFrame;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StormFrameRepository extends JpaRepository<StormFrame, Long> {

    /** Whole lifetime, ordered — powers the scrubber and the intensity sparkline. */
    List<StormFrame> findBySidOrderByObsTimeAsc(String sid);

    /**
     * <b>Invariant I1 — the temporal mask.</b> The only query used to assemble a
     * forecast request. Nothing later than {@code asOf} can be returned, so nothing
     * later than {@code asOf} can reach the AI service.
     */
    List<StormFrame> findBySidAndObsTimeLessThanEqualOrderByObsTimeAsc(
            String sid, OffsetDateTime asOf);

    Optional<StormFrame> findBySidAndObsTime(String sid, OffsetDateTime obsTime);

    /**
     * Nearest observation at or after a target time. Used by verification only, and
     * only from {@code VerificationService} — never while building a forecast request.
     */
    Optional<StormFrame> findFirstBySidAndObsTimeGreaterThanEqualOrderByObsTimeAsc(
            String sid, OffsetDateTime from);

    long countBySid(String sid);

    long countBySidAndImagePathIsNotNull(String sid);
}
