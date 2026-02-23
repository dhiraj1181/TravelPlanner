package com.traveller.demo.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * RestTemplateConfig - Configuration for RestTemplate bean
 * RestTemplate is used to make HTTP calls to external services (ML Engine)
 */
@Configuration
public class RestTemplateConfig {

    /**
     * Create and configure RestTemplate bean
     * 
     * @return Configured RestTemplate instance
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
