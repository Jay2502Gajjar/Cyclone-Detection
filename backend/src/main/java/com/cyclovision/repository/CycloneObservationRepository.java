package com.cyclovision.repository;

import com.cyclovision.entity.CycloneObservation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CycloneObservationRepository extends JpaRepository<CycloneObservation, String> {
    List<CycloneObservation> findByCycloneIdOrderByObservedAtAsc(String cycloneId);
}
