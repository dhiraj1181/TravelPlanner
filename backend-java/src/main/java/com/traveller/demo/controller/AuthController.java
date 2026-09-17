package com.traveller.demo.controller;

import com.traveller.demo.entity.User;
import com.traveller.demo.repository.UserRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * AuthController - Simplified auth with per-process session invalidation.
 *
 * Token format:  tp-{SERVER_INSTANCE_ID}-{userId}-{timestamp}
 *
 * SERVER_INSTANCE_ID is a random UUID generated once per JVM startup.
 * Every restart produces a new ID, so /validate rejects all old tokens
 * and the frontend clears localStorage → forces re-login automatically.
 */
@RestController
@RequestMapping("/api/auth")
@Slf4j
public class AuthController {

    /**
     * Random UUID regenerated each time the JVM starts.
     * Old tokens that carry a different ID are rejected by /validate.
     */
    private static final String SERVER_INSTANCE_ID = UUID.randomUUID().toString();

    static {
        log.info("=== Server instance ID: {} ===", SERVER_INSTANCE_ID);
    }

    // ── Build / parse token ──────────────────────────────────────────────────

    private String buildToken(long userId) {
        return "tp-" + SERVER_INSTANCE_ID + "-" + userId + "-" + System.currentTimeMillis();
    }

    /** Returns the userId embedded in the token, or -1 if the token is invalid
     *  (wrong format or belongs to a different server instance). */
    private long parseUserId(String token) {
        if (token == null) return -1;
        // Format: tp-{instanceId}-{userId}-{timestamp}
        String prefix = "tp-" + SERVER_INSTANCE_ID + "-";
        if (!token.startsWith(prefix)) return -1;
        String rest = token.substring(prefix.length()); // "{userId}-{timestamp}"
        int dash = rest.lastIndexOf('-');
        if (dash < 0) return -1;
        try {
            return Long.parseLong(rest.substring(0, dash));
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    // ── Repository ───────────────────────────────────────────────────────────

    private final UserRepository userRepository;

    public AuthController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    // ── Endpoints ────────────────────────────────────────────────────────────

    /**
     * POST /api/auth/login
     */
    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody Map<String, String> credentials) {
        String email    = credentials.get("email");
        String password = credentials.get("password");
        log.info("Login attempt for email: {}", email);

        try {
            User user = userRepository.findByEmail(email)
                    .orElseThrow(() -> new RuntimeException("Invalid email or password"));

            if (password == null || !password.equals(user.getPassword())) {
                log.warn("Invalid password for email: {}", email);
                throw new RuntimeException("Invalid email or password");
            }

            Map<String, Object> response = new HashMap<>();
            response.put("token", buildToken(user.getId()));

            Map<String, Object> userData = new HashMap<>();
            userData.put("id",    user.getId());
            userData.put("name",  user.getName());
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
     * POST /api/auth/register
     */
    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> register(@RequestBody Map<String, String> userData) {
        String email    = userData.get("email");
        String password = userData.get("password");
        String name     = userData.get("name");
        log.info("Registration attempt for email: {}", email);

        try {
            if (userRepository.findByEmail(email).isPresent()) {
                log.warn("User already exists: {}", email);
                return ResponseEntity.status(HttpStatus.CONFLICT).build();
            }

            User newUser = new User();
            newUser.setEmail(email);
            newUser.setName(name);
            newUser.setPassword(password);
            User savedUser = userRepository.save(newUser);

            Map<String, Object> response = new HashMap<>();
            response.put("token", buildToken(savedUser.getId()));

            Map<String, Object> userDataResponse = new HashMap<>();
            userDataResponse.put("id",    savedUser.getId());
            userDataResponse.put("name",  savedUser.getName());
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
     * GET /api/auth/validate
     *
     * Called by the frontend on every page load.
     * Returns 200 {valid:true, userId:...} if the token belongs to THIS server
     * instance, or 401 {valid:false} if the backend was restarted (or the
     * token is absent / malformed).
     */
    @GetMapping("/validate")
    public ResponseEntity<Map<String, Object>> validate(
            @RequestHeader(value = "Authorization", required = false) String authHeader) {

        String token = null;
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            token = authHeader.substring(7);
        }

        long userId = parseUserId(token);
        Map<String, Object> body = new HashMap<>();

        if (userId < 0) {
            log.debug("Token validation failed – wrong instance or malformed token");
            body.put("valid", false);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(body);
        }

        body.put("valid",  true);
        body.put("userId", userId);
        log.debug("Token valid for userId={}", userId);
        return ResponseEntity.ok(body);
    }

    /**
     * POST /api/auth/logout
     */
    @PostMapping("/logout")
    public ResponseEntity<Void> logout() {
        log.info("Logout request received");
        return ResponseEntity.ok().build();
    }
}
