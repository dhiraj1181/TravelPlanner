package com.traveller.demo.controller;

import com.traveller.demo.entity.User;
import com.traveller.demo.repository.UserRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * AuthController - Simple authentication endpoints for frontend
 * NOTE: This is a simplified version without real JWT authentication
 * For production, implement proper JWT token generation and validation
 */
@RestController
@RequestMapping("/api/auth")
@Slf4j
public class AuthController {

    private final UserRepository userRepository;

    public AuthController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    /**
     * POST /api/auth/login - Simple login endpoint
     * Returns mock token and user data ONLY for existing users with correct
     * password
     */
    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody Map<String, String> credentials) {
        String email = credentials.get("email");
        String password = credentials.get("password");
        log.info("Login attempt for email: {}", email);

        try {
            // Find user - return error if not found
            User user = userRepository.findByEmail(email)
                    .orElseThrow(() -> new RuntimeException("Invalid email or password"));

            // Validate password
            // NOTE: Passwords are currently stored as plain text (NOT recommended for
            // production)
            // In production, use BCrypt or similar: passwordEncoder.matches(password,
            // user.getPassword())
            if (password == null || !password.equals(user.getPassword())) {
                log.warn("Invalid password attempt for email: {}", email);
                throw new RuntimeException("Invalid email or password");
            }

            // Create response with mock token
            Map<String, Object> response = new HashMap<>();
            response.put("token", "mock-jwt-token-" + System.currentTimeMillis());

            Map<String, Object> userData = new HashMap<>();
            userData.put("id", user.getId());
            userData.put("name", user.getName());
            userData.put("email", user.getEmail());
            response.put("user", userData);

            log.info("Login successful for user ID: {}", user.getId());
            return ResponseEntity.ok(response);

        } catch (RuntimeException e) {
            log.warn("Login failed: {}", e.getMessage());
            Map<String, Object> error = new HashMap<>();
            error.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
        } catch (Exception e) {
            log.error("Login error: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * POST /api/auth/register - Simple registration endpoint
     */
    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody Map<String, String> userData) {
        String email = userData.get("email");
        String password = userData.get("password");
        String name = userData.get("name");
        log.info("Registration attempt for email: {}", email);

        try {
            // Check if user already exists
            if (userRepository.findByEmail(email).isPresent()) {
                log.warn("User already exists: {}", email);
                return ResponseEntity.status(HttpStatus.CONFLICT).build();
            }

            // Create new user
            User newUser = new User();
            newUser.setEmail(email);
            newUser.setName(name);
            // NOTE: Storing plain text password (NOT recommended for production)
            // In production, use BCrypt: passwordEncoder.encode(password)
            newUser.setPassword(password); // Save actual password
            User savedUser = userRepository.save(newUser);

            // Create response
            Map<String, Object> response = new HashMap<>();
            response.put("token", "mock-jwt-token-" + System.currentTimeMillis());

            Map<String, Object> userDataResponse = new HashMap<>();
            userDataResponse.put("id", savedUser.getId());
            userDataResponse.put("name", savedUser.getName());
            userDataResponse.put("email", savedUser.getEmail());
            response.put("user", userDataResponse);

            log.info("Registration successful for user ID: {}", savedUser.getId());
            return ResponseEntity.status(HttpStatus.CREATED).body(response);

        } catch (Exception e) {
            log.error("Registration error: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    /**
     * POST /api/auth/logout - Logout endpoint
     * Just returns 200 OK, client handles clearing localStorage
     */
    @PostMapping("/logout")
    public ResponseEntity<Void> logout() {
        log.info("Logout request received");
        return ResponseEntity.ok().build();
    }
}
