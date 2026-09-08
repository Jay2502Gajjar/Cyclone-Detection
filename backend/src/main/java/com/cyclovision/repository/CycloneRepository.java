package com.cyclovision.repository;

import com.cyclovision.entity.Cyclone;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CycloneRepository extends JpaRepository<Cyclone, String> {
    List<Cyclone> findByStatus(String status);
}
