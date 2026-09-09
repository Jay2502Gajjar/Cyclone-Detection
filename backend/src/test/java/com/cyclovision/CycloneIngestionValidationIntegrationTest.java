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
import org.mockito.ArgumentCaptor;
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
class CycloneIngestionValidationIntegrationTest {

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
    @DisplayName("Invalid observation is skipped while valid observation is saved")
    void testInvalidObservationSkippedAndValidObservationSaved() {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        ExternalCycloneDto cycloneDto = new ExternalCycloneDto();
        cycloneDto.setExternalId("TEST_CYC_01");
        cycloneDto.setExternalSource("IBTrACS");
        cycloneDto.setName("VALID_CYCLONE");
        cycloneDto.setBasin("NI");
        cycloneDto.setStatus("ACTIVE");

        when(mockProvider.fetchActiveCyclones()).thenReturn(List.of(cycloneDto));
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());

        Cyclone savedCyclone = new Cyclone();
        savedCyclone.setId(UUID.randomUUID());
        savedCyclone.setExternalId("TEST_CYC_01");
        savedCyclone.setExternalSource("IBTrACS");
        when(cycloneRepository.save(any(Cyclone.class))).thenReturn(savedCyclone);

        // Create 1 valid observation and 1 invalid observation (invalid latitude 999.0)
        ExternalObservationDto validObs = new ExternalObservationDto();
        validObs.setExternalCycloneId("TEST_CYC_01");
        validObs.setSourceRecordId("OBS_VALID");
        validObs.setSource("IBTrACS");
        validObs.setObservedAt(Instant.parse("2026-06-01T00:00:00Z"));
        validObs.setLatitude(15.0);
        validObs.setLongitude(85.0);
        validObs.setWindSpeedKph(100.0);
        validObs.setPressureHpa(980.0);

        ExternalObservationDto invalidObs = new ExternalObservationDto();
        invalidObs.setExternalCycloneId("TEST_CYC_01");
        invalidObs.setSourceRecordId("OBS_INVALID");
        invalidObs.setSource("IBTrACS");
        invalidObs.setObservedAt(Instant.parse("2026-06-01T06:00:00Z"));
        invalidObs.setLatitude(999.0); // INVALID latitude
        invalidObs.setLongitude(85.0);

        when(mockProvider.fetchObservations("TEST_CYC_01")).thenReturn(List.of(validObs, invalidObs));

        Map<String, Object> result = ingestionService.runIngestion("IBTrACS");

        assertTrue((Boolean) result.get("success"));
        assertEquals(1, result.get("cyclonesImported"));
        assertEquals(1, result.get("observationsImported"));
        assertEquals(1, result.get("skippedRecords"));

        @SuppressWarnings("unchecked")
        ArgumentCaptor<List<CycloneObservation>> captor = ArgumentCaptor.forClass(List.class);
        verify(observationRepository, times(1)).saveAll(captor.capture());

        List<CycloneObservation> savedObs = captor.getValue();
        assertEquals(1, savedObs.size(), "Only the 1 valid observation should be saved");
        assertEquals("OBS_VALID", savedObs.get(0).getSourceRecordId());
    }

    @Test
    @DisplayName("Invalid cyclone with blank externalId is rejected and skipped")
    void testInvalidCycloneIsSkipped() {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        ExternalCycloneDto invalidCyclone = new ExternalCycloneDto();
        invalidCyclone.setExternalId("   "); // blank externalId
        invalidCyclone.setExternalSource("IBTrACS");
        invalidCyclone.setName("BAD_STORM");

        when(mockProvider.fetchActiveCyclones()).thenReturn(List.of(invalidCyclone));
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());

        Map<String, Object> result = ingestionService.runIngestion("IBTrACS");

        assertTrue((Boolean) result.get("success"));
        assertEquals(0, result.get("cyclonesImported"));
        assertEquals(1, result.get("skippedRecords"));
        verify(cycloneRepository, never()).save(any(Cyclone.class));
        verify(observationRepository, never()).saveAll(any());
    }
}
