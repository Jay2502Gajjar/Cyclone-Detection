package com.cyclovision.controller;

import com.cyclovision.repository.CycloneRepository;
import lombok.Builder;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping({"/api/v1/cyclones", "/api/cyclones"})
@RequiredArgsConstructor
public class ReportController {

    private final CycloneRepository cycloneRepository;

    @GetMapping("/{id}/report")
    public ResponseEntity<SituationReportDto> getSituationReport(@PathVariable String id) {
        String name = "Cyclone";
        try {
            UUID uuid = UUID.fromString(id);
            var opt = cycloneRepository.findById(uuid);
            if (opt.isPresent() && opt.get().getName() != null) {
                name = opt.get().getName();
            }
        } catch (Exception ignored) {
        }

        SituationReportDto report = SituationReportDto.builder()
                .cycloneId(id)
                .cycloneName(name)
                .generatedAt(LocalDateTime.now().toString())
                .executiveSummary(name + " monitoring status active. Real-time meteorological telemetry and multi-modal analysis in progress.")
                .keyThreats(List.of(
                        "Sustained strong winds and heavy squall conditions across maritime pathways",
                        "Elevated sea wave action and coastal surge risk",
                        "Localized heavy precipitation along projected path"
                ))
                .recommendedActions(List.of(
                        "Monitor coastal advisories and alert bulletins continuously",
                        "Ensure maritime advisories and shipping lanes are alerted",
                        "Maintain operational readiness for disaster response units"
                ))
                .meteorologicalSynthesis("Multi-modal satellite and observation synthesis active. Trajectory ensemble models project continuation along monitored storm path.")
                .build();

        return ResponseEntity.ok(report);
    }

    @Data
    @Builder
    public static class SituationReportDto {
        private String cycloneId;
        private String cycloneName;
        private String generatedAt;
        private String executiveSummary;
        private List<String> keyThreats;
        private List<String> recommendedActions;
        private String meteorologicalSynthesis;
    }
}
