package com.traveller.demo.service;

import com.traveller.demo.dto.MLEngineRequest;
import com.traveller.demo.dto.MLEngineResponse;
import com.traveller.demo.dto.TripPlanRequest;
import com.traveller.demo.entity.ItineraryItem;
import com.traveller.demo.entity.Trip;
import com.traveller.demo.entity.User;
import com.traveller.demo.repository.TripRepository;
import com.traveller.demo.repository.UserRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;

/**
 * TripService - Business logic for trip planning and management
 */
@Service
@Slf4j
public class TripService {

    private final TripRepository tripRepository;
    private final UserRepository userRepository;
    private final MLEngineClient mlEngineClient;

    public TripService(TripRepository tripRepository, UserRepository userRepository, MLEngineClient mlEngineClient) {
        this.tripRepository = tripRepository;
        this.userRepository = userRepository;
        this.mlEngineClient = mlEngineClient;
    }

    /**
     * Plan a new trip - Call ML engine, create Trip and ItineraryItems, save to DB
     * 
     * @param request - Trip planning request from frontend
     * @param userId  - ID of the authenticated user
     * @return Saved Trip with itinerary items
     */
    @Transactional
    public Trip planTrip(TripPlanRequest request, Long userId) {
        log.info("Planning trip for user {} to {}", userId, request.getDestination());

        // 1. Get user - throw exception if not found
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found with ID: " + userId));

        // 2. Calculate number of days
        int days = (int) ChronoUnit.DAYS.between(request.getStartDate(), request.getEndDate()) + 1;
        log.debug("Trip duration: {} days", days);

        // 3. Prepare ML Engine request
        MLEngineRequest mlRequest = new MLEngineRequest(
                request.getDestination(),
                days,
                request.getBudget(),
                request.getInterests());

        // 4. Call ML Engine to generate itinerary
        MLEngineResponse mlResponse = mlEngineClient.generateItinerary(mlRequest);

        // 5. Create Trip entity
        Trip trip = new Trip();
        trip.setUser(user);
        trip.setDestination(request.getDestination());
        trip.setTitle(request.getTitle() != null ? request.getTitle() : "Trip to " + request.getDestination());
        trip.setStartDate(request.getStartDate());
        trip.setEndDate(request.getEndDate());
        trip.setDays(days);
        trip.setBudgetLimit(request.getBudget());
        trip.setTotalEstimatedCost(mlResponse.getEstimatedCost());
        trip.setIsFeasible(mlResponse.getGreenSignal());

        // 6. Create ItineraryItems from ML response
        if (mlResponse.getDayByDay() != null) {
            for (MLEngineResponse.DayItinerary dayData : mlResponse.getDayByDay()) {
                if (dayData.getPois() != null) {
                    int orderIndex = 0;
                    for (MLEngineResponse.POI poi : dayData.getPois()) {
                        ItineraryItem item = new ItineraryItem();
                        item.setTrip(trip);
                        item.setDayNumber(dayData.getDay());
                        item.setPlaceName(poi.getName());
                        item.setPlaceType(poi.getType());
                        item.setLat(poi.getLat());
                        item.setLon(poi.getLon());
                        item.setCost(poi.getCost());
                        item.setDuration(poi.getDuration());
                        item.setOrderIndex(orderIndex++);

                        trip.addItineraryItem(item);
                    }
                }
            }
        }

        // 7. Save trip (cascade will save itinerary items)
        Trip savedTrip = tripRepository.save(trip);
        log.info("Trip saved with ID: {}", savedTrip.getId());

        return savedTrip;
    }

    /**
     * Get all trips for a user
     * 
     * @param userId - User's ID
     * @return List of trips
     */
    public List<Trip> getUserTrips(Long userId) {
        return tripRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    /**
     * Get a specific trip by ID
     * 
     * @param tripId - Trip's ID
     * @param userId - User's ID (for authorization)
     * @return Trip with itinerary items
     */
    public Trip getTripById(Long tripId, Long userId) {
        Trip trip = tripRepository.findById(tripId)
                .orElseThrow(() -> new RuntimeException("Trip not found with ID: " + tripId));

        // Verify the trip belongs to the user
        if (!trip.getUser().getId().equals(userId)) {
            throw new RuntimeException("Unauthorized access to trip");
        }

        return trip;
    }
}
