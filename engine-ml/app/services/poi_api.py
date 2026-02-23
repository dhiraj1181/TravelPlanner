"""
OpenTripMap API Integration Service
Fetches real POI data from OpenTripMap API
"""
import httpx
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# OpenTripMap API configuration
OPENTRIPMAP_BASE_URL = "https://api.opentripmap.com/0.1/en/places"
DEFAULT_RADIUS = 5000  # 5km radius
REQUEST_TIMEOUT = 10  # seconds

# API Key - set via environment variable: OPENTRIPMAP_API_KEY
# Get free API key from: https://opentripmap.io/product
import os
OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY", "")

# Map user interests to OpenTripMap categories
INTEREST_TO_CATEGORY = {
    "museum": "museums",
    "food": "foods,restaurants",
    "culture": "cultural,religion,churches",
    "history": "historic,fortifications,archaeological_sites",
    "nature": "natural,natural_waterfalls,natural_springs,natural_peaks,natural_caves,beaches",
    "shopping": "shops",
    "adventure": "sport,amusements,natural_peaks,natural_caves",
    "nightlife": "entertainment"
}


class OpenTripMapService:
    """Service for fetching POI data from OpenTripMap API"""
    
    def __init__(self):
        self.client = httpx.Client(timeout=REQUEST_TIMEOUT)
        self.cache = {}  # Simple in-memory cache
    
    def geocode_destination(self, destination: str) -> Optional[Dict]:
        """
        Convert destination name to coordinates
        
        Args:
            destination: City name (e.g., "Paris")
            
        Returns:
            Dict with lat, lon, or None if not found or API key missing
        """
        if not OPENTRIPMAP_API_KEY:
            logger.warning("OpenTripMap API key not configured. Set OPENTRIPMAP_API_KEY environment variable.")
            return None
            
        try:
            url = f"{OPENTRIPMAP_BASE_URL}/geoname"
            params = {
                "name": destination,
                "apikey": OPENTRIPMAP_API_KEY
            }
            
            logger.info(f"Geocoding destination: {destination}")
            response = self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data and "lat" in data and "lon" in data:
                logger.info(f"Geocoded {destination}: lat={data['lat']}, lon={data['lon']}")
                return {"lat": data["lat"], "lon": data["lon"]}
            
            logger.warning(f"No coordinates found for {destination}")
            return None
            
        except Exception as e:
            logger.error(f"Geocoding error for {destination}: {str(e)}")
            return None
    
    def fetch_pois_by_radius(self, lat: float, lon: float, 
                            interests: List[str], 
                            radius: int = DEFAULT_RADIUS,
                            limit: int = 50) -> List[Dict]:
        """
        Fetch POIs within radius from coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            interests: List of user interests
            radius: Search radius in meters
            limit: Maximum number of POIs to fetch
            
        Returns:
            List of POI dictionaries
        """
        if not OPENTRIPMAP_API_KEY:
            logger.warning("OpenTripMap API key not configured")
            return []
            
        try:
            # Map interests to API categories
            categories = self._map_interests_to_categories(interests)
            
            url = f"{OPENTRIPMAP_BASE_URL}/radius"
            params = {
                "radius": radius,
                "lon": lon,
                "lat": lat,
                "kinds": categories,
                "limit": limit,
                "format": "json",
                "apikey": OPENTRIPMAP_API_KEY
            }
            
            logger.info(f"Fetching POIs: lat={lat}, lon={lon}, radius={radius}, categories={categories}")
            response = self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pois = data if isinstance(data, list) else []
            
            logger.info(f"Fetched {len(pois)} POIs from OpenTripMap")
            return pois
            
        except Exception as e:
            logger.error(f"Error fetching POIs: {str(e)}")
            return []
    
    def _map_interests_to_categories(self, interests: List[str]) -> str:
        """Map user interests to OpenTripMap category strings"""
        categories = set()
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in INTEREST_TO_CATEGORY:
                # Split comma-separated categories
                cats = INTEREST_TO_CATEGORY[interest_lower].split(',')
                categories.update(cats)
        
        # If no categories mapped, use general interesting places
        if not categories:
            categories = {"interesting_places"}
        
        return ",".join(categories)
    
    def normalize_poi_data(self, api_poi: Dict, interest_type: str = "culture") -> Dict:
        """
        Convert OpenTripMap POI format to internal format
        
        Args:
            api_poi: Raw POI data from API
            interest_type: Primary interest type for this POI
            
        Returns:
            Normalized POI dict with name, type, cost, duration, lat, lon, interests
        """
        # Extract coordinates
        point = api_poi.get("point", {})
        lat = point.get("lat", 0.0)
        lon = point.get("lon", 0.0)
        
        # Extract name
        name = api_poi.get("name", "Unknown POI")
        
        # Determine type from kinds
        kinds = api_poi.get("kinds", "").split(",")
        poi_type = self._determine_poi_type(kinds)
        
        # Estimate cost and duration based on type
        cost, duration = self._estimate_cost_duration(poi_type)
        
        # Map interests
        interests = self._map_kinds_to_interests(kinds)
        if not interests:
            interests = [interest_type]
        
        return {
            "name": name,
            "type": poi_type,
            "cost": cost,
            "duration": duration,
            "lat": lat,
            "lon": lon,
            "interests": interests
        }
    
    def _determine_poi_type(self, kinds: List[str]) -> str:
        """Determine POI type from kinds"""
        kinds_lower = [k.lower() for k in kinds]
        
        if any(k in kinds_lower for k in ["museums", "museum"]):
            return "museum"
        elif any(k in kinds_lower for k in ["restaurants", "foods", "food"]):
            return "food"
        elif any(k in kinds_lower for k in ["historic", "archaeology"]):
            return "history"
        elif any(k in kinds_lower for k in ["natural", "nature_reserves", "parks", "falls"]):
            return "nature"
        elif any(k in kinds_lower for k in ["shops", "shopping"]):
            return "shopping"
        elif any(k in kinds_lower for k in ["sport", "amusements"]):
            return "adventure"
        elif any(k in kinds_lower for k in ["entertainment", "theatres_and_entertainments"]):
            return "nightlife"
        elif any(k in kinds_lower for k in ["cultural", "religion"]):
            return "culture"
        else:
            return "culture"  # Default
    
    def _map_kinds_to_interests(self, kinds: List[str]) -> List[str]:
        """Map API kinds to user interests"""
        interests = set()
        kinds_lower = [k.lower() for k in kinds]
        
        # Reverse mapping
        for interest, categories in INTEREST_TO_CATEGORY.items():
            cats = [c.strip().lower() for c in categories.split(',')]
            if any(cat in kinds_lower for cat in cats):
                interests.add(interest)
        
        return list(interests)
    
    def _estimate_cost_duration(self, poi_type: str) -> tuple:
        """
        Estimate cost and duration for POI type
        
        Returns:
            (cost in USD, duration in hours)
        """
        estimates = {
            "museum": (15, 2),
            "food": (35, 2),
            "history": (12, 1),
            "culture": (10, 1),
            "nature": (0, 1),
            "shopping": (50, 2),
            "adventure": (30, 2),
            "nightlife": (60, 3)
        }
        
        return estimates.get(poi_type, (20, 2))  # Default
    
    def close(self):
        """Close HTTP client"""
        self.client.close()


# Global service instance
_service = None

def get_service() -> OpenTripMapService:
    """Get or create global service instance"""
    global _service
    if _service is None:
        _service = OpenTripMapService()
    return _service
