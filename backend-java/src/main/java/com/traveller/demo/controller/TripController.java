package com.traveller.demo.controller;

import com.traveller.demo.dto.TripPlanRequest;
import com.traveller.demo.dto.TripResponse;
import com.traveller.demo.entity.Trip;
import com.traveller.demo.service.TripService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;

/**
 * TripController - REST API endpoints for trip management
 * Base path: /api/trips
 */
@RestController
@RequestMapping("/api/trips")
@Slf4j
public class TripController {

    private final TripService tripService;

    public TripController(TripService tripService) {
        this.tripService = tripService;
    }

    /**
     * POST /api/trips/plan - Plan a new trip
     * Calls ML engine, creates trip and itinerary items, saves to database
     * 
     * @param request - Trip planning request (destination, dates, budget,
     *                interests)
     * @return TripResponse with generated itinerary
     */
    @PostMapping("/plan")
    public ResponseEntity<TripResponse> planTrip(@Valid @RequestBody TripPlanRequest request) {
        log.info("Received trip planning request for destination: {}", request.getDestination());
        log.debug("Request details: {}", request);

        try {
            // For now, using hardcoded user ID = 1
            // TODO: Replace with actual authenticated user ID from JWT token
            Long userId = 1L;

            Trip trip = tripService.planTrip(request, userId);
            TripResponse response = TripResponse.fromEntity(trip);

            log.info("Trip created successfully with ID: {}", trip.getId());
            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (RuntimeException e) {
            log.error("Runtime error planning trip: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(null);
        } catch (Exception e) {
            log.error("Error planning trip: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * GET /api/trips - Get all trips for the authenticated user
     * 
     * @return List of trips
     */
    @GetMapping
    public ResponseEntity<List<TripResponse>> getUserTrips() {
        log.info("Fetching trips for user");

        try {
            // For now, using hardcoded user ID = 1
            // TODO: Replace with actual authenticated user ID from JWT token
            Long userId = 1L;

            List<Trip> trips = tripService.getUserTrips(userId);
            List<TripResponse> responses = trips.stream()
                    .map(TripResponse::fromEntity)
                    .collect(Collectors.toList());

            log.info("Found {} trips for user", responses.size());
            return ResponseEntity.ok(responses);

        } catch (Exception e) {
            log.error("Error fetching trips: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * GET /api/trips/{id} - Get a specific trip by ID
     * 
     * @param id - Trip ID
     * @return Trip with full itinerary
     */
    @GetMapping("/{id}")
    public ResponseEntity<TripResponse> getTripById(@PathVariable Long id) {
        log.info("Fetching trip with ID: {}", id);

        try {
            // For now, using hardcoded user ID = 1
            // TODO: Replace with actual authenticated user ID from JWT token
            Long userId = 1L;

            Trip trip = tripService.getTripById(id, userId);
            TripResponse response = TripResponse.fromEntity(trip);

            return ResponseEntity.ok(response);

        } catch (RuntimeException e) {
            log.error("Error fetching trip: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        } catch (Exception e) {
            log.error("Error fetching trip: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
