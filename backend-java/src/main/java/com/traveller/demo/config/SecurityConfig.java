package com.traveller.demo.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

import static org.springframework.security.config.Customizer.withDefaults;

/**
 * SecurityConfig - Temporary security configuration
 * Disables authentication for development and testing
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    /**
     * Configure security to permit all requests and enable CORS.
     * .cors(withDefaults()) is critical — without it Spring Security
     * blocks all OPTIONS preflight requests before the CorsFilter runs.
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .cors(withDefaults())                           // ← lets CorsFilter handle preflight
                .csrf(csrf -> csrf.disable())                   // disable CSRF for REST API
                .authorizeHttpRequests(auth -> auth
                        .anyRequest().permitAll()               // allow all requests
                );

        return http.build();
    }
}
