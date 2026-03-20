"""
POI (Point of Interest) Database
Fetches POI data from external API or uses mock data as fallback
"""
import logging
from typing import List, Dict

from app.services.poi_api import get_service

logger = logging.getLogger(__name__)

# Mock POI database for fallback - INDIAN CITIES
POI_DATABASE = {
    "mumbai": [
        # Museums & Culture
        {"name": "Gateway of India", "type": "culture", "cost": 0, "duration": 1, "lat": 18.9220, "lon": 72.8347, "interests": ["culture", "history"]},
        {"name": "Chhatrapati Shivaji Maharaj Vastu Sangrahalaya", "type": "museum", "cost": 500, "duration": 2, "lat": 18.9269, "lon": 72.8326, "interests": ["museum", "culture", "history"]},
        {"name": "Elephanta Caves", "type": "history", "cost": 600, "duration": 4, "lat": 18.9633, "lon": 72.9315, "interests": ["history", "culture"]},
        
        # Food & Dining
        {"name": "Mohammed Ali Road Food Street", "type": "food", "cost": 500, "duration": 2, "lat": 18.9585, "lon": 72.8314, "interests": ["food"]},
        {"name": "Bandra Food Walk", "type": "food", "cost": 800, "duration": 3, "lat": 19.0596, "lon": 72.8295, "interests": ["food"]},
        
        # Shopping
        {"name": "Fashion Street", "type": "shopping", "cost": 1000, "duration": 2, "lat": 18.9469, "lon": 72.8286, "interests": ["shopping"]},
        {"name": "Colaba Causeway", "type": "shopping", "cost": 1500, "duration": 3, "lat": 18.9067, "lon": 72.8147, "interests": ["shopping"]},
        
        # Nature & Parks
        {"name": "Marine Drive", "type": "nature", "cost": 0, "duration": 2, "lat": 18.9432, "lon": 72.8236, "interests": ["nature"]},
        {"name": "Sanjay Gandhi National Park", "type": "nature", "cost": 50, "duration": 3, "lat": 19.2147, "lon": 72.9101, "interests": ["nature", "adventure"]},
        
        # Nightlife
        {"name": "Bandra-Worli Sea Link Cruise", "type": "nightlife", "cost": 1500, "duration": 2, "lat": 19.0368, "lon": 72.8197, "interests": ["nightlife", "adventure"]},
    ],
    
    "delhi": [
        # Monuments & Culture  
        {"name": "Red Fort", "type": "history", "cost": 80, "duration": 2, "lat": 28.6562, "lon": 77.2410, "interests": ["history", "culture"]},
        {"name": "Qutub Minar", "type": "history", "cost": 80, "duration": 2, "lat": 28.5244, "lon": 77.1855, "interests": ["history", "culture"]},
        {"name": "India Gate", "type": "culture", "cost": 0, "duration": 1, "lat": 28.6129, "lon": 77.2295, "interests": ["culture", "history"]},
        {"name": "Lotus Temple", "type": "culture", "cost": 0, "duration": 1, "lat": 28.5535, "lon": 77.2588, "interests": ["culture"]},
        
        # Museums
        {"name": "National Museum", "type": "museum", "cost": 50, "duration": 2, "lat": 28.6117, "lon": 77.2192, "interests": ["museum", "history"]},
        
        # Food
        {"name": "Chandni Chowk Street Food", "type": "food", "cost": 400, "duration": 3, "lat": 28.6506, "lon": 77.2303, "interests": ["food"]},
        {"name": "Connaught Place Dining", "type": "food", "cost": 1200, "duration": 2, "lat": 28.6315, "lon": 77.2167, "interests": ["food"]},
        
        # Shopping
        {"name": "Sarojini Nagar Market", "type": "shopping", "cost": 800, "duration": 2, "lat": 28.5742, "lon": 77.2033, "interests": ["shopping"]},
        
        # Nature
        {"name": "Lodhi Garden", "type": "nature", "cost": 0, "duration": 1, "lat": 28.5933, "lon": 77.2181, "interests": ["nature"]},
    ],
    
    "goa": [
        # Beaches & Nature
        {"name": "Baga Beach", "type": "nature", "cost": 0, "duration": 3, "lat": 15.5557, "lon": 73.7519, "interests": ["nature", "adventure"]},
        {"name": "Anjuna Beach", "type": "nature", "cost": 0, "duration": 2, "lat": 15.5734, "lon": 73.7408, "interests": ["nature", "adventure"]},
        {"name": "Palolem Beach", "type": "nature", "cost": 0, "duration": 3, "lat": 15.0100, "lon": 74.0233, "interests": ["nature"]},
        
        # Culture & History
        {"name": "Basilica of Bom Jesus", "type": "history", "cost": 50, "duration": 1, "lat": 15.5008, "lon": 73.9114, "interests": ["history", "culture"]},
        {"name": "Fort Aguada", "type": "history", "cost": 50, "duration": 2, "lat": 15.4909, "lon": 73.7733, "interests": ["history"]},
        
        # Food
        {"name": "Beach Shacks Food Tour", "type": "food", "cost": 1000, "duration": 2, "lat": 15.5586, "lon": 73.7479, "interests": ["food"]},
        
        # Adventure
        {"name": "Water Sports", "type": "adventure", "cost": 2000, "duration": 2, "lat": 15.5537, "lon": 73.7516, "interests": ["adventure"]},
        
        # Nightlife
        {"name": "Tito's Lane", "type": "nightlife", "cost": 1500, "duration": 3, "lat": 15.5559, "lon": 73.7516, "interests": ["nightlife"]},
    ],
    
    "jaipur": [
        # Palaces & Forts
        {"name": "Hawa Mahal", "type": "history", "cost": 200, "duration": 1, "lat": 26.9239, "lon": 75.8267, "interests": ["history", "culture"]},
        {"name": "Amber Fort", "type": "history", "cost": 500, "duration": 3, "lat": 26.9855, "lon": 75.8513, "interests": ["history", "culture", "adventure"]},
        {"name": "City Palace", "type": "culture", "cost": 400, "duration": 2, "lat": 26.9255, "lon": 75.8237, "interests": ["culture", "history"]},
        
        # Shopping
        {"name": "Johari Bazaar", "type": "shopping", "cost": 1000, "duration": 2, "lat": 26.9244, "lon": 75.8266, "interests": ["shopping"]},
        
        # Food
        {"name": "MI Road Food Street", "type": "food", "cost": 600, "duration": 2, "lat": 26.9124, "lon": 75.7873, "interests": ["food"]},
    ],
    
    # Generic fallback for unknown destinations
    "default": [
        {"name": "City Museum",          "type": "museum",    "cost": 300,  "duration": 2, "lat": 0.0, "lon": 0.0, "interests": ["museum", "culture"],   "osm_id": "mock_museum_1"},
        {"name": "Historical Monument",  "type": "culture",   "cost": 200,  "duration": 1, "lat": 0.0, "lon": 0.0, "interests": ["culture", "history"],   "osm_id": "mock_culture_1"},
        {"name": "Local Restaurant",     "type": "food",      "cost": 600,  "duration": 2, "lat": 0.0, "lon": 0.0, "interests": ["food"],                 "osm_id": "mock_food_1"},
        {"name": "Shopping District",    "type": "shopping",  "cost": 800,  "duration": 2, "lat": 0.0, "lon": 0.0, "interests": ["shopping"],             "osm_id": "mock_shopping_1"},
        {"name": "City Park",            "type": "nature",    "cost": 0,    "duration": 1, "lat": 0.0, "lon": 0.0, "interests": ["nature"],               "osm_id": "mock_nature_1"},
        {"name": "Evening Entertainment","type": "nightlife", "cost": 1000, "duration": 3, "lat": 0.0, "lon": 0.0, "interests": ["nightlife"],            "osm_id": "mock_night_1"},
    ],

    # Ranchi fallback (used when Overpass API is down / timing out)
    "ranchi": [
        {"name": "Morabadi Museum",        "type": "museum",    "cost": 100,  "duration": 2, "lat": 23.3694, "lon": 85.3213, "interests": ["museum", "culture"],           "osm_id": "mock_rch_1"},
        {"name": "Jagannath Temple",       "type": "culture",   "cost": 0,    "duration": 1, "lat": 23.3441, "lon": 85.3096, "interests": ["culture", "history"],          "osm_id": "mock_rch_2"},
        {"name": "Tagore Hill",            "type": "nature",    "cost": 50,   "duration": 2, "lat": 23.3551, "lon": 85.3044, "interests": ["nature", "adventure"],         "osm_id": "mock_rch_3"},
        {"name": "Rock Garden",            "type": "nature",    "cost": 50,   "duration": 2, "lat": 23.3831, "lon": 85.3329, "interests": ["nature", "adventure"],         "osm_id": "mock_rch_4"},
        {"name": "Birsa Zoological Park",  "type": "nature",    "cost": 80,   "duration": 3, "lat": 23.3193, "lon": 85.2817, "interests": ["nature"],                      "osm_id": "mock_rch_5"},
        {"name": "Hundru Falls",           "type": "adventure", "cost": 50,   "duration": 4, "lat": 23.4503, "lon": 85.6003, "interests": ["nature", "adventure"],         "osm_id": "mock_rch_6"},
        {"name": "Dassam Falls",           "type": "adventure", "cost": 50,   "duration": 4, "lat": 23.2540, "lon": 85.6140, "interests": ["nature", "adventure"],         "osm_id": "mock_rch_7"},
        {"name": "Jonha Falls",            "type": "nature",    "cost": 30,   "duration": 3, "lat": 23.3145, "lon": 85.5773, "interests": ["nature", "adventure"],         "osm_id": "mock_rch_8"},
        {"name": "Ranchi Lake",            "type": "nature",    "cost": 0,    "duration": 2, "lat": 23.3448, "lon": 85.3094, "interests": ["nature"],                      "osm_id": "mock_rch_9"},
        {"name": "Rajrappa Temple",        "type": "culture",   "cost": 0,    "duration": 3, "lat": 23.6460, "lon": 85.7358, "interests": ["culture", "history"],          "osm_id": "mock_rch_10"},
        {"name": "Pahari Mandir",          "type": "culture",   "cost": 0,    "duration": 1, "lat": 23.3644, "lon": 85.3406, "interests": ["culture", "history"],          "osm_id": "mock_rch_11"},
        {"name": "Ranchi Science Centre",  "type": "museum",    "cost": 100,  "duration": 2, "lat": 23.3723, "lon": 85.3813, "interests": ["museum", "culture"],           "osm_id": "mock_rch_12"},
        {"name": "Kanke Dam",              "type": "nature",    "cost": 0,    "duration": 2, "lat": 23.4175, "lon": 85.3183, "interests": ["nature"],                      "osm_id": "mock_rch_13"},
        {"name": "Upper Bazar Market",     "type": "shopping",  "cost": 500,  "duration": 2, "lat": 23.3492, "lon": 85.3241, "interests": ["shopping"],                    "osm_id": "mock_rch_14"},
        {"name": "Dhurwa Dam",             "type": "nature",    "cost": 0,    "duration": 2, "lat": 23.2985, "lon": 85.3090, "interests": ["nature"],                      "osm_id": "mock_rch_15"},
        {"name": "ISKCON Ranchi",          "type": "culture",   "cost": 0,    "duration": 1, "lat": 23.3850, "lon": 85.3341, "interests": ["culture", "history"],          "osm_id": "mock_rch_16"},
        {"name": "Ratu Palace",            "type": "history",   "cost": 100,  "duration": 2, "lat": 23.4456, "lon": 85.2623, "interests": ["history", "culture"],          "osm_id": "mock_rch_17"},
        {"name": "Hatia Lake",             "type": "nature",    "cost": 0,    "duration": 1, "lat": 23.3090, "lon": 85.2754, "interests": ["nature"],                      "osm_id": "mock_rch_18"},
        {"name": "Lalpur Night Market",    "type": "nightlife", "cost": 400,  "duration": 2, "lat": 23.3479, "lon": 85.3393, "interests": ["nightlife", "food"],           "osm_id": "mock_rch_19"},
        {"name": "Main Road Food Street",  "type": "food",      "cost": 600,  "duration": 2, "lat": 23.3536, "lon": 85.3147, "interests": ["food"],                        "osm_id": "mock_rch_20"},
    ],
}



