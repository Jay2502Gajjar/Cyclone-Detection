package com.cyclovision.repository;

import com.cyclovision.entity.*;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface PredictionRepository extends JpaRepository<Prediction, String> {
    @EntityGraph(attributePaths = {"trajectory"})
    Optional<Prediction> findFirstByCycloneIdOrderByGeneratedAtDesc(String cycloneId);
}
