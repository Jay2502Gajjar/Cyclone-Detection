package com.cyclovision;

import com.cyclovision.entity.Cyclone;
import com.cyclovision.entity.CycloneObservation;
import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.dto.ExternalObservationDto;
import com.cyclovision.ingestion.provider.CycloneDataProvider;
import com.cyclovision.ingestion.service.CycloneIngestionService;
import com.cyclovision.ingestion.validation.CycloneDataValidator;
import com.cyclovision.repository.CycloneObservationRepository;
import com.cyclovision.repository.CycloneRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionStatus;

import java.time.Instant;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CycloneIngestionMonitoringTest {

    @Mock
    private CycloneDataProvider mockProvider;

    @Mock
    private CycloneRepository cycloneRepository;

    @Mock
    private CycloneObservationRepository observationRepository;

    @Mock
    private PlatformTransactionManager transactionManager;

    @Mock
    private TransactionStatus transactionStatus;

    private CycloneDataValidator validator;
    private CycloneIngestionService ingestionService;

    @BeforeEach
    void setUp() {
        lenient().when(transactionManager.getTransaction(any())).thenReturn(transactionStatus);
        validator = new CycloneDataValidator();
        ingestionService = new CycloneIngestionService(
                List.of(mockProvider),
                cycloneRepository,
                observationRepository,
                transactionManager,
                validator
        );
    }

    @Test
    @DisplayName("Ingestion summary contains structured monitoring metadata")
    void testSuccessfulIngestionSummaryStructure() {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        ExternalCycloneDto cycloneDto = new ExternalCycloneDto();
        cycloneDto.setExternalId("MON_CYC_01");
        cycloneDto.setExternalSource("IBTrACS");
        cycloneDto.setName("MONITOR_STORM");
        cycloneDto.setBasin("NI");
        cycloneDto.setStatus("ACTIVE");

        when(mockProvider.fetchActiveCyclones()).thenReturn(List.of(cycloneDto));
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());

        Cyclone saved = new Cyclone();
        saved.setId(UUID.randomUUID());
        saved.setExternalId("MON_CYC_01");
        saved.setExternalSource("IBTrACS");
        when(cycloneRepository.save(any(Cyclone.class))).thenReturn(saved);

        Map<String, Object> result = ingestionService.runIngestion("IBTrACS");

        assertEquals("IBTrACS", result.get("provider"));
        assertNotNull(result.get("startTime"));
        assertNotNull(result.get("endTime"));
        assertTrue(((Number) result.get("durationMs")).longValue() >= 0);
        assertEquals(Boolean.TRUE, result.get("success"));
        assertEquals(1, result.get("cyclonesImported"));
        assertEquals(0, result.get("failures"));
        assertEquals(0, result.get("skippedRecords"));
        assertNotNull(result.get("failedCycloneIds"));
        assertTrue(((List<?>) result.get("failedCycloneIds")).isEmpty());
    }

    @Test
    @DisplayName("Single cyclone failure does not abort other cyclones and tracks failed ID")
    void testFailedCycloneDoesNotPreventOtherCyclonesFromBeingProcessed() {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        ExternalCycloneDto badCyclone = new ExternalCycloneDto();
        badCyclone.setExternalId("FAIL_CYC");
        badCyclone.setExternalSource("IBTrACS");
        badCyclone.setName("FAILING_STORM");

        ExternalCycloneDto goodCyclone = new ExternalCycloneDto();
        goodCyclone.setExternalId("GOOD_CYC");
        goodCyclone.setExternalSource("IBTrACS");
        goodCyclone.setName("GOOD_STORM");

        when(mockProvider.fetchActiveCyclones()).thenReturn(List.of(badCyclone, goodCyclone));
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());

        // Fail when saving bad cyclone, succeed on good cyclone
        when(cycloneRepository.save(argThat(c -> c != null && "FAIL_CYC".equals(c.getExternalId()))))
                .thenThrow(new RuntimeException("Simulated database write error for FAIL_CYC"));

        Cyclone goodSaved = new Cyclone();
        goodSaved.setId(UUID.randomUUID());
        goodSaved.setExternalId("GOOD_CYC");
        goodSaved.setExternalSource("IBTrACS");
        when(cycloneRepository.save(argThat(c -> c != null && "GOOD_CYC".equals(c.getExternalId()))))
                .thenReturn(goodSaved);

        Map<String, Object> result = ingestionService.runIngestion("IBTrACS");

        assertEquals(Boolean.FALSE, result.get("success"));
        assertEquals(1, result.get("failures"));
        assertEquals(1, result.get("cyclonesImported"), "Good cyclone must be imported despite the failure of the bad cyclone");

        @SuppressWarnings("unchecked")
        List<String> failedIds = (List<String>) result.get("failedCycloneIds");
        assertNotNull(failedIds);
        assertTrue(failedIds.contains("FAIL_CYC"), "Failed cyclone ID must be recorded");
    }

    @Test
    @DisplayName("Validation skips are counted and preserved in the execution summary")
    void testValidationSkipsRemainCountedInSummary() {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        ExternalCycloneDto cycloneDto = new ExternalCycloneDto();
        cycloneDto.setExternalId("TEST_CYC");
        cycloneDto.setExternalSource("IBTrACS");
        cycloneDto.setName("TEST_STORM");

        when(mockProvider.fetchActiveCyclones()).thenReturn(List.of(cycloneDto));
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());

        Cyclone saved = new Cyclone();
        saved.setId(UUID.randomUUID());
        saved.setExternalId("TEST_CYC");
        saved.setExternalSource("IBTrACS");
        when(cycloneRepository.save(any(Cyclone.class))).thenReturn(saved);

        ExternalObservationDto validObs = new ExternalObservationDto();
        validObs.setExternalCycloneId("TEST_CYC");
        validObs.setSourceRecordId("OBS_OK");
        validObs.setSource("IBTrACS");
        validObs.setObservedAt(Instant.parse("2026-06-01T00:00:00Z"));
        validObs.setLatitude(15.0);
        validObs.setLongitude(85.0);

        ExternalObservationDto invalidObs = new ExternalObservationDto();
        invalidObs.setExternalCycloneId("TEST_CYC");
        invalidObs.setSourceRecordId("OBS_BAD");
        invalidObs.setSource("IBTrACS");
        invalidObs.setObservedAt(Instant.parse("2026-06-01T06:00:00Z"));
        invalidObs.setLatitude(199.0); // Invalid latitude
        invalidObs.setLongitude(85.0);

        when(mockProvider.fetchObservations("TEST_CYC")).thenReturn(List.of(validObs, invalidObs));

        Map<String, Object> result = ingestionService.runIngestion("IBTrACS");

        assertEquals(Boolean.TRUE, result.get("success"));
        assertEquals(1, result.get("observationsImported"));
        assertEquals(1, result.get("skippedRecords"), "Skipped invalid observation must be counted");
        assertEquals(0, result.get("failures"));
    }

    @Test
    @DisplayName("Provider-level failure is tracked and reported cleanly")
    void testProviderLevelFailureReportedInSummary() {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");
        when(mockProvider.fetchActiveCyclones()).thenThrow(new RuntimeException("Simulated provider fetch failure"));

        Map<String, Object> result = ingestionService.runIngestion("IBTrACS");

        assertEquals(Boolean.FALSE, result.get("success"));
        assertEquals(1, result.get("failures"));
        @SuppressWarnings("unchecked")
        List<String> failedIds = (List<String>) result.get("failedCycloneIds");
        assertNotNull(failedIds);
        assertTrue(failedIds.contains("PROVIDER_IBTrACS"));
    }
}