def get_pois_for_destination(destination: str, interests: List[str], use_api: bool = True) -> List[Dict]:
    """
    Get POIs for a destination filtered by user interests
    
    Uses Fetch-and-Cache strategy:
    1. Check database cache (7 days fresh)
    2. If cache miss or stale, fetch from OSM API
    3. Save to cache for future requests
    4. Fall back to mock data if everything fails
    
    Args:
        destination: Destination city (case-insensitive)
        interests: List of user interests
        use_api: Whether to try fetching from external sources (default: True)
    
    Returns:
        List of POI dictionaries matching user interests
    """
    logger.info(f"Fetching POIs for {destination} with use_api={use_api}, interests={interests}")
    
    # Try OSM API with caching
    if use_api:
        osm_pois = _get_pois_from_osm_with_cache(destination, interests)
        if osm_pois:
            logger.info(f"Using {len(osm_pois)} POIs from OSM/cache")
            return osm_pois
        logger.warning("OSM fetch failed, falling back to mock data")
    
    # Fallback to mock data
    return _get_pois_from_mock(destination, interests)


def _get_pois_from_osm_with_cache(destination: str, interests: List[str]) -> List[Dict]:
    """
    Fetch POIs using OpenStreetMap with database caching
    
    Strategy:
    - Check cache first (fast)
    - If cache miss or stale, fetch from API and cache
    """
    try:
        from app.database.poi_cache import get_cache_manager
        from app.services.osm_service import get_osm_service
        
        cache = get_cache_manager()
        osm = get_osm_service()
        
        # Step 1: Check cache
        if cache.is_cache_fresh(destination, max_age_hours=720):  # 30 days
            logger.info(f"Cache hit for {destination}")
            cached_pois = cache.get_cached_pois(destination, interests)
            if cached_pois:
                return cached_pois
        
        # Step 2: Cache miss - fetch from OSM API
        logger.info(f"Cache miss for {destination}, fetching from OSM")
        pois = osm.fetch_pois_for_city(destination, interests, radius_km=50, limit=250)
        
        if not pois:
            logger.warning(f"No POIs fetched from OSM for {destination}")
            return None
        
        # Step 3: Save to cache for next time
        saved_count = cache.save_pois(destination, pois)
        logger.info(f"Saved {saved_count} POIs to cache for {destination}")
        
        return pois
        
    except Exception as e:
        logger.error(f"Error in OSM fetch-and-cache: {e}", exc_info=True)
        
        # Try OSM without cache as last resort
        try:
            from app.services.osm_service import get_osm_service
            logger.warning("Database cache failed, trying OSM directly")
            osm = get_osm_service()
            pois = osm.fetch_pois_for_city(destination, interests, radius_km=20, limit=250)
            if pois:
                logger.info(f"Successfully fetched {len(pois)} POIs from OSM (no cache)")
                return pois
        except Exception as e2:
            logger.error(f"Direct OSM fetch also failed: {e2}")
        
        logger.warning("All OSM attempts failed, falling back to mock data")
        return None  # Will trigger mock fallback in get_pois_for_destination



def _get_pois_from_mock(destination: str, interests: List[str]) -> List[Dict]:
    """Get POIs from mock database"""
    # Normalize destination name (lowercase, strip whitespace)
    dest_key = destination.lower().strip()
    
    # Get POI list for this destination, or use default if not found
    pois = POI_DATABASE.get(dest_key, POI_DATABASE["default"])
    
    # Filter by user interests if provided
    if not interests:
        return pois
    
    # Return POIs that match at least one interest
    filtered_pois = [
        poi for poi in pois
        if any(interest in poi.get("interests", []) for interest in interests)
    ]
    
    # If no match, return all POIs for the destination
    return filtered_pois if filtered_pois else pois
