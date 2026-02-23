package com.traveller.demo.repository;

import com.traveller.demo.entity.Trip;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * TripRepository - Data access layer for Trip entity
 * Extends JpaRepository for CRUD operations
 */
@Repository
public interface TripRepository extends JpaRepository<Trip, Long> {

    /**
     * Find all trips for a specific user, ordered by creation date (newest first)
     * 
     * @param userId - User's ID
     * @return List of trips
     */
    List<Trip> findByUserIdOrderByCreatedAtDesc(Long userId);

    /**
     * Find all trips for a specific user
     * 
     * @param userId - User's ID
     * @return List of trips
     */
    List<Trip> findByUserId(Long userId);
}
