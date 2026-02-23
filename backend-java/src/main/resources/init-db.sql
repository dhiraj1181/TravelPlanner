-- Database: travelpro_db
-- Initialize with test user for development

USE travelpro_db;

-- Insert test user (password is BCrypt hash of "password123")
-- You can generate new hashes at https://bcrypt-generator.com/
INSERT INTO users (email, password, name, created_at, updated_at) 
VALUES (
    'test@example.com', 
    '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',  -- password123
    'Test User',
    NOW(),
    NOW()
) ON DUPLICATE KEY UPDATE email=email;

-- Verify user was created
SELECT * FROM users;
