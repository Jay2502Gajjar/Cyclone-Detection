package com.cyclovision.ingestion.service;

import com.cyclovision.entity.Cyclone;
import com.cyclovision.entity.CycloneObservation;
import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import com.cyclovision.ingestion.provider.CycloneDataProvider;
import com.cyclovision.repository.CycloneObservationRepository;
import com.cyclovision.repository.CycloneRepository;
import com.cyclovision.ingestion.validation.CycloneDataValidator;
import com.cyclovision.ingestion.validation.ValidationResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class CycloneIngestionService {

    private static final Logger logger = LoggerFactory.getLogger(CycloneIngestionService.class);

    private final List<CycloneDataProvider> dataProviders;
    private final CycloneRepository cycloneRepository;
    private final CycloneObservationRepository observationRepository;
    private final TransactionTemplate transactionTemplate;
    private final CycloneDataValidator cycloneDataValidator;
    private final ReentrantLock ingestionLock = new ReentrantLock();

    // In-memory status tracking
    private volatile String currentProvider = null;
    private volatile Instant currentRunStartTime = null;

    private volatile String lastRunProvider = null;
    private volatile Instant lastRunStartTime = null;
    private volatile Instant lastRunEndTime = null;
    private volatile Long lastRunDurationMs = null;
    private volatile Boolean lastRunSuccess = null;
    private volatile Integer lastRunFailures = null;
    private volatile Integer lastRunSkippedRecords = null;
    private volatile String lastRunMessage = null;

    public CycloneIngestionService(List<CycloneDataProvider> dataProviders,
                                   CycloneRepository cycloneRepository,
                                   CycloneObservationRepository observationRepository,
                                   PlatformTransactionManager transactionManager) {
        this(dataProviders, cycloneRepository, observationRepository, transactionManager, new CycloneDataValidator());
    }

    @Autowired
    public CycloneIngestionService(List<CycloneDataProvider> dataProviders,
                                   CycloneRepository cycloneRepository,
                                   CycloneObservationRepository observationRepository,
                                   PlatformTransactionManager transactionManager,
                                   CycloneDataValidator cycloneDataValidator) {
        this.dataProviders = dataProviders;
        this.cycloneRepository = cycloneRepository;
        this.observationRepository = observationRepository;
        this.transactionTemplate = new TransactionTemplate(transactionManager);
        this.cycloneDataValidator = cycloneDataValidator != null ? cycloneDataValidator : new CycloneDataValidator();
    }

    public boolean isIngestionRunning() {
        return ingestionLock.isLocked();
    }

    public Map<String, Object> getIngestionStatus() {
        Map<String, Object> status = new LinkedHashMap<>();
        boolean isRunning = ingestionLock.isLocked();
        status.put("running", isRunning);
        status.put("provider", isRunning ? currentProvider : lastRunProvider);
        status.put("currentRunStartTime", currentRunStartTime != null ? currentRunStartTime.toString() : null);
        status.put("lastRunStartTime", lastRunStartTime != null ? lastRunStartTime.toString() : null);
        status.put("lastRunEndTime", lastRunEndTime != null ? lastRunEndTime.toString() : null);
        status.put("lastRunDurationMs", lastRunDurationMs);
        status.put("lastRunSuccess", lastRunSuccess);
        status.put("lastRunFailures", lastRunFailures);
        status.put("lastRunSkippedRecords", lastRunSkippedRecords);
        status.put("lastRunMessage", lastRunMessage);
        return status;
    }

    public Map<String, Object> runIngestion() {
        return runIngestion(null);
    }

    public Map<String, Object> runIngestion(String providerFilter) {
        Instant startTime = Instant.now();
        String effectiveProvider = (providerFilter != null && !providerFilter.isBlank()) ? providerFilter : "ALL";

        if (!ingestionLock.tryLock()) {
            logger.warn("Ingestion is already in progress. Skipping concurrent execution request (filter: {})", providerFilter);
            Map<String, Object> busyResult = new LinkedHashMap<>();
            busyResult.put("provider", effectiveProvider);
            busyResult.put("startTime", startTime.toString());
            busyResult.put("endTime", Instant.now().toString());
            busyResult.put("durationMs", 0L);
            busyResult.put("success", false);
            busyResult.put("skipped", true);
            busyResult.put("message", "Ingestion is already in progress");
            return busyResult;
        }

        currentProvider = effectiveProvider;
        currentRunStartTime = startTime;

        try {
            AtomicInteger totalCyclonesImported = new AtomicInteger(0);
            AtomicInteger totalCyclonesUpdated = new AtomicInteger(0);
            AtomicInteger totalObsImported = new AtomicInteger(0);
            AtomicInteger totalObsUpdated = new AtomicInteger(0);
            AtomicInteger totalFailures = new AtomicInteger(0);
            AtomicInteger totalSkipped = new AtomicInteger(0);
            ConcurrentLinkedQueue<String> failedCycloneIds = new ConcurrentLinkedQueue<>();

        for (CycloneDataProvider provider : dataProviders) {
            String providerName = provider.getProviderName();
            if (providerFilter != null && !providerFilter.isBlank() && !providerName.equalsIgnoreCase(providerFilter)) {
                logger.info("Skipping provider: {} (filter: {})", providerName, providerFilter);
                continue;
            }

            logger.info("Starting ingestion from provider: {}", providerName);

            try {
                List<ExternalCycloneDto> activeCyclones = provider.fetchActiveCyclones();
                int totalToProcess = activeCyclones.size();
                logger.info("Provider {} supplied {} cyclones to process", providerName, totalToProcess);

                // Preload existing cyclones for this provider in one query
                Map<String, Cyclone> existingCycloneMap = new ConcurrentHashMap<>();
                for (Cyclone c : cycloneRepository.findByExternalSource(providerName)) {
                    if (c.getExternalId() != null) {
                        existingCycloneMap.put(c.getExternalId(), c);
                    }
                }
                logger.info("Found {} already existing cyclones for provider {} in database", existingCycloneMap.size(), providerName);

                // Process in parallel using 4 worker threads to match Hikari pool sizing comfortably
                ExecutorService executor = Executors.newFixedThreadPool(4);
                AtomicInteger count = new AtomicInteger(0);

                for (ExternalCycloneDto extCyclone : activeCyclones) {
                    executor.submit(() -> {
                        int currentIdx = count.incrementAndGet();
                        try {
                            transactionTemplate.executeWithoutResult(status -> {
                                processCyclone(providerName, extCyclone, provider, 
                                    existingCycloneMap,
                                    totalCyclonesImported, totalCyclonesUpdated, 
                                    totalObsImported, totalObsUpdated,
                                    totalSkipped);
                            });

                            if (currentIdx % 100 == 0 || currentIdx == totalToProcess) {
                                logger.info("Ingestion progress [{}]: {}/{} cyclones processed (new: {}, updated: {}, new obs: {})",
                                    providerName, currentIdx, totalToProcess, totalCyclonesImported.get(), totalCyclonesUpdated.get(), totalObsImported.get());
                            }
                        } catch (Exception e) {
                            String failedId = (extCyclone != null && extCyclone.getExternalId() != null)
                                    ? extCyclone.getExternalId() : "UNKNOWN";
                            String cycloneName = (extCyclone != null && extCyclone.getName() != null)
                                    ? extCyclone.getName() : "UNKNOWN";
                            logger.warn("Non-fatal failure processing cyclone [id={}, name={}, provider={}]: {}", 
                                failedId, cycloneName, providerName, e.getMessage());
                            failedCycloneIds.add(failedId);
                            totalFailures.incrementAndGet();
                        }
                    });
                }

                executor.shutdown();
                executor.awaitTermination(30, TimeUnit.MINUTES);

            } catch (Exception e) {
                logger.error("Error during ingestion for provider: " + providerName, e);
                failedCycloneIds.add("PROVIDER_" + providerName);
                totalFailures.incrementAndGet();
            }
        }

        long mockCyclonesRemaining = cycloneRepository.countByExternalSource("MOCK");
        long ibtracsCyclones = cycloneRepository.countByExternalSource("IBTrACS");
        long totalCyclonesInDb = cycloneRepository.count();
        long ibtracsObs = observationRepository.countBySource("IBTrACS");
        long mockObs = observationRepository.countBySource("MOCK");
        long totalObsInDb = observationRepository.count();

        Instant endTime = Instant.now();
        long durationMs = Duration.between(startTime, endTime).toMillis();

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("provider", effectiveProvider);
        result.put("startTime", startTime.toString());
        result.put("endTime", endTime.toString());
        result.put("durationMs", durationMs);
        result.put("success", totalFailures.get() == 0);
        result.put("message", totalFailures.get() == 0
                ? "Cyclone ingestion completed successfully"
                : "Cyclone ingestion completed with " + totalFailures.get() + " failure(s)");
        result.put("cyclonesImported", totalCyclonesImported.get());
        result.put("cyclonesUpdated", totalCyclonesUpdated.get());
        result.put("observationsImported", totalObsImported.get());
        result.put("observationsUpdated", totalObsUpdated.get());
        result.put("skippedRecords", totalSkipped.get());
        result.put("failures", totalFailures.get());
        result.put("failedCycloneIds", new ArrayList<>(failedCycloneIds));
        result.put("ibtracsCyclonesInDb", ibtracsCyclones);
        result.put("ibtracsObservationsInDb", ibtracsObs);
        result.put("mockCyclonesRemaining", mockCyclonesRemaining);
        result.put("mockObservationsRemaining", mockObs);
        result.put("totalCyclonesInDb", totalCyclonesInDb);
        result.put("totalObservationsInDb", totalObsInDb);

        lastRunProvider = effectiveProvider;
        lastRunStartTime = startTime;
        lastRunEndTime = endTime;
        lastRunDurationMs = durationMs;
        lastRunSuccess = (totalFailures.get() == 0);
        lastRunFailures = totalFailures.get();
        lastRunSkippedRecords = totalSkipped.get();
        lastRunMessage = (String) result.get("message");

        if (totalFailures.get() == 0) {
            logger.info("Ingestion completed successfully in {} ms for provider {}: {}", durationMs, effectiveProvider, result);
        } else {
            logger.warn("Ingestion completed with {} failure(s) in {} ms for provider {}: {}", totalFailures.get(), durationMs, effectiveProvider, result);
        }
        return result;
        } catch (Throwable t) {
            Instant errorEndTime = Instant.now();
            lastRunProvider = effectiveProvider;
            lastRunStartTime = startTime;
            lastRunEndTime = errorEndTime;
            lastRunDurationMs = Duration.between(startTime, errorEndTime).toMillis();
            lastRunSuccess = false;
            lastRunFailures = (lastRunFailures != null ? lastRunFailures + 1 : 1);
            lastRunMessage = "Ingestion failed unexpectedly: " + t.getMessage();
            throw t;
        } finally {
            currentProvider = null;
            currentRunStartTime = null;
            ingestionLock.unlock();
        }
    }

    private void processCyclone(String providerName,
                                ExternalCycloneDto extCyclone,
                                CycloneDataProvider provider,
                                Map<String, Cyclone> existingCycloneMap,
                                AtomicInteger cyclonesImported,
                                AtomicInteger cyclonesUpdated,
                                AtomicInteger obsImported,
                                AtomicInteger obsUpdated,
                                AtomicInteger totalSkipped) {

        ValidationResult cycloneVal = cycloneDataValidator.validateCyclone(extCyclone);
        if (!cycloneVal.isValid()) {
            logger.warn("Skipping invalid cyclone [provider={}, id={}, name={}]: {}",
                    providerName,
                    extCyclone != null ? extCyclone.getExternalId() : "null",
                    extCyclone != null ? extCyclone.getName() : "null",
                    cycloneVal.getReason());
            totalSkipped.incrementAndGet();
            return;
        }

        String externalId = extCyclone.getExternalId();
        Cyclone existing = existingCycloneMap.get(externalId);
        Cyclone cyclone;
        boolean isNew = (existing == null);

        String basin = extCyclone.getBasin() != null && !extCyclone.getBasin().isBlank()
                ? extCyclone.getBasin() : "Unknown";
        String status = extCyclone.getStatus() != null && !extCyclone.getStatus().isBlank()
                ? extCyclone.getStatus() : "HISTORICAL";

        if (!isNew) {
            cyclone = existing;
            cyclone.setName(extCyclone.getName());
            cyclone.setBasin(basin);
            cyclone.setStatus(status);
            if (extCyclone.getCurrentCategory() != null) {
                cyclone.setCurrentCategory(extCyclone.getCurrentCategory());
            }
        } else {
            cyclone = new Cyclone();
            cyclone.setExternalSource(providerName);
            cyclone.setExternalId(externalId);
            cyclone.setName(extCyclone.getName());
            cyclone.setBasin(basin);
            cyclone.setStatus(status);
            cyclone.setCurrentCategory(extCyclone.getCurrentCategory());
        }

        cyclone = cycloneRepository.save(cyclone);
        if (isNew) {
            cyclonesImported.incrementAndGet();
        } else {
            cyclonesUpdated.incrementAndGet();
        }

        List<ExternalObservationDto> observations = provider.fetchObservations(externalId);
        if (observations != null && !observations.isEmpty()) {
            Map<String, CycloneObservation> existingMap = new HashMap<>();
            if (!isNew && cyclone.getId() != null) {
                List<CycloneObservation> existingObsList = observationRepository.findByCycloneIdOrderByObservedAtAsc(cyclone.getId());
                for (CycloneObservation obs : existingObsList) {
                    if (obs.getSourceRecordId() != null) {
                        existingMap.put(obs.getSourceRecordId(), obs);
                    }
                }
            }

            List<CycloneObservation> toSave = new ArrayList<>(observations.size());
            int newObsCount = 0;
            int updatedObsCount = 0;

            for (ExternalObservationDto extObs : observations) {
                ValidationResult obsVal = cycloneDataValidator.validateObservation(extObs);
                if (!obsVal.isValid()) {
                    logger.warn("Skipping invalid observation [cycloneId={}, recordId={}, observedAt={}]: {}",
                            externalId,
                            extObs != null ? extObs.getSourceRecordId() : "null",
                            extObs != null ? extObs.getObservedAt() : "null",
                            obsVal.getReason());
                    totalSkipped.incrementAndGet();
                    continue;
                }

                CycloneObservation observation = existingMap.get(extObs.getSourceRecordId());
                if (observation != null) {
                    updatedObsCount++;
                } else {
                    observation = new CycloneObservation();
                    observation.setCyclone(cyclone);
                    observation.setSourceRecordId(extObs.getSourceRecordId());
                    newObsCount++;
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

            if (!toSave.isEmpty()) {
                observationRepository.saveAll(toSave);
                obsImported.addAndGet(newObsCount);
                obsUpdated.addAndGet(updatedObsCount);
            }
        }
    }
}
