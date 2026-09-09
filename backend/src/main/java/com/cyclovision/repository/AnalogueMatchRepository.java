package com.cyclovision.repository;

import com.cyclovision.entity.AnalogueMatch;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AnalogueMatchRepository extends JpaRepository<AnalogueMatch, Long> {

    List<AnalogueMatch> findByRunIdOrderByRankAsc(UUID runId);
}
