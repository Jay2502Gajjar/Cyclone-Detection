package com.cyclovision;

import com.cyclovision.ingestion.scheduler.CycloneIngestionScheduler;
import com.cyclovision.ingestion.service.CycloneIngestionService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CycloneIngestionSchedulerTest {

    @Mock
    private CycloneIngestionService ingestionService;

    private CycloneIngestionScheduler scheduler;

    @BeforeEach
    void setUp() {
        scheduler = new CycloneIngestionScheduler(ingestionService);
    }

    @Test
    void testScheduledIngestionInvokesExistingService() {
        when(ingestionService.runIngestion(eq("IBTrACS")))
                .thenReturn(Map.of("success", true, "message", "Completed"));

        scheduler.scheduleIngestion();

        verify(ingestionService, times(1)).runIngestion("IBTrACS");
    }

    @Test
    void testScheduledIngestionHandlesSkippedWhenBusy() {
        when(ingestionService.runIngestion(eq("IBTrACS")))
                .thenReturn(Map.of("success", false, "skipped", true, "message", "Ingestion is already in progress"));

        assertDoesNotThrow(() -> scheduler.scheduleIngestion());

        verify(ingestionService, times(1)).runIngestion("IBTrACS");
    }

    @Test
    void testIngestionFailureDoesNotDisableFutureRuns() {
        // Run 1: Fails with unexpected exception
        when(ingestionService.runIngestion(eq("IBTrACS")))
                .thenThrow(new RuntimeException("Simulated network/DB disconnect"))
                .thenReturn(Map.of("success", true, "message", "Completed"));

        // First run should catch exception and not rethrow
        assertDoesNotThrow(() -> scheduler.scheduleIngestion());

        // Second run should proceed normally without being permanently disabled
        assertDoesNotThrow(() -> scheduler.scheduleIngestion());

        verify(ingestionService, times(2)).runIngestion("IBTrACS");
    }
}
