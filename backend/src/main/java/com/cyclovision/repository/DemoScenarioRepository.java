package com.cyclovision.repository;

import com.cyclovision.entity.DemoScenario;
import java.time.OffsetDateTime;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DemoScenarioRepository extends JpaRepository<DemoScenario, Integer> {

    Optional<DemoScenario> findBySidAndIssuedFor(String sid, OffsetDateTime issuedFor);

    Optional<DemoScenario> findFirstBySidOrderByIssuedForAsc(String sid);
}
