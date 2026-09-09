package com.cyclovision.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * The one WebClient used to reach the AI service.
 *
 * <p>The buffer limit is raised because a full analysis response carries SHAP factors,
 * analogue tracks and structural metrics for a whole forecast in a single payload.
 */
@Configuration
public class WebClientConfig {

    @Bean
    public WebClient aiWebClient(@Value("${cyclovision.ai-service.url:http://localhost:8000}")
            String baseUrl) {
        return WebClient.builder()
                .baseUrl(baseUrl)
                .codecs(c -> c.defaultCodecs().maxInMemorySize(8 * 1024 * 1024))
                .build();
    }
}
