package com.cyclovision;

import com.cyclovision.controller.IngestionController;
import com.cyclovision.entity.Cyclone;
import com.cyclovision.ingestion.dto.ExternalCycloneDto;
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
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionStatus;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CycloneIngestionHealthStatusTest {

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
    private IngestionController ingestionController;

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
        ingestionController = new IngestionController(ingestionService);
    }

    @Test
    @DisplayName("Initial ingestion status reports not running and null last-run metadata")
    void testInitialStatusBeforeAnyRun() {
        Map<String, Object> status = ingestionService.getIngestionStatus();

        assertNotNull(status);
        assertEquals(Boolean.FALSE, status.get("running"));
        assertNull(status.get("provider"));
        assertNull(status.get("currentRunStartTime"));
        assertNull(status.get("lastRunStartTime"));
        assertNull(status.get("lastRunEndTime"));
        assertNull(status.get("lastRunDurationMs"));
        assertNull(status.get("lastRunSuccess"));
        assertNull(status.get("lastRunFailures"));
        assertNull(status.get("lastRunSkippedRecords"));
    }

    @Test
    @DisplayName("Status reports running=true during execution and updates lastRun on success")
    void testStatusBecomesRunningDuringIngestionAndUpdatesOnCompletion() throws Exception {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        CountDownLatch runStarted = new CountDownLatch(1);
        CountDownLatch allowCompletion = new CountDownLatch(1);

        ExternalCycloneDto cycloneDto = new ExternalCycloneDto();
        cycloneDto.setExternalId("CYC_STATUS_TEST");
        cycloneDto.setExternalSource("IBTrACS");
        cycloneDto.setName("STATUS_TEST_CYCLONE");

        when(mockProvider.fetchActiveCyclones()).thenAnswer(inv -> {
            runStarted.countDown();
            assertTrue(allowCompletion.await(5, TimeUnit.SECONDS), "Timed out waiting for completion signal");
            return List.of(cycloneDto);
        });
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());

        Cyclone saved = new Cyclone();
        saved.setId(UUID.randomUUID());
        saved.setExternalId("CYC_STATUS_TEST");
        saved.setExternalSource("IBTrACS");
        when(cycloneRepository.save(any(Cyclone.class))).thenReturn(saved);

        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<Map<String, Object>> future = executor.submit(() -> ingestionService.runIngestion("IBTrACS"));

        assertTrue(runStarted.await(5, TimeUnit.SECONDS), "Ingestion did not start in time");

        // Verify status while running
        Map<String, Object> runningStatus = ingestionService.getIngestionStatus();
        assertEquals(Boolean.TRUE, runningStatus.get("running"));
        assertEquals("IBTrACS", runningStatus.get("provider"));
        assertNotNull(runningStatus.get("currentRunStartTime"));

        // Allow run to finish
        allowCompletion.countDown();
        Map<String, Object> result = future.get(5, TimeUnit.SECONDS);
        assertEquals(Boolean.TRUE, result.get("success"));

        // Verify status after completion
        Map<String, Object> completedStatus = ingestionService.getIngestionStatus();
        assertEquals(Boolean.FALSE, completedStatus.get("running"));
        assertEquals("IBTrACS", completedStatus.get("provider"));
        assertNull(completedStatus.get("currentRunStartTime"));
        assertNotNull(completedStatus.get("lastRunStartTime"));
        assertNotNull(completedStatus.get("lastRunEndTime"));
        assertNotNull(completedStatus.get("lastRunDurationMs"));
        assertEquals(Boolean.TRUE, completedStatus.get("lastRunSuccess"));
        assertEquals(0, completedStatus.get("lastRunFailures"));
        assertEquals(0, completedStatus.get("lastRunSkippedRecords"));

        executor.shutdown();
    }

    @Test
    @DisplayName("Failed ingestion updates lastRun with failure count and error message")
    void testFailedIngestionUpdatesLastRunFailureInformation() {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        ExternalCycloneDto badCyclone = new ExternalCycloneDto();
        badCyclone.setExternalId("FAILING_CYC");
        badCyclone.setExternalSource("IBTrACS");

        when(mockProvider.fetchActiveCyclones()).thenReturn(List.of(badCyclone));
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());
        when(cycloneRepository.save(any(Cyclone.class))).thenThrow(new RuntimeException("Simulated save failure"));

        Map<String, Object> result = ingestionService.runIngestion("IBTrACS");
        assertEquals(Boolean.FALSE, result.get("success"));

        Map<String, Object> status = ingestionService.getIngestionStatus();
        assertEquals(Boolean.FALSE, status.get("running"));
        assertEquals("IBTrACS", status.get("provider"));
        assertEquals(Boolean.FALSE, status.get("lastRunSuccess"));
        assertEquals(1, status.get("lastRunFailures"));
        assertTrue(((String) status.get("lastRunMessage")).contains("1 failure"));
    }

    @Test
    @DisplayName("Skipped concurrent execution does not corrupt active or lastRun status")
    void testSkippedConcurrentExecutionDoesNotCorruptStatus() throws Exception {
        when(mockProvider.getProviderName()).thenReturn("IBTrACS");

        CountDownLatch runStarted = new CountDownLatch(1);
        CountDownLatch allowCompletion = new CountDownLatch(1);

        when(mockProvider.fetchActiveCyclones()).thenAnswer(inv -> {
            runStarted.countDown();
            assertTrue(allowCompletion.await(5, TimeUnit.SECONDS));
            return Collections.emptyList();
        });
        when(cycloneRepository.findByExternalSource("IBTrACS")).thenReturn(Collections.emptyList());

        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<Map<String, Object>> future = executor.submit(() -> ingestionService.runIngestion("IBTrACS"));

        assertTrue(runStarted.await(5, TimeUnit.SECONDS));

        // Attempt concurrent execution while primary is running
        Map<String, Object> skippedResult = ingestionService.runIngestion("IBTrACS");
        assertEquals(Boolean.TRUE, skippedResult.get("skipped"));

        // Verify status still points to the ongoing primary run
        Map<String, Object> statusDuring = ingestionService.getIngestionStatus();
        assertEquals(Boolean.TRUE, statusDuring.get("running"));
        assertEquals("IBTrACS", statusDuring.get("provider"));
        assertNull(statusDuring.get("lastRunEndTime"));

        allowCompletion.countDown();
        future.get(5, TimeUnit.SECONDS);

        // Verify final status is cleanly populated
        Map<String, Object> finalStatus = ingestionService.getIngestionStatus();
        assertEquals(Boolean.FALSE, finalStatus.get("running"));
        assertEquals(Boolean.TRUE, finalStatus.get("lastRunSuccess"));

        executor.shutdown();
    }

    @Test
    @DisplayName("GET /api/internal/ingest/status returns 200 OK and expected structure")
    void testStatusEndpointReturnsExpectedResponse() {
        ResponseEntity<Map<String, Object>> response = ingestionController.getIngestionStatus();

        assertEquals(HttpStatus.OK, response.getStatusCode());
        Map<String, Object> body = response.getBody();
        assertNotNull(body);
        assertTrue(body.containsKey("running"));
        assertTrue(body.containsKey("provider"));
        assertTrue(body.containsKey("currentRunStartTime"));
        assertTrue(body.containsKey("lastRunStartTime"));
        assertTrue(body.containsKey("lastRunEndTime"));
        assertTrue(body.containsKey("lastRunDurationMs"));
        assertTrue(body.containsKey("lastRunSuccess"));
        assertTrue(body.containsKey("lastRunFailures"));
        assertTrue(body.containsKey("lastRunSkippedRecords"));
        assertTrue(body.containsKey("lastRunMessage"));
    }
}
