package com.cyclovision.repository;

import com.cyclovision.entity.ForecastPoint;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ForecastPointRepository extends JpaRepository<ForecastPoint, Long> {

    List<ForecastPoint> findByRunIdOrderByLeadHoursAsc(UUID runId);
}
