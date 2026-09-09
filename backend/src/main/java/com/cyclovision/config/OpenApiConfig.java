package com.cyclovision.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** Swagger UI at /swagger-ui.html — useful for manual endpoint checks during the build. */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI cycloVisionOpenApi() {
        return new OpenAPI().info(new Info()
                .title("CycloVision API")
                .version("phase0")
                .description("Tropical cyclone evolution intelligence. "
                        + "Read path serves precomputed frames; the forecast path applies "
                        + "temporal masking and adds verification from the database."));
    }
}
