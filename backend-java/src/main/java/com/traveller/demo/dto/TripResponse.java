package com.traveller.demo.dto;

import com.traveller.demo.entity.Trip;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * TripResponse DTO - Response payload sent to frontend
 * Includes trip details and formatted itinerary
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TripResponse {

    private Long id;
    private String destination;
    private String title;
    private LocalDate startDate;
    private LocalDate endDate;
    private Integer days;
    private BigDecimal budget;
    private ItineraryData itinerary;

    /**
     * Nested class for itinerary data
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ItineraryData {
        private BigDecimal estimatedCost;
        private Boolean greenSignal;
        private List<DayItinerary> dayByDay;
    }

    /**
     * Nested class for day itinerary
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DayItinerary {
        private Integer day;
        private String date;
        private List<POI> pois;
    }

    /**
     * Nested class for POI (Point of Interest)
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class POI {
        private String name;
        private String type;
        private BigDecimal cost;
        private Integer duration;
        private BigDecimal lat;
        private BigDecimal lon;
    }

    /**
     * Factory method to create TripResponse from Trip entity
     * 
     * @param trip - Trip entity
     * @return TripResponse DTO
     */
    public static TripResponse fromEntity(Trip trip) {
        TripResponse response = new TripResponse();
        response.setId(trip.getId());
        response.setDestination(trip.getDestination());
        response.setTitle(trip.getTitle());
        response.setStartDate(trip.getStartDate());
        response.setEndDate(trip.getEndDate());
        response.setDays(trip.getDays());
        response.setBudget(trip.getBudgetLimit());

        // Build itinerary data
        ItineraryData itineraryData = new ItineraryData();
        itineraryData.setEstimatedCost(trip.getTotalEstimatedCost());
        itineraryData.setGreenSignal(trip.getIsFeasible());

        // Group itinerary items by day
        List<DayItinerary> dayByDay = new ArrayList<>();
        if (trip.getItineraryItems() != null && !trip.getItineraryItems().isEmpty()) {
            // Find all unique day numbers
            List<Integer> dayNumbers = trip.getItineraryItems().stream()
                    .map(item -> item.getDayNumber())
                    .distinct()
                    .sorted()
                    .collect(Collectors.toList());

            // For each day, create a DayItinerary
            for (Integer dayNumber : dayNumbers) {
                DayItinerary dayItinerary = new DayItinerary();
                dayItinerary.setDay(dayNumber);

                // Calculate date for this day
                LocalDate dayDate = trip.getStartDate().plusDays(dayNumber - 1);
                dayItinerary.setDate(dayDate.toString());

                // Get all POIs for this day
                List<POI> pois = trip.getItineraryItems().stream()
                        .filter(item -> item.getDayNumber().equals(dayNumber))
                        .map(item -> new POI(
                                item.getPlaceName(),
                                item.getPlaceType(),
                                item.getCost(),
                                item.getDuration(),
                                item.getLat(),
                                item.getLon()))
                        .collect(Collectors.toList());

                dayItinerary.setPois(pois);
                dayByDay.add(dayItinerary);
            }
        }

        itineraryData.setDayByDay(dayByDay);
        response.setItinerary(itineraryData);

        return response;
    }
}
