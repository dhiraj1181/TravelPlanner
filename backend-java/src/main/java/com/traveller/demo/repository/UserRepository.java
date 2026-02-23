package com.traveller.demo.repository;

import com.traveller.demo.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * UserRepository - Data access layer for User entity
 * Extends JpaRepository for CRUD operations
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    /**
     * Find user by email address
     * 
     * @param email - User's email
     * @return Optional containing user if found, empty otherwise
     */
    Optional<User> findByEmail(String email);

    /**
     * Check if user exists with given email
     * 
     * @param email - Email to check
     * @return true if user exists, false otherwise
     */
    boolean existsByEmail(String email);
}
