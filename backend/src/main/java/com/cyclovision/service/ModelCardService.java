package com.cyclovision.service;

import com.cyclovision.domain.Provenance;
import com.cyclovision.dto.ModelCardDto.AblationRow;
import com.cyclovision.dto.ModelCardDto.ConeCalibrationRow;
import com.cyclovision.dto.ModelCardDto.DatasetInfo;
import com.cyclovision.dto.ModelCardDto.ModelCard;
import com.cyclovision.dto.ModelCardDto.ModelRow;
import com.cyclovision.dto.ModelCardDto.NotBuiltRow;
import com.cyclovision.dto.ModelCardDto.SplitInfo;
import com.cyclovision.entity.ModelRegistryEntry;
import com.cyclovision.repository.ModelRegistryRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Assembles the credibility screen from two sources of truth: the {@code model_registry}
 * table (what is loaded and whether it is trained) and {@code models/metrics.json}
 * (held-out numbers written by {@code ml/eval/evaluate_all.py}).
 *
 * <p>If metrics.json is absent — which is exactly the Phase 0 state — the card still
 * renders, showing every model as untrained with no metrics. That is the honest report,
 * and it is why the page is built before there is anything flattering to put on it.
 */
@Service
public class ModelCardService {

    private static final Logger log = LoggerFactory.getLogger(ModelCardService.class);

    private final ModelRegistryRepository registryRepository;
    private final ObjectMapper objectMapper;
    private final Path metricsPath;
    private final String bundleVersion;

    public ModelCardService(ModelRegistryRepository registryRepository,
            ObjectMapper objectMapper,
            @Value("${cyclovision.models-dir:../models}") String modelsDir,
            @Value("${cyclovision.bundle-version:phase0}") String bundleVersion) {
        this.registryRepository = registryRepository;
        this.objectMapper = objectMapper;
        this.metricsPath = Path.of(modelsDir).resolve("metrics.json");
        this.bundleVersion = bundleVersion;
    }

    @Transactional(readOnly = true)
    public ModelCard get() {
        JsonNode metrics = readMetrics();

        List<ModelRow> models = new ArrayList<>();
        for (ModelRegistryEntry e : registryRepository.findAllByOrderByModelKeyAsc()) {
            JsonNode m = metrics == null ? null : metrics.path("models").path(e.getModelKey());
            models.add(new ModelRow(
                    e.getModelKey(),
                    e.getVersion(),
                    // A registry row can never advertise a trained model that is not trained.
                    e.isTrained() ? e.getProvenance() : Provenance.DEMO_DATA,
                    e.isTrained(),
                    text(m, "metric"),
                    number(m, "value"),
                    text(m, "baseline"),
                    number(m, "baselineValue"),
                    integer(m, "n"),
                    e.getNotes()));
        }

        return new ModelCard(
                bundleVersion,
                OffsetDateTime.now(),
                datasets(metrics),
                split(metrics),
                models,
                ablation(metrics),
                coneCalibration(metrics),
                notBuilt());
    }

    private JsonNode readMetrics() {
        try {
            if (!Files.exists(metricsPath)) {
                log.info("No metrics.json at {} — reporting an untrained bundle", metricsPath);
                return null;
            }
            return objectMapper.readTree(Files.readString(metricsPath));
        } catch (Exception e) {
            log.warn("Could not read {}: {}", metricsPath, e.toString());
            return null;
        }
    }

    private List<DatasetInfo> datasets(JsonNode metrics) {
        if (metrics == null || !metrics.path("datasets").isArray()) {
            return List.of();
        }
        List<DatasetInfo> out = new ArrayList<>();
        for (JsonNode d : metrics.path("datasets")) {
            out.add(new DatasetInfo(
                    d.path("name").asText(null),
                    d.path("source").asText(null),
                    d.path("licence").asText(null),
                    d.path("stormCount").asInt(0),
                    d.path("frameCount").asInt(0),
                    number(d, "matchRatePct"),
                    d.path("note").asText(null)));
        }
        return out;
    }

    private SplitInfo split(JsonNode metrics) {
        JsonNode s = metrics == null ? null : metrics.path("split");
        if (s == null || s.isMissingNode()) {
            return new SplitInfo("storm-wise", 0, 0, 0, true);
        }
        return new SplitInfo("storm-wise", s.path("train").asInt(0), s.path("val").asInt(0),
                s.path("test").asInt(0), s.path("demoStormsInTest").asBoolean(true));
    }

    private List<AblationRow> ablation(JsonNode metrics) {
        List<AblationRow> out = new ArrayList<>();
        List<String> settings = List.of("track-only", "image-only", "fused");
        for (String setting : settings) {
            JsonNode a = metrics == null ? null : metrics.path("ablation").path(setting);
            out.add(new AblationRow(setting, number(a, "maeKt"), integer(a, "n")));
        }
        return out;
    }

    private List<ConeCalibrationRow> coneCalibration(JsonNode metrics) {
        List<ConeCalibrationRow> out = new ArrayList<>();
        for (int lead : new int[] {12, 24, 48}) {
            JsonNode c = metrics == null ? null
                    : metrics.path("coneCalibration").path(String.valueOf(lead));
            out.add(new ConeCalibrationRow(lead, number(c, "p67Km"), number(c, "p90Km"),
                    number(c, "observedContainmentP67"), integer(c, "n")));
        }
        return out;
    }

    /** Stated plainly, on the page. It pre-answers the hardest questions a judge asks. */
    private List<NotBuiltRow> notBuilt() {
        return List.of(
                new NotBuiltRow("Trained Dvorak pattern classifier",
                        "No free labelled Dvorak pattern dataset exists at scale. We report "
                                + "deterministic structural measurements and a transparent "
                                + "rule engine instead, and label them as such."),
                new NotBuiltRow("Wide-field cyclone detection (bounding boxes)",
                        "No labelled detection data available in the time budget. Our "
                                + "imagery is storm-centred, so detection is not required."),
                new NotBuiltRow("Deep sequence trajectory model (GRU/LSTM/Transformer)",
                        "Cannot be trained and validated reliably in the time budget. We use "
                                + "a CLIPER-style model, the operational benchmark, instead."),
                new NotBuiltRow("Live satellite ingestion",
                        "The product is historical replay and hindcast verification; a live "
                                + "feed would add a demo-time network dependency for no "
                                + "scientific gain."),
                new NotBuiltRow("Observed sea-surface temperature / shear fields",
                        "Reanalysis downloads are too heavy for the window. A feature-vector "
                                + "slot is reserved for them."));
    }

    private static String text(JsonNode n, String field) {
        return n == null || !n.path(field).isTextual() ? null : n.path(field).asText();
    }

    private static Double number(JsonNode n, String field) {
        return n == null || !n.path(field).isNumber() ? null : n.path(field).asDouble();
    }

    private static Integer integer(JsonNode n, String field) {
        return n == null || !n.path(field).isNumber() ? null : n.path(field).asInt();
    }
}
