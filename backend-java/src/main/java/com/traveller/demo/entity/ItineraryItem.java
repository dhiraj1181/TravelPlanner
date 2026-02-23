package com.traveller.demo.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * ItineraryItem Entity - Represents a single point of interest (POI) in a trip
 * Maps to 'itinerary_items' table in MySQL database
 */
@Entity
@Table(name = "itinerary_items")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ItineraryItem {

    /**
     * Primary key - Auto-generated ID
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Trip this item belongs to - Many items belong to one trip
     * FetchType.LAZY: Don't load trip unless explicitly requested
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trip_id", nullable = false)
    @JsonIgnore // Prevent circular reference
    private Trip trip;

    /**
     * Day number in the trip (1-based index)
     * Day 1, Day 2, Day 3, etc.
     */
    @Column(name = "day_number", nullable = false)
    private Integer dayNumber;

    /**
     * Name of the place/attraction (e.g., "Eiffel Tower", "Louvre Museum")
     */
    @Column(name = "place_name", nullable = false, length = 255)
    private String placeName;

    /**
     * Type/category of the place (e.g., "museum", "food", "adventure")
     * Matches the interests from frontend
     */
    @Column(name = "place_type", length = 100)
    private String placeType;

    /**
     * Latitude coordinate of the place
     * precision=10, scale=8 allows -90.00000000 to 90.00000000
     */
    @Column(precision = 10, scale = 8)
    private BigDecimal lat;

    /**
     * Longitude coordinate of the place
     * precision=11, scale=8 allows -180.00000000 to 180.00000000
     */
    @Column(precision = 11, scale = 8)
    private BigDecimal lon;

    /**
     * Est imated cost to visit this place (in USD)
     */
    @Column(precision = 10, scale = 2)
    private BigDecimal cost;

    /**
     * Estimated duration to spend at this place (in hours)
     */
    @Column
    private Integer duration;

    /**
     * Order of this item within the day (0-based index)
     * Used for TSP routing - visit order
     */
    @Column(name = "order_index", nullable = false)
    private Integer orderIndex;

    /**
     * Timestamp when item was created - Auto-populated
     */
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Constructor for creating new itinerary item
     */
    public ItineraryItem(Trip trip, Integer dayNumber, String placeName, String placeType,
            BigDecimal lat, BigDecimal lon, BigDecimal cost, Integer duration, Integer orderIndex) {
        this.trip = trip;
        this.dayNumber = dayNumber;
        this.placeName = placeName;
        this.placeType = placeType;
        this.lat = lat;
        this.lon = lon;
        this.cost = cost;
        this.duration = duration;
        this.orderIndex = orderIndex;
    }
}
