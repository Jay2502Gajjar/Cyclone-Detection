package com.cyclovision.service;

import com.cyclovision.domain.Provenance;
import com.cyclovision.dto.FrameDto.FrameAnalysis;
import com.cyclovision.dto.FrameDto.ObservedBlock;
import com.cyclovision.dto.FrameDto.StructureBlock;
import com.cyclovision.dto.FrameDto.VisionBlock;
import com.cyclovision.dto.Source;
import com.cyclovision.dto.StormDto.Landfall;
import com.cyclovision.dto.StormDto.StormDetail;
import com.cyclovision.dto.StormDto.StormSummary;
import com.cyclovision.dto.StormDto.TrackFrame;
import com.cyclovision.entity.Storm;
import com.cyclovision.entity.StormFrame;
import com.cyclovision.exception.NotFoundException;
import com.cyclovision.repository.StormFrameRepository;
import com.cyclovision.repository.StormRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * The read path. Serves precomputed data only.
 *
 * <p><b>Invariant I5:</b> nothing here calls the AI service. The timeline scrubber is
 * the most-used control in the demo, so it reads rows that
 * {@code ml/precompute/precompute_frames.py} already wrote. That keeps scrubbing instant
 * and keeps a dead AI service from breaking the primary interaction.
 */
@Service
public class StormService {

    private final StormRepository stormRepository;
    private final StormFrameRepository frameRepository;
    private final ObjectMapper objectMapper;

    public StormService(StormRepository stormRepository, StormFrameRepository frameRepository,
            ObjectMapper objectMapper) {
        this.stormRepository = stormRepository;
        this.frameRepository = frameRepository;
        this.objectMapper = objectMapper;
    }

    @Transactional(readOnly = true)
    public List<StormSummary> listStorms() {
        return stormRepository.findAllByOrderBySeasonYearDescNameAsc().stream()
                .map(this::toSummary)
                .toList();
    }

    @Transactional(readOnly = true)
    public StormDetail getStorm(String sid) {
        Storm storm = stormRepository.findById(sid)
                .orElseThrow(() -> new NotFoundException("STORM_NOT_FOUND",
                        "No storm with sid " + sid));

        List<StormFrame> frames = frameRepository.findBySidOrderByObsTimeAsc(sid);
        List<TrackFrame> trackFrames = frames.stream().map(this::toTrackFrame).toList();

        Landfall landfall = null;
        if (storm.getLandfallTime() != null && storm.getLandfallLat() != null
                && storm.getLandfallLon() != null) {
            landfall = new Landfall(storm.getLandfallTime(), storm.getLandfallLat(),
                    storm.getLandfallLon(), storm.getLandfallPlace());
        }

        Map<String, Source> sources = new LinkedHashMap<>();
        sources.put("track", Source.observed());
        sources.put("cnnVmaxKt", sourceFromFrames(frames, "vision"));
        sources.put("regime", sourceFromFrames(frames, "structure"));

        int withImagery = (int) frames.stream().filter(f -> f.getImagePath() != null).count();

        return new StormDetail(storm.getSid(), storm.getName(), storm.getBasin(),
                storm.getSeasonYear(), storm.getStartTime(), storm.getEndTime(),
                storm.getPeakVmaxKt(), storm.getPeakCategory(), frames.size(), withImagery,
                storm.isDemo(), storm.getSplit(), landfall, trackFrames, sources);
    }

    @Transactional(readOnly = true)
    public FrameAnalysis getFrame(String sid, OffsetDateTime t) {
        StormFrame frame = frameRepository.findBySidAndObsTime(sid, t)
                .orElseThrow(() -> new NotFoundException("FRAME_NOT_FOUND",
                        "No frame for storm " + sid + " at " + t));
        return toFrameAnalysis(frame);
    }

    // --- mapping ---------------------------------------------------------------

    private StormSummary toSummary(Storm s) {
        return new StormSummary(s.getSid(), s.getName(), s.getBasin(), s.getSeasonYear(),
                s.getStartTime(), s.getEndTime(), s.getPeakVmaxKt(), s.getPeakCategory(),
                (int) frameRepository.countBySid(s.getSid()),
                (int) frameRepository.countBySidAndImagePathIsNotNull(s.getSid()),
                s.isDemo(), s.getSplit());
    }

    private TrackFrame toTrackFrame(StormFrame f) {
        JsonNode analysis = readAnalysis(f);
        Double cnnVmax = analysis == null ? null
                : optDouble(analysis.path("vision").path("vmaxKt"));
        String regime = analysis == null ? null
                : optText(analysis.path("structure").path("regime"));

        return new TrackFrame(f.getObsTime(), f.getLat(), f.getLon(), f.getVmaxKt(),
                f.getPressureHpa(), f.getCategory(), mediaUrl(f.getImagePath()),
                analysis != null, cnnVmax, regime);
    }

