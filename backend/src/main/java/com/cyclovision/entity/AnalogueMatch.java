package com.cyclovision.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;
import java.util.UUID;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

/**
 * One retrieved historical analogue, with what happened to it next.
 *
 * <p>The outcome columns are the point of the feature: the analogue ensemble is a
 * second, independent forecast, not a "similar storms" card. Same-storm and same-season
 * neighbours are excluded upstream so a storm cannot be its own analogue.
 */
@Entity
@Table(name = "analogue_match")
public class AnalogueMatch {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @Column(name = "run_id", nullable = false)
    private UUID runId;

    @Column(name = "rank", nullable = false)
    private int rank;

    @Column(name = "match_sid", nullable = false)
    private String matchSid;

    @Column(name = "match_time", nullable = false)
    private OffsetDateTime matchTime;

    @Column(name = "similarity", nullable = false)
    private double similarity;

    @Column(name = "outcome_delta_vmax_24h_kt")
    private Double outcomeDeltaVmax24hKt;

    @Column(name = "outcome_was_ri")
    private Boolean outcomeWasRi;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "onward_track_json")
    private String onwardTrackJson;

    protected AnalogueMatch() {
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

    public int getRank() {
        return rank;
    }

    public void setRank(int rank) {
        this.rank = rank;
    }

    public String getMatchSid() {
        return matchSid;
    }

    public void setMatchSid(String matchSid) {
        this.matchSid = matchSid;
    }

    public OffsetDateTime getMatchTime() {
        return matchTime;
    }

    public void setMatchTime(OffsetDateTime matchTime) {
        this.matchTime = matchTime;
    }

    public double getSimilarity() {
        return similarity;
    }

    public void setSimilarity(double similarity) {
        this.similarity = similarity;
    }

    public Double getOutcomeDeltaVmax24hKt() {
        return outcomeDeltaVmax24hKt;
    }

    public void setOutcomeDeltaVmax24hKt(Double outcomeDeltaVmax24hKt) {
        this.outcomeDeltaVmax24hKt = outcomeDeltaVmax24hKt;
    }

    public Boolean getOutcomeWasRi() {
        return outcomeWasRi;
    }

    public void setOutcomeWasRi(Boolean outcomeWasRi) {
        this.outcomeWasRi = outcomeWasRi;
    }

    public String getOnwardTrackJson() {
        return onwardTrackJson;
    }

    public void setOnwardTrackJson(String onwardTrackJson) {
        this.onwardTrackJson = onwardTrackJson;
    }
}
