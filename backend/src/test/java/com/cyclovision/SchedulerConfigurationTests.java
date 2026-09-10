package com.cyclovision;

import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SchedulerConfigurationTests {

    @SpringBootTest
    @Nested
    class DefaultConfiguration {
        @Autowired
        private ApplicationContext applicationContext;

        @Test
        void testSchedulerIsEnabledByDefault() {
            assertTrue(
                    applicationContext.containsBean("cycloneIngestionScheduler"),
                    "CycloneIngestionScheduler must be registered by default when cyclovision.ingestion.scheduler.enabled is true or missing"
            );
        }
    }

    @SpringBootTest(properties = {"cyclovision.ingestion.scheduler.enabled=false"})
    @Nested
    class DisabledConfiguration {
        @Autowired
        private ApplicationContext applicationContext;

        @Test
        void testSchedulerCanBeDisabledViaConfiguration() {
            assertFalse(
                    applicationContext.containsBean("cycloneIngestionScheduler"),
                    "CycloneIngestionScheduler must NOT be registered when cyclovision.ingestion.scheduler.enabled=false"
            );
        }
    }
}
