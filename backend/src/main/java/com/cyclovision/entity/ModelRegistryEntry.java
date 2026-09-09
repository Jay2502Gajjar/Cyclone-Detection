package com.cyclovision.entity;

import com.cyclovision.domain.Provenance;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * What produced what. Drives the Model Card and the provenance system.
 *
 * <p>A row may only claim {@link Provenance#TRAINED_MODEL} when {@code trained} is true
 * and {@code metricsJson} carries a held-out metric together with the baseline it is
 * compared against. In Phase 0 every row is {@code DEMO_DATA} with
 * {@code trained = false}.
 */
@Entity
@Table(name = "model_registry")
public class ModelRegistryEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Integer id;

    @Column(name = "model_key", nullable = false)
    private String modelKey;

    @Column(name = "version", nullable = false)
    private String version;

    @Enumerated(EnumType.STRING)
    @Column(name = "provenance", nullable = false)
    private Provenance provenance;

    @Column(name = "is_trained", nullable = false)
    private boolean trained;

    @Column(name = "trained_at")
    private OffsetDateTime trainedAt;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metrics_json")
    private String metricsJson;

    @Column(name = "notes")
    private String notes;

    protected ModelRegistryEntry() {
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public String getModelKey() {
        return modelKey;
    }

    public void setModelKey(String modelKey) {
        this.modelKey = modelKey;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public Provenance getProvenance() {
        return provenance;
    }

    public void setProvenance(Provenance provenance) {
        this.provenance = provenance;
    }

    public boolean isTrained() {
        return trained;
    }

    public void setTrained(boolean trained) {
        this.trained = trained;
    }

    public OffsetDateTime getTrainedAt() {
        return trainedAt;
    }

    public void setTrainedAt(OffsetDateTime trainedAt) {
        this.trainedAt = trainedAt;
    }

    public String getMetricsJson() {
        return metricsJson;
    }

    public void setMetricsJson(String metricsJson) {
        this.metricsJson = metricsJson;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}
