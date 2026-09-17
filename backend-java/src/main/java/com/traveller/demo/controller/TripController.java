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
 *
 * User identity is resolved from the X-User-Id request header, which the
 * frontend sends after login (user.id stored in localStorage).
 */
@RestController
@RequestMapping("/api/trips")
@Slf4j
public class TripController {

    private final TripService tripService;

    public TripController(TripService tripService) {
        this.tripService = tripService;
    }

    // ── Helper ──────────────────────────────────────────────────────────────
    /**
     * Extract user ID from the X-User-Id header.
     * Falls back to 1L if the header is absent (useful for curl / local testing).
     */
    private Long resolveUserId(String userIdHeader) {
        if (userIdHeader != null && !userIdHeader.isBlank()) {
            try {
                return Long.parseLong(userIdHeader.trim());
            } catch (NumberFormatException ex) {
                log.warn("Invalid X-User-Id header value: '{}', falling back to 1", userIdHeader);
            }
        }
        return 1L; // fallback – only reached when header is missing
    }

    // ── Endpoints ───────────────────────────────────────────────────────────

    /**
     * POST /api/trips/plan - Plan a new trip for the requesting user.
     */
    @PostMapping("/plan")
    public ResponseEntity<?> planTrip(
            @Valid @RequestBody TripPlanRequest request,
            @RequestHeader(value = "X-User-Id", required = false) String userIdHeader) {

        Long userId = resolveUserId(userIdHeader);
        log.info("Trip planning request for user={} destination={}", userId, request.getDestination());

        try {
            Trip trip = tripService.planTrip(request, userId);
            TripResponse response = TripResponse.fromEntity(trip);
            log.info("Trip {} created for user {}", trip.getId(), userId);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (RuntimeException e) {
            // Surface the real reason to the caller (frontend + logs)
            String msg = e.getMessage() != null ? e.getMessage() : "Unknown error";
            log.error("Runtime error planning trip: {}", msg, e);
            java.util.Map<String, String> err = new java.util.HashMap<>();
            err.put("error", msg);
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(err);

        } catch (Exception e) {
            String msg = e.getMessage() != null ? e.getMessage() : "Internal error";
            log.error("Error planning trip: {}", msg, e);
            java.util.Map<String, String> err = new java.util.HashMap<>();
            err.put("error", msg);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(err);
        }
    }

    /**
     * GET /api/trips - Get all trips for the requesting user only.
     */
    @GetMapping
    public ResponseEntity<List<TripResponse>> getUserTrips(
            @RequestHeader(value = "X-User-Id", required = false) String userIdHeader) {

        Long userId = resolveUserId(userIdHeader);
        log.info("Fetching trips for user={}", userId);

        try {
            List<Trip> trips = tripService.getUserTrips(userId);
            List<TripResponse> responses = trips.stream()
                    .map(TripResponse::fromEntity)
                    .collect(Collectors.toList());

            log.info("Found {} trips for user {}", responses.size(), userId);
            return ResponseEntity.ok(responses);

        } catch (Exception e) {
            log.error("Error fetching trips: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * GET /api/trips/{id} - Get a specific trip (only if it belongs to the
     * requesting user).
     */
    @GetMapping("/{id}")
    public ResponseEntity<TripResponse> getTripById(
            @PathVariable Long id,
            @RequestHeader(value = "X-User-Id", required = false) String userIdHeader) {

        Long userId = resolveUserId(userIdHeader);
        log.info("Fetching trip={} for user={}", id, userId);

        try {
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

    /**
     * DELETE /api/trips/{id} - Delete a trip (only if it belongs to the requesting
     * user).
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTrip(
            @PathVariable Long id,
            @RequestHeader(value = "X-User-Id", required = false) String userIdHeader) {

        Long userId = resolveUserId(userIdHeader);
        log.info("Deleting trip={} for user={}", id, userId);

        try {
            tripService.deleteTrip(id, userId);
            return ResponseEntity.noContent().build();

        } catch (RuntimeException e) {
            log.error("Error deleting trip: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        } catch (Exception e) {
            log.error("Error deleting trip: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
