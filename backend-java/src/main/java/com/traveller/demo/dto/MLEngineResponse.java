package com.traveller.demo.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * MLEngineResponse DTO - Response payload received from ML Engine (FastAPI)
 * Contains generated itinerary with day-by-day breakdown
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class MLEngineResponse {

    /**
     * Destination (echoed from request)
     */
    private String destination;

    /**
     * Number of days (echoed from request)
     */
    private Integer days;

    /**
     * User's budget limit
     */
    private BigDecimal totalBudget;

    /**
     * Estimated cost calculated by ML engine
     */
    private BigDecimal estimatedCost;

    /**
     * Green signal (true) = within budget, Red signal (false) = over budget
     */
    private Boolean greenSignal;

    /**
     * Day-by-day itinerary breakdown
     */
    private List<DayItinerary> dayByDay;

    /**
     * DayItinerary - Represents one day in the trip
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DayItinerary {
        /**
         * Day number (1-based)
         */
        private Integer day;

        /**
         * Date in ISO format (YYYY-MM-DD)
         */
        private String date;

        /**
         * List of points of interest for this day
         */
        private List<POI> pois;
    }

    /**
     * POI - Point of Interest (a place to visit)
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class POI {
        /**
         * Name of the place
         */
        private String name;

        /**
         * Type/category (museum, food, etc.)
         */
        private String type;

        /**
         * Estimated cost to visit (in USD)
         */
        private BigDecimal cost;

        /**
         * Duration to spend (in hours)
         */
        private Integer duration;

        /**
         * Latitude coordinate
         */
        private BigDecimal lat;

        /**
         * Longitude coordinate
         */
        private BigDecimal lon;
    }
}