    private FrameAnalysis toFrameAnalysis(StormFrame f) {
        ObservedBlock observed = new ObservedBlock(f.getLat(), f.getLon(), f.getVmaxKt(),
                f.getPressureHpa(), f.getCategory(), f.getDistToCoastKm(), Source.observed());

        JsonNode analysis = readAnalysis(f);
        StructureBlock structure;
        VisionBlock vision;

        if (analysis == null) {
            // No precomputed analysis: report absence rather than inventing values.
            Source notComputed = Source.demoData(null, f.getAnalysisVersion());
            structure = StructureBlock.empty(notComputed, notComputed);
            vision = VisionBlock.empty(notComputed);
        } else {
            structure = readStructure(analysis.path("structure"));
            vision = readVision(analysis.path("vision"), f.getGradcamPath());
        }

        return new FrameAnalysis(f.getSid(), f.getObsTime(), observed,
                mediaUrl(f.getImagePath()), f.getImageTime(), f.getImageSource(),
                structure, vision, f.getAnalysisVersion());
    }

    private StructureBlock readStructure(JsonNode n) {
        if (n.isMissingNode() || n.isNull()) {
            Source unknown = Source.demoData(null, null);
            return StructureBlock.empty(unknown, unknown);
        }
        List<String> rules = n.path("rulesApplied").isArray()
                ? objectMapper.convertValue(n.path("rulesApplied"),
                        objectMapper.getTypeFactory()
                                .constructCollectionType(List.class, String.class))
                : List.of();
        return new StructureBlock(
                optText(n.path("regime")),
                optText(n.path("regimeLabel")),
                n.path("eyePresent").isBoolean() ? n.path("eyePresent").asBoolean() : null,
                optDouble(n.path("eyeRadiusKm")),
                optDouble(n.path("eyeRingBtContrastK")),
                optDouble(n.path("minBtK")),
                optDouble(n.path("cdoFraction100km")),
                optDouble(n.path("axisymmetry")),
                optDouble(n.path("convectiveRingRadiusKm")),
                optDouble(n.path("coldCloudOffsetKm")),
                rules,
                readSource(n.path("metricsSource"), Provenance.DERIVED_MEASUREMENT),
                readSource(n.path("regimeSource"), Provenance.RULE_ENGINE));
    }

    private VisionBlock readVision(JsonNode n, String gradcamPath) {
        if (n.isMissingNode() || n.isNull()) {
            return VisionBlock.empty(Source.demoData(null, null));
        }
        return new VisionBlock(
                optDouble(n.path("vmaxKt")),
                optText(n.path("category")),
                optDouble(n.path("confidence")),
                gradcamPath != null ? mediaUrl(gradcamPath) : optText(n.path("gradcamUrl")),
                readSource(n.path("source"), Provenance.DEMO_DATA));
    }

    /**
     * Reads a provenance stamp from stored analysis, then re-applies the trained-flag
     * rule. A stale row that claims TRAINED_MODEL without a trained model behind it is
     * downgraded here rather than reaching the browser.
     */
    private Source readSource(JsonNode n, Provenance fallback) {
        if (n.isMissingNode() || n.isNull()) {
            return new Source(fallback, null, null, false, null);
        }
        Source parsed = objectMapper.convertValue(n, Source.class);
        return parsed == null ? new Source(fallback, null, null, false, null)
                : parsed.enforceTrainedFlag();
    }

    private Source sourceFromFrames(List<StormFrame> frames, String block) {
        return frames.stream()
                .map(this::readAnalysis)
                .filter(java.util.Objects::nonNull)
                .findFirst()
                .map(n -> readSource(n.path(block).path("source"), Provenance.DEMO_DATA))
                .orElseGet(() -> Source.demoData(null, null));
    }

    private JsonNode readAnalysis(StormFrame f) {
        if (f.getAnalysisJson() == null || f.getAnalysisJson().isBlank()) {
            return null;
        }
        try {
            return objectMapper.readTree(f.getAnalysisJson());
        } catch (Exception e) {
            return null;
        }
    }

    private static String mediaUrl(String path) {
        return path == null ? null : "/media/" + path;
    }

    private static Double optDouble(JsonNode n) {
        return n.isNumber() ? n.asDouble() : null;
    }

    private static String optText(JsonNode n) {
        return n.isTextual() ? n.asText() : null;
    }
}
