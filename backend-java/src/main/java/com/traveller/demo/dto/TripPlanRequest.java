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
     * Trip start date
     */
    @NotNull(message = "Start date is required")
    @FutureOrPresent(message = "Start date must be today or in the future")
    private LocalDate startDate;

    /**
     * Trip end date (must be >= start date)
     */
    @NotNull(message = "End date is required")
    @FutureOrPresent(message = "End date must be today or in the future")
    private LocalDate endDate;

    /**
     * User's budget (in USD)
     */
    @NotNull(message = "Budget is required")
    @DecimalMin(value = "100.0", message = "Budget must be at least $100")
    private BigDecimal budget;

    /**
     * List of user's interests (e.g., ["museum", "food", "adventure"] )
     */
    @NotEmpty(message = "At least one interest is required")
    private List<String> interests;
}
