package com.traveller.demo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

/**
 * TripPlanRequest DTO - Request payload for creating a new trip
 * Received from frontend when user submits trip planning form
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TripPlanRequest {

    /**
     * Destination city/country (e.g., "Paris, France")
     */
    @NotBlank(message = "Destination is required")
    private String destination;

    /**
     * Trip title (e.g., "Summer Vacation 2025")
     */
    private String title;

    /**
     * Trip start date — validated by the frontend; no server-side @FutureOrPresent
     * to avoid UTC vs IST clock skew rejecting valid Indian dates.
     */
    @NotNull(message = "Start date is required")
    private LocalDate startDate;

    /**
     * Trip end date — validated by the frontend; no @FutureOrPresent for same reason.
     */
    @NotNull(message = "End date is required")
    private LocalDate endDate;

    /**
     * User's budget in INR (validated >0 on frontend)
     */
    @NotNull(message = "Budget is required")
    private BigDecimal budget;

    /**
     * List of user's interests (e.g., ["museum", "food", "adventure"] )
     */
    @NotEmpty(message = "At least one interest is required")
    private List<String> interests;
}
