package com.traveller.demo.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Trip Entity - Represents a travel trip/itinerary
 * Maps to 'trips' table in MySQL database
 */
@Entity
@Table(name = "trips")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Trip {

    /**
     * Primary key - Auto-generated ID
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * User who owns this trip - Many trips belong to one user
     * FetchType.LAZY: Don't load user unless explicitly requested
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @JsonIgnore // Prevent circular reference
    private User user;

    /**
     * Destination city/country (e.g., "Paris, France")
     */
    @Column(nullable = false, length = 255)
    private String destination;

    /**
     * Trip title given by user (e.g., "Summer Vacation 2025")
     */
    @Column(length = 255)
    private String title;

    /**
     * Trip start date
     */
    @Column(name = "start_date", nullable = false)
    private LocalDate startDate;

    /**
     * Trip end date (must be >= start date)
     */
    @Column(name = "end_date", nullable = false)
    private LocalDate endDate;

    /**
     * Number of days for the trip (calculated from dates)
     */
    @Column(nullable = false)
    private Integer days;

    /**
     * User's budget limit for the trip (in USD)
     * precision=10, scale=2 allows values up to 99,999,999.99
     */
    @Column(name = "budget_limit", nullable = false, precision = 10, scale = 2)
    private BigDecimal budgetLimit;

    /**
     * Total estimated cost calculated by ML engine (in USD)
     */
    @Column(name = "total_estimated_cost", precision = 10, scale = 2)
    private BigDecimal totalEstimatedCost;

    /**
     * Is the trip feasible within budget?
     * True = green signal (within budget)
     * False = red signal (over budget)
     */
    @Column(name = "is_feasible", nullable = false)
    private Boolean isFeasible = true;

    /**
     * Itinerary items for this trip - One trip has many itinerary items
     * Cascade: When trip is deleted, all itinerary items are deleted
     * orphanRemoval: If an itinerary item is removed from list, delete it from DB
     * OrderBy: Automatically sort by day number, then order within day
     */
    @OneToMany(mappedBy = "trip", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @OrderBy("dayNumber ASC, orderIndex ASC")
    private List<ItineraryItem> itineraryItems = new ArrayList<>();

    /**
     * Timestamp when trip was created - Auto-populated
     */
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Timestamp when trip was last updated - Auto-updated
     */
    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    /**
     * Helper method to add itinerary item to trip
     * Maintains bi-directional relationship
     */
    public void addItineraryItem(ItineraryItem item) {
        itineraryItems.add(item);
        item.setTrip(this);
    }

    /**
     * Helper method to remove itinerary item from trip
     * Maintains bi-directional relationship
     */
    public void removeItineraryItem(ItineraryItem item) {
        itineraryItems.remove(item);
        item.setTrip(null);
    }
}
