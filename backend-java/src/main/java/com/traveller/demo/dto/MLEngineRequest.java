package com.traveller.demo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * MLEngineRequest DTO - Request payload sent to ML Engine (FastAPI)
 * Mapped from TripPlanRequest
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class MLEngineRequest {

    /**
     * Destination city
     */
    private String destination;

    /**
     * Number of days for the trip
     */
    private Integer days;

    /**
     * User's budget (in USD)
     */
    private BigDecimal budget;

    /**
     * List of user's interests
     */
    private List<String> interests;

    /**
     * User ID for personalized recommendations (avoids repeating seen POIs)
     */
    private Long userId;
}
