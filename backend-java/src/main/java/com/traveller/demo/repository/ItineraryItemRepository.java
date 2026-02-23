package com.traveller.demo.repository;

import com.traveller.demo.entity.ItineraryItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * ItineraryItemRepository - Data access layer for ItineraryItem entity
 * Extends JpaRepository for CRUD operations
 */
@Repository
public interface ItineraryItemRepository extends JpaRepository<ItineraryItem, Long> {

    /**
     * Find all itinerary items for a specific trip
     * Automatically sorted by day number and order within day
     * 
     * @param tripId - Trip's ID
     * @return List of itinerary items
     */
    List<ItineraryItem> findByTripIdOrderByDayNumberAscOrderIndexAsc(Long tripId);
}
