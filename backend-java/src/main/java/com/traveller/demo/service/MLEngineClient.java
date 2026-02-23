package com.traveller.demo.service;

import com.traveller.demo.dto.MLEngineRequest;
import com.traveller.demo.dto.MLEngineResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

/**
 * MLEngineClient - Service for communicating with the FastAPI ML Engine
 * Uses RestTemplate to make HTTP POST requests
 */
@Service
@Slf4j
public class MLEngineClient {

    @Value("${ml.engine.url}")
    private String mlEngineUrl;

    private final RestTemplate restTemplate;

    public MLEngineClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Call ML engine to generate itinerary
     * 
     * @param request - Request containing destination, days, budget, interests
     * @return ML engine response with generated itinerary
     * @throws RuntimeException if ML engine call fails
     */
    public MLEngineResponse generateItinerary(MLEngineRequest request) {
        try {
            String url = mlEngineUrl + "/generate_itinerary";
            log.info("Calling ML Engine at {}", url);
            log.debug("Request payload: {}", request);

            ResponseEntity<MLEngineResponse> response = restTemplate.postForEntity(
                    url,
                    request,
                    MLEngineResponse.class);

            MLEngineResponse responseBody = response.getBody();
            log.info("ML Engine response received successfully");
            log.debug("Response payload: {}", responseBody);

            return responseBody;

        } catch (Exception e) {
            log.error("Error calling ML Engine: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to generate itinerary from ML Engine: " + e.getMessage(), e);
        }
    }
}
