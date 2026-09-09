package com.cyclovision;

import com.cyclovision.controller.IngestionController;
import com.cyclovision.ingestion.dto.ExternalCycloneDto;
import com.cyclovision.ingestion.provider.CycloneDataProvider;
import com.cyclovision.ingestion.service.CycloneIngestionService;
import com.cyclovision.repository.CycloneObservationRepository;
import com.cyclovision.repository.CycloneRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.PlatformTransactionManager;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CycloneIngestionConcurrencyTest {

    @Mock
    private CycloneDataProvider mockProvider;

    @Mock
    private CycloneRepository cycloneRepository;

    @Mock
    private CycloneObservationRepository observationRepository;

    @Mock
    private PlatformTransactionManager transactionManager;

    private CycloneIngestionService ingestionService;
    private IngestionController ingestionController;

    @BeforeEach
    void setUp() {
        when(mockProvider.getProviderName()).thenReturn("MOCK");
        ingestionService = new CycloneIngestionService(
                List.of(mockProvider),
                cycloneRepository,
                observationRepository,
                transactionManager
        );
        ingestionController = new IngestionController(ingestionService);
    }

    @Test
    void testConcurrencyProtectionPreventsOverlappingRuns() throws Exception {
        CountDownLatch runStarted = new CountDownLatch(1);
        CountDownLatch blockLatch = new CountDownLatch(1);

        // Configure provider to block until released
        when(mockProvider.fetchActiveCyclones()).thenAnswer(invocation -> {
            runStarted.countDown();
            blockLatch.await(5, TimeUnit.SECONDS);
            return Collections.emptyList();
        });

        ExecutorService executor = Executors.newFixedThreadPool(2);
        try {
            // Thread 1: Starts ingestion and holds the lock
            Future<Map<String, Object>> future1 = executor.submit(() -> ingestionService.runIngestion("MOCK"));

            // Wait for Thread 1 to enter the run
            assertTrue(runStarted.await(2, TimeUnit.SECONDS));
            assertTrue(ingestionService.isIngestionRunning(), "Ingestion lock should be held");

            // Thread 2: Concurrent attempt must skip immediately
            Map<String, Object> result2 = ingestionService.runIngestion("MOCK");
            assertEquals(false, result2.get("success"), "Concurrent run must not report success");
            assertEquals(true, result2.get("skipped"), "Concurrent run must report skipped");
            assertEquals("Ingestion is already in progress", result2.get("message"));

            // Release Thread 1
            blockLatch.countDown();
            Map<String, Object> result1 = future1.get(5, TimeUnit.SECONDS);
            assertEquals(true, result1.get("success"), "First run should complete successfully");

            // Now that Thread 1 finished, lock must be free
            assertFalse(ingestionService.isIngestionRunning(), "Lock should be released after completion");

            // Thread 3 can now run successfully
            when(mockProvider.fetchActiveCyclones()).thenReturn(Collections.emptyList());
            Map<String, Object> result3 = ingestionService.runIngestion("MOCK");
            assertEquals(true, result3.get("success"), "Subsequent run must succeed after lock is released");

        } finally {
            blockLatch.countDown();
            executor.shutdownNow();
        }
    }

    @Test
    void testManualTriggerSharesConcurrencyProtection() throws Exception {
        CountDownLatch runStarted = new CountDownLatch(1);
        CountDownLatch blockLatch = new CountDownLatch(1);

        when(mockProvider.fetchActiveCyclones()).thenAnswer(invocation -> {
            runStarted.countDown();
            blockLatch.await(5, TimeUnit.SECONDS);
            return Collections.emptyList();
        });

        ExecutorService executor = Executors.newSingleThreadExecutor();
        try {
            // Background thread starts ingestion (simulating scheduler)
            executor.submit(() -> ingestionService.runIngestion("MOCK"));
            assertTrue(runStarted.await(2, TimeUnit.SECONDS));

            // Manual controller endpoint is invoked while scheduler is running
            ResponseEntity<Map<String, Object>> response = ingestionController.triggerIngestion("MOCK");
            assertNotNull(response.getBody());
            assertEquals(false, response.getBody().get("success"));
            assertEquals(true, response.getBody().get("skipped"));
            assertEquals("Ingestion is already in progress", response.getBody().get("message"));

        } finally {
            blockLatch.countDown();
            executor.shutdownNow();
        }
    }

    @Test
    void testLockIsReleasedWhenIngestionFails() {
        when(mockProvider.fetchActiveCyclones()).thenThrow(new RuntimeException("Simulated provider failure"));

        Map<String, Object> result = ingestionService.runIngestion("MOCK");
        assertEquals(false, result.get("success"));

        // Lock must be released even after failure
        assertFalse(ingestionService.isIngestionRunning(), "Lock must be released on failure");

        // Next run can acquire lock
        doReturn(Collections.emptyList()).when(mockProvider).fetchActiveCyclones();
        Map<String, Object> retryResult = ingestionService.runIngestion("MOCK");
        assertEquals(true, retryResult.get("success"), "Subsequent run must succeed after previous failure");
    }
}
