package com.cyclovision.repository;

import com.cyclovision.entity.ModelRegistryEntry;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ModelRegistryRepository extends JpaRepository<ModelRegistryEntry, Integer> {

    List<ModelRegistryEntry> findAllByOrderByModelKeyAsc();
}
