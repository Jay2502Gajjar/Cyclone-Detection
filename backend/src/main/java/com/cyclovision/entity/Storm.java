package com.cyclovision.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;

/**
 * One tropical cyclone, keyed by its IBTrACS SID (e.g. {@code 2019114N06084}).
 *
 * <p>{@code split} and {@code isDemo} carry the leakage guard: the database itself
 * enforces {@code CHECK (NOT is_demo OR split = 'test')}, so a storm we demonstrate on
 * cannot silently end up in the training set.
 */
@Entity
@Table(name = "storm")
public class Storm {

    @Id
    @Column(name = "sid", nullable = false)
    private String sid;

    @Column(name = "name", nullable = false)
    private String name;

    @Column(name = "basin", nullable = false)
    private String basin;

    @Column(name = "season_year", nullable = false)
    private int seasonYear;

    @Column(name = "start_time", nullable = false)
    private OffsetDateTime startTime;

    @Column(name = "end_time", nullable = false)
    private OffsetDateTime endTime;

    @Column(name = "peak_vmax_kt")
    private Double peakVmaxKt;

    @Column(name = "peak_category")
    private String peakCategory;

    @Column(name = "landfall_time")
    private OffsetDateTime landfallTime;

    @Column(name = "landfall_lat")
    private Double landfallLat;

    @Column(name = "landfall_lon")
    private Double landfallLon;

    @Column(name = "landfall_place")
    private String landfallPlace;

    @Column(name = "is_demo", nullable = false)
    private boolean demo;

    @Column(name = "split", nullable = false)
    private String split;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    public Storm() {
    }

    public String getSid() {
        return sid;
    }

    public void setSid(String sid) {
        this.sid = sid;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getBasin() {
        return basin;
    }

    public void setBasin(String basin) {
        this.basin = basin;
    }

    public int getSeasonYear() {
        return seasonYear;
    }

    public void setSeasonYear(int seasonYear) {
        this.seasonYear = seasonYear;
    }

    public OffsetDateTime getStartTime() {
        return startTime;
    }

    public void setStartTime(OffsetDateTime startTime) {
        this.startTime = startTime;
    }

    public OffsetDateTime getEndTime() {
        return endTime;
    }

    public void setEndTime(OffsetDateTime endTime) {
        this.endTime = endTime;
    }

    public Double getPeakVmaxKt() {
        return peakVmaxKt;
    }

    public void setPeakVmaxKt(Double peakVmaxKt) {
        this.peakVmaxKt = peakVmaxKt;
    }

    public String getPeakCategory() {
        return peakCategory;
    }

    public void setPeakCategory(String peakCategory) {
        this.peakCategory = peakCategory;
    }

    public OffsetDateTime getLandfallTime() {
        return landfallTime;
    }

    public void setLandfallTime(OffsetDateTime landfallTime) {
        this.landfallTime = landfallTime;
    }

    public Double getLandfallLat() {
        return landfallLat;
    }

    public void setLandfallLat(Double landfallLat) {
        this.landfallLat = landfallLat;
    }

    public Double getLandfallLon() {
        return landfallLon;
    }

    public void setLandfallLon(Double landfallLon) {
        this.landfallLon = landfallLon;
    }

    public String getLandfallPlace() {
        return landfallPlace;
    }

    public void setLandfallPlace(String landfallPlace) {
        this.landfallPlace = landfallPlace;
    }

    public boolean isDemo() {
        return demo;
    }

    public void setDemo(boolean demo) {
        this.demo = demo;
    }

    public String getSplit() {
        return split;
    }

    public void setSplit(String split) {
        this.split = split;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
