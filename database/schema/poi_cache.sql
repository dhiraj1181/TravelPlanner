-- POI Cache Table for storing fetched Points of Interest
-- This implements the "Fetch & Cache" strategy to minimize API calls

CREATE TABLE IF NOT EXISTS poi_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    
    -- Location Information
    city VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    
    -- Classification
    category VARCHAR(50),           -- museum, food, culture, etc.
    type VARCHAR(50),                -- specific OSM type
    osm_id VARCHAR(50),              -- OpenStreetMap ID for uniqueness
    
    -- Details
    rating DECIMAL(3, 2),            -- 0.00 to 5.00
    cost_rupees INT DEFAULT 0,       -- Estimated cost in Indian Rupees
    address TEXT,
    description TEXT,
    
    -- Metadata
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_city (city),
    INDEX idx_category (category),
    INDEX idx_cached_at (cached_at),
    
    -- Prevent duplicate POIs
    UNIQUE KEY unique_poi (city, osm_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create index for faster cache lookups
CREATE INDEX idx_city_category ON poi_cache(city, category);
CREATE INDEX idx_city_cached_at ON poi_cache(city, cached_at);
