"""
Database connection and POI cache manager
Implements the fetch-and-cache strategy
"""
import mysql.connector
from mysql.connector import Error
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Dhiraj@11'),
    'database': os.getenv('DB_NAME', 'travelpro_db')
}


class POICacheManager:
    """Manages POI caching in MySQL database"""
    
    def __init__(self):
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                logger.info("Connected to MySQL database")
        except Error as e:
            logger.error(f"Database connection error: {e}")
            self.connection = None
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        if not self.connection or not self.connection.is_connected():
            logger.warning("Database connection lost, reconnecting...")
            self._connect()
    
    def is_cache_fresh(self, city: str, max_age_hours: int = 168) -> bool:
        """
        Check if cache for a city is fresh (< max_age_hours old)
        
        Args:
            city: City name
            max_age_hours: Maximum age in hours (default: 7 days)
            
        Returns:
            True if cache exists and is fresh
        """
        if not self.connection:
            return False
        
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
                SELECT COUNT(*), MAX(cached_at)
                FROM poi_cache
                WHERE city = %s
            """
            
            cursor.execute(query, (city.lower(),))
            count, latest_cached = cursor.fetchone()
            cursor.close()
            
            if count == 0:
                logger.info(f"No cache found for {city}")
                return False
            
            # Check if cache is fresh
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            is_fresh = latest_cached > cutoff_time
            
            logger.info(f"Cache for {city}: {count} POIs, latest: {latest_cached}, fresh: {is_fresh}")
            return is_fresh
            
        except Error as e:
            logger.error(f"Error checking cache freshness: {e}")
            return False
    
    def get_cached_pois(self, city: str, interests: Optional[List[str]] = None) -> List[Dict]:
        """
        Get cached POIs for a city
        
        Args:
            city: City name
            interests: Optional list of interests to filter by
            
        Returns:
            List of POI dictionaries
        """
        if not self.connection:
            logger.warning("No database connection, cannot fetch cache")
            return []
        
        try:
            self._ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            # Build query
            if interests:
                placeholders = ', '.join(['%s'] * len(interests))
                query = f"""
                    SELECT id, city, name, latitude, longitude, category, type,
                           rating, cost_rupees, address, description, osm_id
                    FROM poi_cache
                    WHERE city = %s AND category IN ({placeholders})
                    ORDER BY rating DESC, cost_rupees ASC
                """
                params = [city.lower()] + interests
            else:
                query = """
                    SELECT id, city, name, latitude, longitude, category, type,
                           rating, cost_rupees, address, description, osm_id
                    FROM poi_cache
                    WHERE city = %s
                    ORDER BY rating DESC, cost_rupees ASC
                """
                params = [city.lower()]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            
            # Convert to POI format
            pois = []
            for row in rows:
                poi = {
                    'name': row['name'],
                    'type': row['category'],
                    'cost': row['cost_rupees'],
                    'duration': 2,  # Default 2 hours
                    'lat': float(row['latitude']),
                    'lon': float(row['longitude']),
                    'interests': [row['category']],
                    'osm_id': row['osm_id']
                }
                pois.append(poi)
            
            logger.info(f"Retrieved {len(pois)} cached POIs for {city}")
            return pois
            
        except Error as e:
            logger.error(f"Error fetching cached POIs: {e}")
            return []
    
    def save_pois(self, city: str, pois: List[Dict]) -> int:
        """
        Save POIs to cache
        
        Args:
            city: City name
            pois: List of POI dictionaries
            
        Returns:
            Number of POIs saved
        """
        if not self.connection or not pois:
            return 0
        
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO poi_cache 
                (city, name, latitude, longitude, category, type, 
                 rating, cost_rupees, address, description, osm_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    latitude = VALUES(latitude),
                    longitude = VALUES(longitude),
                    category = VALUES(category),
                    rating = VALUES(rating),
                    cost_rupees = VALUES(cost_rupees),
                    updated_at = CURRENT_TIMESTAMP
            """
            
            saved_count = 0
            for poi in pois:
                try:
                    values = (
                        city.lower(),
                        poi.get('name', 'Unknown'),
                        poi.get('lat', 0.0),
                        poi.get('lon', 0.0),
                        poi.get('type', 'culture'),
                        poi.get('osm_type', 'attraction'),
                        poi.get('rating'),
                        poi.get('cost', 0),
                        poi.get('address', ''),
                        poi.get('description', ''),
                        poi.get('osm_id', f"poi_{saved_count}")
                    )
                    
                    cursor.execute(query, values)
                    saved_count += 1
                    
                except Error as e:
                    logger.warning(f"Error saving POI {poi.get('name')}: {e}")
                    continue
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Saved {saved_count}/{len(pois)} POIs for {city}")
            return saved_count
            
        except Error as e:
            logger.error(f"Error saving POIs to cache: {e}")
            if self.connection:
                self.connection.rollback()
            return 0
    
    def clear_city_cache(self, city: str) -> bool:
        """
        Clear cache for a specific city
        
        Args:
            city: City name
            
        Returns:
            True if successful
        """
        if not self.connection:
            return False
        
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = "DELETE FROM poi_cache WHERE city = %s"
            cursor.execute(query, (city.lower(),))
            self.connection.commit()
            
            deleted_count = cursor.rowcount
            cursor.close()
            
            logger.info(f"Cleared {deleted_count} POIs from cache for {city}")
            return True
            
        except Error as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.connection:
            return {}
        
        try:
            self._ensure_connection()
            cursor = self.connection.cursor()
            
            query = """
                SELECT city, COUNT(*) as count, MAX(cached_at) as latest
                FROM poi_cache
                GROUP BY city
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            
            stats = {}
            for row in rows:
                stats[row[0]] = {
                    'count': row[1],
                    'latest': row[2]
                }
            
            return stats
            
        except Error as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")


# Singleton instance
_cache_manager = None

def get_cache_manager() -> POICacheManager:
    """Get singleton cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = POICacheManager()
    return _cache_manager
