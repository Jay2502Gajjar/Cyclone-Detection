package com.cyclovision.controller;

import com.cyclovision.ingestion.service.CycloneIngestionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/internal/ingest")
public class IngestionController {

    private final CycloneIngestionService ingestionService;

    public IngestionController(CycloneIngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getIngestionStatus() {
        return ResponseEntity.ok(ingestionService.getIngestionStatus());
    }

    @PostMapping("/trigger")
    public ResponseEntity<Map<String, Object>> triggerIngestion(
            @RequestParam(required = false) String provider
    ) {
        Map<String, Object> result = ingestionService.runIngestion(provider);
        return ResponseEntity.ok(result);
    }
}
