package com.cyclovision.repository;

import com.cyclovision.entity.Storm;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StormRepository extends JpaRepository<Storm, String> {

    List<Storm> findAllByOrderBySeasonYearDescNameAsc();

    List<Storm> findByDemoTrueOrderBySeasonYearDescNameAsc();
}
