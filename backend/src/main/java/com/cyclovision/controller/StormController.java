package com.cyclovision.controller;

import com.cyclovision.dto.FrameDto.FrameAnalysis;
import com.cyclovision.dto.StormDto.StormDetail;
import com.cyclovision.dto.StormDto.StormSummary;
import com.cyclovision.service.StormService;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** The read path: storm list, storm detail (whole timeline), one frame's analysis. */
@RestController
@RequestMapping("/api/storms")
public class StormController {

    private final StormService stormService;

    public StormController(StormService stormService) {
        this.stormService = stormService;
    }

    @GetMapping
    public List<StormSummary> list() {
        return stormService.listStorms();
    }

    /** Metadata plus the whole thin frame index — one call, so the scrubber never waterfalls. */
    @GetMapping("/{sid}")
    public StormDetail get(@PathVariable String sid) {
        return stormService.getStorm(sid);
    }

    @GetMapping("/{sid}/frames/{isoTime}")
    public FrameAnalysis frame(@PathVariable String sid, @PathVariable String isoTime) {
        return stormService.getFrame(sid, parseTime(isoTime));
    }

    static OffsetDateTime parseTime(String iso) {
        try {
            return OffsetDateTime.parse(iso);
        } catch (DateTimeParseException e) {
            throw new IllegalArgumentException(
                    "Expected an ISO-8601 instant with offset, got: " + iso);
        }
    }
}
