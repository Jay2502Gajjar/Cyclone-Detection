package com.cyclovision.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.util.UUID;

/**
 * One predicted position for a forecast run.
 *
 * <p>The cone radii are empirical: they are percentiles of the track model's own
 * held-out error at this lead time, not chosen radii. That is why they carry
 * {@code STATISTICAL_BASELINE} provenance rather than {@code TRAINED_MODEL}.
 */
@Entity
@Table(name = "forecast_point")
public class ForecastPoint {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @Column(name = "run_id", nullable = false)
    private UUID runId;

    @Column(name = "lead_hours", nullable = false)
    private int leadHours;

    @Column(name = "lat", nullable = false)
    private double lat;

    @Column(name = "lon", nullable = false)
    private double lon;

    @Column(name = "cone_radius_p67_km")
    private Double coneRadiusP67Km;

    @Column(name = "cone_radius_p90_km")
    private Double coneRadiusP90Km;

    @Column(name = "predicted_vmax_kt")
    private Double predictedVmaxKt;

    protected ForecastPoint() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public UUID getRunId() {
        return runId;
    }

    public void setRunId(UUID runId) {
        this.runId = runId;
    }

    public int getLeadHours() {
        return leadHours;
    }

    public void setLeadHours(int leadHours) {
        this.leadHours = leadHours;
    }

    public double getLat() {
        return lat;
    }

    public void setLat(double lat) {
        this.lat = lat;
    }

    public double getLon() {
        return lon;
    }

    public void setLon(double lon) {
        this.lon = lon;
    }

    public Double getConeRadiusP67Km() {
        return coneRadiusP67Km;
    }

    public void setConeRadiusP67Km(Double coneRadiusP67Km) {
        this.coneRadiusP67Km = coneRadiusP67Km;
    }

    public Double getConeRadiusP90Km() {
        return coneRadiusP90Km;
    }

    public void setConeRadiusP90Km(Double coneRadiusP90Km) {
        this.coneRadiusP90Km = coneRadiusP90Km;
    }

    public Double getPredictedVmaxKt() {
        return predictedVmaxKt;
    }

    public void setPredictedVmaxKt(Double predictedVmaxKt) {
        this.predictedVmaxKt = predictedVmaxKt;
    }
}
