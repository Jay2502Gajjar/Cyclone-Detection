package com.cyclovision.controller;

import com.cyclovision.dto.ForecastDto.ForecastResponse;
import com.cyclovision.service.ForecastService;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Rewind &amp; Verify.
 *
 * <p>{@code from} is the temporal-mask boundary T: the forecast is produced using only
 * observations at or before it. {@code reveal} controls whether ground truth is attached
 * afterwards — it never affects what the AI service is given.
 */
@RestController
@RequestMapping("/api/storms")
public class ForecastController {

    private final ForecastService forecastService;

    public ForecastController(ForecastService forecastService) {
        this.forecastService = forecastService;
    }

    @PostMapping("/{sid}/forecast")
    public ForecastResponse forecast(
            @PathVariable String sid,
            @RequestParam("from") String from,
            @RequestParam(name = "reveal", defaultValue = "false") boolean reveal) {
        return forecastService.forecast(sid, StormController.parseTime(from), reveal);
    }
}
