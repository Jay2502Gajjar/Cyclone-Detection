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
 * The offline safety net: a fully-formed forecast response, stored verbatim.
 *
 * <p>Used only when the AI service is unreachable and no cached run exists. Anything
 * served from here comes back with {@code servedFrom = "demo"} and
 * {@code DEMO_DATA} provenance, so it can never be mistaken for a live prediction.
 */
@Entity
@Table(name = "demo_scenario")
public class DemoScenario {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Integer id;

    @Column(name = "sid", nullable = false)
    private String sid;

    @Column(name = "issued_for", nullable = false)
    private OffsetDateTime issuedFor;

    @Column(name = "label", nullable = false)
    private String label;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "payload_json", nullable = false)
    private String payloadJson;

    protected DemoScenario() {
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
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

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label;
    }

    public String getPayloadJson() {
        return payloadJson;
    }

    public void setPayloadJson(String payloadJson) {
        this.payloadJson = payloadJson;
    }
}
