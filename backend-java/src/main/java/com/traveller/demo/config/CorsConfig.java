package com.traveller.demo.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * CorsConfig - Cross-Origin Resource Sharing configuration
 * Allows frontend running on different port to access backend API
 */
@Configuration
public class CorsConfig {

    @Value("${cors.allowed.origins}")
    private String[] allowedOrigins;

    /**
     * Configure CORS filter
     * 
     * @return CorsFilter bean
     */
    @Bean
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();

        // Allow credentials (cookies, authorization headers)
        config.setAllowCredentials(true);

        // Set allowed origin patterns (supports wildcards, works with allowCredentials)
        // Also includes "null" to allow requests from file:// pages (browser sends Origin: null)
        List<String> patterns = new ArrayList<>(Arrays.asList(allowedOrigins));
        patterns.add("null"); // file:// origin
        config.setAllowedOriginPatterns(patterns);

        // Allow all HTTP methods
        config.addAllowedMethod("*");

        // Allow all headers
        config.addAllowedHeader("*");

        // Apply CORS configuration to all endpoints
        source.registerCorsConfiguration("/**", config);

        return new CorsFilter(source);
    }
}
