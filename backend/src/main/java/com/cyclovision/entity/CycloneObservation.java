package com.cyclovision.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "cyclone_observations")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CycloneObservation {

    @Id
    private String id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cyclone_id")
    @JsonIgnore
    private Cyclone cyclone;

    private LocalDateTime observedAt;
    private Double lat;
    private Double longCoord; // renamed property to avoid SQL keyword
    private Double windSpeedKmh;
    private Double pressureHpa;
    private Double movementDirectionDeg;
    private Double movementSpeedKmh;
    private String intensityCategory;
}
