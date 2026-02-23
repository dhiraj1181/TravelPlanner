package com.traveller.demo.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * User Entity - Represents a user in the system
 * Maps to 'users' table in MySQL database
 */
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {

    /**
     * Primary key - Auto-generated ID
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * User's email - Must be unique and not null
     */
    @Column(nullable = false, unique = true, length = 255)
    private String email;

    /**
     * User's password - BCrypt hashed, never expose in API responses
     */
    @Column(nullable = false, length = 255)
    @JsonIgnore // Never include password in JSON responses
    private String password;

    /**
     * User's full name
     */
    @Column(nullable = false, length = 255)
    private String name;

    /**
     * User's trips - One user can have many trips
     * Cascade: When user is deleted, all their trips are deleted
     * FetchType.LAZY: Don't load trips unless explicitly requested
     */
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @JsonIgnore // Prevent circular reference in JSON
    private List<Trip> trips = new ArrayList<>();

    /**
     * Timestamp when user was created - Auto-populated
     */
    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Timestamp when user was last updated - Auto-updated
     */
    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    /**
     * Constructor for creating new user (without ID)
     */
    public User(String email, String password, String name) {
        this.email = email;
        this.password = password;
        this.name = name;
    }
}
