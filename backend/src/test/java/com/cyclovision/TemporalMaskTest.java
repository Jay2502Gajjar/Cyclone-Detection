package com.cyclovision;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.cyclovision.dto.InferDto.InferFullRequest;
import com.cyclovision.dto.InferDto.InferOptions;
import com.cyclovision.entity.StormFrame;
import com.cyclovision.service.InferRequestBuilder;
import java.time.OffsetDateTime;
import java.util.List;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Invariant I1 — the temporal mask.
 *
 * <p>This is the most important test in the backend. Rewind &amp; Verify only means
 * anything if the forecast genuinely could not see the future, and a leak here would be
 * invisible in a demo: the numbers would simply look impressively good. So the builder
 * is tested directly, against inputs that deliberately contain future observations.
 */
class TemporalMaskTest {

    private final InferRequestBuilder builder = new InferRequestBuilder();

    @Test
    @DisplayName("history never contains an observation later than asOf")
    void dropsFutureObservations() {
        List<StormFrame> frames = TestFixtures.sequenceAround(TestFixtures.T0, 8, 8);

        InferFullRequest request = builder.build(TestFixtures.SID, TestFixtures.T0, frames,
                InferOptions.defaults());

        assertThat(request.history()).isNotEmpty();
        assertThat(request.history())
                .allSatisfy(h -> assertThat(h.t()).isBeforeOrEqualTo(TestFixtures.T0));
        assertThat(request.asOf()).isEqualTo(TestFixtures.T0);
    }

    @Test
    @DisplayName("the boundary observation at exactly asOf is kept")
    void keepsBoundaryObservation() {
        List<StormFrame> frames = TestFixtures.sequenceAround(TestFixtures.T0, 4, 4);

        InferFullRequest request = builder.build(TestFixtures.SID, TestFixtures.T0, frames,
                InferOptions.defaults());

        assertThat(request.history()).extracting(h -> h.t()).contains(TestFixtures.T0);
    }

    @Test
    @DisplayName("history is ordered even when the input is not")
    void ordersHistory() {
        List<StormFrame> frames = new java.util.ArrayList<>(
                TestFixtures.sequenceAround(TestFixtures.T0, 6, 6));
        java.util.Collections.shuffle(frames, new java.util.Random(42));

        InferFullRequest request = builder.build(TestFixtures.SID, TestFixtures.T0, frames,
                InferOptions.defaults());

        List<OffsetDateTime> times = request.history().stream().map(h -> h.t()).toList();
        assertThat(times).isSorted();
    }

    @Test
    @DisplayName("a frame reference is never taken from the future")
    void frameRefIsNotFromTheFuture() {
        List<StormFrame> frames = new java.util.ArrayList<>();
        StormFrame past = TestFixtures.frame(TestFixtures.T0.minusHours(3), 17.0, 85.0, 120.0);
        past.setBtPath("frames/" + TestFixtures.SID + "/past.npy");
        StormFrame future = TestFixtures.frame(TestFixtures.T0.plusHours(3), 18.0, 85.5, 130.0);
        future.setBtPath("frames/" + TestFixtures.SID + "/future.npy");
        frames.add(past);
        frames.add(future);

        InferFullRequest request = builder.build(TestFixtures.SID, TestFixtures.T0, frames,
                InferOptions.defaults());

        assertThat(request.frameRef()).isNotNull();
        assertThat(request.frameRef().btPath()).contains("past.npy");
    }

    @Test
    @DisplayName("refuses to build a request with no observable history")
    void rejectsEmptyHistory() {
        List<StormFrame> onlyFuture = List.of(
                TestFixtures.frame(TestFixtures.T0.plusHours(3), 18.0, 85.5, 130.0));

        assertThatThrownBy(() -> builder.build(TestFixtures.SID, TestFixtures.T0, onlyFuture,
                InferOptions.defaults()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("No observations at or before");
    }

    @Test
    @DisplayName("the request type carries no field that could hold ground truth")
    void requestCarriesNoGroundTruth() {
        // Invariant I2, checked structurally: if someone adds a verification-shaped field
        // to the inference contract, this fails and the reason is stated here.
        List<String> fieldNames = java.util.Arrays.stream(
                        InferFullRequest.class.getRecordComponents())
                .map(java.lang.reflect.RecordComponent::getName)
                .toList();

        assertThat(fieldNames)
                .as("the AI service must never be handed observed future outcomes")
                .containsExactlyInAnyOrder("sid", "asOf", "history", "frameRef", "options");
    }
}
