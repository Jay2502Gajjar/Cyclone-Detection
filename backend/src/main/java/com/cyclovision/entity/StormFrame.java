package com.cyclovision.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * The central timeline table: one row per (storm, observation time).
 *
 * <p>Everything the scrubber needs lives here, already computed. Invariant I5 says the
 * scrubber never triggers inference — it reads {@code analysisJson}, which
 * {@code ml/precompute/precompute_frames.py} wrote offline.
 *
 * <p>The {@code geom} column in the schema is a PostGIS generated column derived from
 * lat/lon. It is deliberately not mapped here: nothing in the application reads it, and
 * mapping it would drag in hibernate-spatial for no benefit.
 */
@Entity
@Table(name = "storm_frame")
public class StormFrame {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @Column(name = "sid", nullable = false)
    private String sid;

    @Column(name = "obs_time", nullable = false)
    private OffsetDateTime obsTime;

    // --- OBSERVED (IBTrACS best track) ---

    @Column(name = "lat", nullable = false)
    private double lat;

    @Column(name = "lon", nullable = false)
    private double lon;

    @Column(name = "vmax_kt")
    private Double vmaxKt;

    @Column(name = "pressure_hpa")
    private Double pressureHpa;

    @Column(name = "category")
    private String category;

    @Column(name = "translation_speed_kt")
    private Double translationSpeedKt;

    @Column(name = "heading_deg")
    private Double headingDeg;

    @Column(name = "dist_to_coast_km")
    private Double distToCoastKm;

    // --- SATELLITE (nullable: not every track point has a matched frame) ---

    @Column(name = "image_path")
    private String imagePath;

    /** Raw brightness temperature in Kelvin (.npy). Structural metrics need this, not the PNG. */
    @Column(name = "bt_path")
    private String btPath;

    @Column(name = "image_time")
    private OffsetDateTime imageTime;

    @Column(name = "image_source")
    private String imageSource;

    @Column(name = "gradcam_path")
    private String gradcamPath;

    // --- PRECOMPUTED ANALYSIS ---

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "analysis_json")
    private String analysisJson;

    @Column(name = "analysis_version")
    private String analysisVersion;

    public StormFrame() {
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getSid() {
        return sid;
    }

    public void setSid(String sid) {
        this.sid = sid;
    }

    public OffsetDateTime getObsTime() {
        return obsTime;
    }

    public void setObsTime(OffsetDateTime obsTime) {
        this.obsTime = obsTime;
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

    public Double getVmaxKt() {
        return vmaxKt;
    }

    public void setVmaxKt(Double vmaxKt) {
        this.vmaxKt = vmaxKt;
    }

    public Double getPressureHpa() {
        return pressureHpa;
    }

    public void setPressureHpa(Double pressureHpa) {
        this.pressureHpa = pressureHpa;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public Double getTranslationSpeedKt() {
        return translationSpeedKt;
    }

    public void setTranslationSpeedKt(Double translationSpeedKt) {
        this.translationSpeedKt = translationSpeedKt;
    }

    public Double getHeadingDeg() {
        return headingDeg;
    }

    public void setHeadingDeg(Double headingDeg) {
        this.headingDeg = headingDeg;
    }

    public Double getDistToCoastKm() {
        return distToCoastKm;
    }

    public void setDistToCoastKm(Double distToCoastKm) {
        this.distToCoastKm = distToCoastKm;
    }

    public String getImagePath() {
        return imagePath;
    }

    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }

    public String getBtPath() {
        return btPath;
    }

    public void setBtPath(String btPath) {
        this.btPath = btPath;
    }

    public OffsetDateTime getImageTime() {
        return imageTime;
    }

    public void setImageTime(OffsetDateTime imageTime) {
        this.imageTime = imageTime;
    }

    public String getImageSource() {
        return imageSource;
    }

    public void setImageSource(String imageSource) {
        this.imageSource = imageSource;
    }

    public String getGradcamPath() {
        return gradcamPath;
    }

    public void setGradcamPath(String gradcamPath) {
        this.gradcamPath = gradcamPath;
    }

    public String getAnalysisJson() {
        return analysisJson;
    }

    public void setAnalysisJson(String analysisJson) {
        this.analysisJson = analysisJson;
    }

    public String getAnalysisVersion() {
        return analysisVersion;
    }

    public void setAnalysisVersion(String analysisVersion) {
        this.analysisVersion = analysisVersion;
    }
}
