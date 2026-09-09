package com.cyclovision;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;

import static org.junit.jupiter.api.Assertions.assertFalse;

@SpringBootTest
class ConditionalProviderTests {

    @Autowired
    private ApplicationContext applicationContext;

    @Test
    void testMockProviderDisabledByDefault() {
        assertFalse(
                applicationContext.containsBean("mockCycloneDataProvider"),
                "MockCycloneDataProvider bean must NOT be registered by default when cyclovision.mock-provider.enabled is false or missing"
        );
    }

    @Test
    void testDemoDataSeederDisabledByDefault() {
        assertFalse(
                applicationContext.containsBean("demoDataSeeder"),
                "DemoDataSeeder bean must NOT be registered by default when cyclovision.demo-data.enabled is false or missing"
        );
    }
}
