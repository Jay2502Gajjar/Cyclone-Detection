package com.cyclovision.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import java.util.UUID;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * One live forecast invocation.
 *
 * <p>{@code issuedFor} is the temporal-mask boundary T: the forecast was produced using
 * only observations at or before this instant. The unique key
 * {@code (sid, issued_for, model_bundle_version)} makes runs idempotent and cacheable,
 * which is what lets the service degrade gracefully when the AI service is unreachable.
 */
@Entity
@Table(name = "forecast_run")
public class ForecastRun {

    @Id
    @Column(name = "id")
    private UUID id;

    @Column(name = "sid", nullable = false)
    private String sid;

    @Column(name = "issued_for", nullable = false)
    private OffsetDateTime issuedFor;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "model_bundle_version", nullable = false)
    private String modelBundleVersion;

    @Column(name = "delta_vmax_24h_kt")
    private Double deltaVmax24hKt;

    @Column(name = "predicted_vmax_24h_kt")
    private Double predictedVmax24hKt;

    @Column(name = "intensity_trend")
    private String intensityTrend;

    @Column(name = "intensity_confidence")
    private Double intensityConfidence;

    @Column(name = "ri_probability")
    private Double riProbability;

    @Column(name = "ri_base_rate")
    private Double riBaseRate;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "structure_json")
    private String structureJson;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "vision_json")
    private String visionJson;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "shap_json")
    private String shapJson;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "analogue_summary_json")
    private String analogueSummaryJson;

    @Column(name = "risk_score")
    private Double riskScore;

    @Column(name = "risk_level")
    private String riskLevel;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "risk_terms_json")
    private String riskTermsJson;

    @Column(name = "report_text")
    private String reportText;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "provenance_json", nullable = false)
    private String provenanceJson;

    @Column(name = "degraded", nullable = false)
    private boolean degraded;

    protected ForecastRun() {
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getSid() {
        return sid;
    }

    public void setSid(String sid) {
        this.sid = sid;
    }

    public OffsetDateTime getIssuedFor() {
        return issuedFor;
    }

    public void setIssuedFor(OffsetDateTime issuedFor) {
        this.issuedFor = issuedFor;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public String getModelBundleVersion() {
        return modelBundleVersion;
    }

    public void setModelBundleVersion(String modelBundleVersion) {
        this.modelBundleVersion = modelBundleVersion;
    }

    public Double getDeltaVmax24hKt() {
        return deltaVmax24hKt;
    }

    public void setDeltaVmax24hKt(Double deltaVmax24hKt) {
        this.deltaVmax24hKt = deltaVmax24hKt;
    }

    public Double getPredictedVmax24hKt() {
        return predictedVmax24hKt;
    }

    public void setPredictedVmax24hKt(Double predictedVmax24hKt) {
        this.predictedVmax24hKt = predictedVmax24hKt;
    }

    public String getIntensityTrend() {
        return intensityTrend;
    }

    public void setIntensityTrend(String intensityTrend) {
        this.intensityTrend = intensityTrend;
    }

    public Double getIntensityConfidence() {
        return intensityConfidence;
    }

    public void setIntensityConfidence(Double intensityConfidence) {
        this.intensityConfidence = intensityConfidence;
    }

    public Double getRiProbability() {
        return riProbability;
    }

    public void setRiProbability(Double riProbability) {
        this.riProbability = riProbability;
    }

    public Double getRiBaseRate() {
        return riBaseRate;
    }

    public void setRiBaseRate(Double riBaseRate) {
        this.riBaseRate = riBaseRate;
    }

    public String getStructureJson() {
        return structureJson;
    }

    public void setStructureJson(String structureJson) {
        this.structureJson = structureJson;
    }

    public String getVisionJson() {
        return visionJson;
    }

    public void setVisionJson(String visionJson) {
        this.visionJson = visionJson;
    }

    public String getShapJson() {
        return shapJson;
    }

    public void setShapJson(String shapJson) {
        this.shapJson = shapJson;
    }

    public String getAnalogueSummaryJson() {
        return analogueSummaryJson;
    }

    public void setAnalogueSummaryJson(String analogueSummaryJson) {
        this.analogueSummaryJson = analogueSummaryJson;
    }

    public Double getRiskScore() {
        return riskScore;
    }

    public void setRiskScore(Double riskScore) {
        this.riskScore = riskScore;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
    }

    public String getRiskTermsJson() {
        return riskTermsJson;
    }

    public void setRiskTermsJson(String riskTermsJson) {
        this.riskTermsJson = riskTermsJson;
    }

    public String getReportText() {
        return reportText;
    }

    public void setReportText(String reportText) {
        this.reportText = reportText;
    }

    public String getProvenanceJson() {
        return provenanceJson;
    }

    public void setProvenanceJson(String provenanceJson) {
        this.provenanceJson = provenanceJson;
    }

    public boolean isDegraded() {
        return degraded;
    }

    public void setDegraded(boolean degraded) {
        this.degraded = degraded;
    }
}
