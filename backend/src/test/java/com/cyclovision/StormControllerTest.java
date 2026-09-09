package com.cyclovision;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.cyclovision.controller.StormController;
import com.cyclovision.dto.Source;
import com.cyclovision.dto.StormDto.StormDetail;
import com.cyclovision.dto.StormDto.TrackFrame;
import com.cyclovision.exception.GlobalExceptionHandler;
import com.cyclovision.exception.NotFoundException;
import com.cyclovision.service.StormService;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;

/**
 * The read path's contract, checked at the HTTP boundary.
 *
 * <p>A slice test with a mocked service, so it runs without a database. What it protects
 * is the JSON shape the frontend's generated types are written against.
 */
@WebMvcTest(controllers = StormController.class)
@Import(GlobalExceptionHandler.class)
class StormControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private StormService stormService;

    private StormDetail detail() {
        TrackFrame frame = new TrackFrame(TestFixtures.T0, 17.2, 85.1, 125.0, 936.0,
                "EXTREMELY_SEVERE", "/media/frames/x.png", true, 118.0, "EYE");
        return new StormDetail(TestFixtures.SID, "FANI", "NI", 2019,
                TestFixtures.T0.minusDays(6), TestFixtures.T0.plusDays(3), 135.0,
                "EXTREMELY_SEVERE", 1, 1, true, "test", null, List.of(frame),
                Map.of("track", Source.observed()));
    }

    @Test
    @DisplayName("storm detail returns the whole frame index in one call")
    void returnsStormDetail() throws Exception {
        when(stormService.getStorm(anyString())).thenReturn(detail());

        mockMvc.perform(get("/api/storms/" + TestFixtures.SID))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.sid").value(TestFixtures.SID))
                .andExpect(jsonPath("$.name").value("FANI"))
                .andExpect(jsonPath("$.split").value("test"))
                .andExpect(jsonPath("$.frames[0].cnnVmaxKt").value(118.0))
                .andExpect(jsonPath("$.frames[0].regime").value("EYE"))
                .andExpect(jsonPath("$.sources.track.provenance").value("OBSERVED"));
    }

    @Test
    @DisplayName("demo storms are reported as held out, so verification stays meaningful")
    void demoStormIsHeldOut() throws Exception {
        when(stormService.getStorm(anyString())).thenReturn(detail());

        mockMvc.perform(get("/api/storms/" + TestFixtures.SID))
                .andExpect(jsonPath("$.isDemo").value(true))
                .andExpect(jsonPath("$.split").value("test"));
    }

    @Test
    @DisplayName("an unknown storm returns the shared error envelope")
    void unknownStormReturnsApiError() throws Exception {
        when(stormService.getStorm(anyString()))
                .thenThrow(new NotFoundException("STORM_NOT_FOUND", "No storm with sid nope"));

        mockMvc.perform(get("/api/storms/nope"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("STORM_NOT_FOUND"));
    }

    @Test
    @DisplayName("a malformed timestamp is rejected before it reaches the service")
    void rejectsMalformedTime() throws Exception {
        mockMvc.perform(get("/api/storms/" + TestFixtures.SID + "/frames/not-a-time"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_TIME"));
    }

    @Test
    @DisplayName("a valid ISO instant reaches the service")
    void acceptsIsoInstant() throws Exception {
        when(stormService.getFrame(anyString(), any(OffsetDateTime.class)))
                .thenThrow(new NotFoundException("FRAME_NOT_FOUND", "none"));

        mockMvc.perform(get("/api/storms/" + TestFixtures.SID
                        + "/frames/2019-05-02T06:00:00Z"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("FRAME_NOT_FOUND"));
    }
}
