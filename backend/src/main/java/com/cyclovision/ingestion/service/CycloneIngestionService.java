package com.cyclovision.ingestion.service;

import com.cyclovision.entity.Cyclone;
import com.cyclovision.entity.CycloneObservation;
import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import com.cyclovision.ingestion.provider.CycloneDataProvider;
import com.cyclovision.repository.CycloneObservationRepository;
import com.cyclovision.repository.CycloneRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class CycloneIngestionService {

    private static final Logger logger = LoggerFactory.getLogger(CycloneIngestionService.class);

    private final List<CycloneDataProvider> dataProviders;
    private final CycloneRepository cycloneRepository;
    private final CycloneObservationRepository observationRepository;

    public CycloneIngestionService(List<CycloneDataProvider> dataProviders,
                                   CycloneRepository cycloneRepository,
                                   CycloneObservationRepository observationRepository) {
        this.dataProviders = dataProviders;
        this.cycloneRepository = cycloneRepository;
        this.observationRepository = observationRepository;
    }

    public void runIngestion() {
        for (CycloneDataProvider provider : dataProviders) {
            String providerName = provider.getProviderName();
            logger.info("Starting ingestion from provider: {}", providerName);

            try {
                List<ExternalCycloneDto> activeCyclones = provider.fetchActiveCyclones();
                for (ExternalCycloneDto extCyclone : activeCyclones) {
                    processCyclone(providerName, extCyclone, provider);
                }
            } catch (Exception e) {
                logger.error("Error during ingestion for provider: " + providerName, e);
            }
        }
    }

    @Transactional
    public void processCyclone(String providerName, ExternalCycloneDto extCyclone, CycloneDataProvider provider) {
        String externalId = extCyclone.getExternalId();

        Optional<Cyclone> existingCyclone = cycloneRepository.findByExternalSourceAndExternalId(providerName, externalId);
        Cyclone cyclone;

        if (existingCyclone.isPresent()) {
            cyclone = existingCyclone.get();
            cyclone.setName(extCyclone.getName());
            cyclone.setBasin(extCyclone.getBasin());
            cyclone.setStatus(extCyclone.getStatus());
            cyclone.setCurrentCategory(extCyclone.getCurrentCategory());
        } else {
            cyclone = new Cyclone();
            cyclone.setExternalSource(providerName);
            cyclone.setExternalId(externalId);
            cyclone.setName(extCyclone.getName());
            cyclone.setBasin(extCyclone.getBasin());
            cyclone.setStatus(extCyclone.getStatus());
            cyclone.setCurrentCategory(extCyclone.getCurrentCategory());
        }

        cyclone = cycloneRepository.save(cyclone);

        List<ExternalObservationDto> observations = provider.fetchObservations(externalId);
        if (observations == null || observations.isEmpty()) {
            return;
        }

        Map<String, CycloneObservation> existingMap = new HashMap<>();
        if (cyclone.getId() != null) {
            List<CycloneObservation> existingList = observationRepository.findByCycloneIdOrderByObservedAtAsc(cyclone.getId());
            for (CycloneObservation obs : existingList) {
                if (obs.getSourceRecordId() != null) {
                    existingMap.put(obs.getSourceRecordId(), obs);
                }
            }
        }

        List<CycloneObservation> toSave = new ArrayList<>(observations.size());
        for (ExternalObservationDto extObs : observations) {
            String recordId = extObs.getSourceRecordId();
            CycloneObservation observation = recordId != null ? existingMap.get(recordId) : null;
            if (observation == null) {
                observation = new CycloneObservation();
                observation.setCyclone(cyclone);
                observation.setSourceRecordId(recordId);
            }

            observation.setObservedAt(extObs.getObservedAt());
            observation.setLatitude(extObs.getLatitude());
            observation.setLongitude(extObs.getLongitude());
            observation.setWindSpeedKph(extObs.getWindSpeedKph());
            observation.setPressureHpa(extObs.getPressureHpa());
            observation.setMovementSpeedKph(extObs.getMovementSpeedKph());
            observation.setMovementDirectionDegrees(extObs.getMovementDirectionDegrees());
            
            String source = extObs.getSource() != null ? extObs.getSource() : cyclone.getExternalSource();
            observation.setSource(source);

            toSave.add(observation);
        }

        observationRepository.saveAll(toSave);
    }
}
