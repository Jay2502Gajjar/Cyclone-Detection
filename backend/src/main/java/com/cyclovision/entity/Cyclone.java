package com.cyclovision.entity;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "cyclones")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Cyclone {

    @Id
    private String id;

    private String name;
    private String basin;
    private Integer seasonYear;
    private String status;
    private LocalDateTime createdAt;

    @OneToMany(mappedBy = "cyclone", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @OrderBy("observedAt ASC")
    @Builder.Default
    private List<CycloneObservation> observations = new ArrayList<>();
}
