"""
OpenStreetMap Service
Fetches POI data from Overpass API (OpenStreetMap)
Free, no API key required
"""
import requests
import logging
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Interest to OSM tags mapping
INTEREST_TAG_MAP = {
    "museum": ["tourism=museum", "tourism=gallery"],
    "food": ["amenity=restaurant", "amenity=cafe", "amenity=fast_food"],
    "culture": ["tourism=attraction", "tourism=monument", "historic=monument", "amenity=place_of_worship"],
    "nature": [
        "leisure=park", "leisure=garden", "natural=beach",
        "natural=waterfall", "waterway=waterfall",
        "natural=peak", "natural=cave_entrance",
        "natural=water", "leisure=nature_reserve",
        "natural=hot_spring", "natural=geyser"
    ],
    "shopping": ["shop=mall", "shop=department_store", "amenity=marketplace"],
    "adventure": [
        "tourism=viewpoint", "sport=climbing", "leisure=water_park",
        "natural=peak", "natural=cave_entrance", "waterway=rapids",
        "leisure=trail_riding_station"
    ],
    "history": ["historic=castle", "historic=memorial", "historic=archaeological_site", "historic=ruins"],
    "nightlife": ["amenity=bar", "amenity=nightclub", "amenity=pub"]
}

# Cost estimates in Indian Rupees
COST_ESTIMATES = {
    "museum": 300,
    "gallery": 200,
    "restaurant": 800,
    "cafe": 400,
    "monument": 100,
    "attraction": 150,
    "park": 0,
    "garden": 0,
    "beach": 0,
    "waterfall": 0,
    "peak": 0,
    "cave_entrance": 100,
    "nature_reserve": 50,
    "hot_spring": 200,
    "ruins": 100,
    "place_of_worship": 0,
    "mall": 1000,
    "marketplace": 500,
    "viewpoint": 0,
    "castle": 500,
    "bar": 600,
    "nightclub": 1000,
    "default": 200
}

# Offline city coordinates database (fallback when Nominatim is unavailable)
INDIAN_CITIES_COORDS = {
    "mumbai": {"lat": 19.0760, "lon": 72.8777},
    "delhi": {"lat": 28.7041, "lon": 77.1025},
    "bangalore": {"lat": 12.9716, "lon": 77.5946},
    "bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "chennai": {"lat": 13.0827, "lon": 80.2707},
    "kolkata": {"lat": 22.5726, "lon": 88.3639},
    "pune": {"lat": 18.5204, "lon": 73.8567},
    "ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "jaipur": {"lat": 26.9124, "lon": 75.7873},
    "surat": {"lat": 21.1702, "lon": 72.8311},
    "lucknow": {"lat": 26.8467, "lon": 80.9462},
    "kanpur": {"lat": 26.4499, "lon": 80.3319},
    "nagpur": {"lat": 21.1458, "lon": 79.0882},
    "indore": {"lat": 22.7196, "lon": 75.8577},
    "thane": {"lat": 19.2183, "lon": 72.9781},
    "bhopal": {"lat": 23.2599, "lon": 77.4126},
    "visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
    "pimpri-chinchwad": {"lat": 18.6298, "lon": 73.7997},
    "patna": {"lat": 25.5941, "lon": 85.1376},
    "vadodara": {"lat": 22.3072, "lon": 73.1812},
    "ghaziabad": {"lat": 28.6692, "lon": 77.4538},
    "ludhiana": {"lat": 30.9010, "lon": 75.8573},
    "agra": {"lat": 27.1767, "lon": 78.0081},
    "nashik": {"lat": 19.9975, "lon": 73.7898},
    "faridabad": {"lat": 28.4089, "lon": 77.3178},
    "meerut": {"lat": 28.9845, "lon": 77.7064},
    "rajkot": {"lat": 22.3039, "lon": 70.8022},
    "varanasi": {"lat": 25.3176, "lon": 82.9739},
    "srinagar": {"lat": 34.0837, "lon": 74.7973},
    "aurangabad": {"lat": 19.8762, "lon": 75.3433},
    "dhanbad": {"lat": 23.7957, "lon": 86.4304},
    "amritsar": {"lat": 31.6340, "lon": 74.8723},
    "navi mumbai": {"lat": 19.0330, "lon": 73.0297},
    "allahabad": {"lat": 25.4358, "lon": 81.8463},
    "prayagraj": {"lat": 25.4358, "lon": 81.8463},
    "ranchi": {"lat": 23.3441, "lon": 85.3096},
    "howrah": {"lat": 22.5958, "lon": 88.2636},
    "coimbatore": {"lat": 11.0168, "lon": 76.9558},
    "jabalpur": {"lat": 23.1815, "lon": 79.9864},
    "gwalior": {"lat": 26.2183, "lon": 78.1828},
    "vijayawada": {"lat": 16.5062, "lon": 80.6480},
    "jodhpur": {"lat": 26.2389, "lon": 73.0243},
    "madurai": {"lat": 9.9252, "lon": 78.1198},
    "raipur": {"lat": 21.2514, "lon": 81.6296},
    "kota": {"lat": 25.2138, "lon": 75.8648},
    "chandigarh": {"lat": 30.7333, "lon": 76.7794},
    "guwahati": {"lat": 26.1445, "lon": 91.7362},
    "solapur": {"lat": 17.6599, "lon": 75.9064},
    "goa": {"lat": 15.2993, "lon": 74.1240},
    "panaji": {"lat": 15.4909, "lon": 73.8278},
    "mysore": {"lat": 12.2958, "lon": 76.6394},
    "bareilly": {"lat": 28.3670, "lon": 79.4304},
    "thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366},
    "trivandrum": {"lat": 8.5241, "lon": 76.9366},
}



class OSMService:
    """Service for fetching POI data from OpenStreetMap"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TravelPro/1.0 (Travel Planning App)'
        })
    
    def geocode_city(self, city_name: str) -> Optional[Dict[str, float]]:
        """
        Get coordinates for a city using Nominatim or offline fallback
        
        Args:
            city_name: Name of the city
            
        Returns:
            Dictionary with 'lat' and 'lon' keys, or None if not found
        """
        # Try offline database first (faster and more reliable)
        city_lower = city_name.lower().strip()
        if city_lower in INDIAN_CITIES_COORDS:
            logger.info(f"Using offline coordinates for {city_name}")
            return INDIAN_CITIES_COORDS[city_lower]
        
        # Try Nominatim API as fallback
        try:
            params = {
                'q': f"{city_name}, India",
                'format': 'json',
                'limit': 1
            }
            
            logger.info(f"Geocoding city via Nominatim: {city_name}")
            response = self.session.get(NOMINATIM_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                result = data[0]
                coords = {
                    'lat': float(result['lat']),
                    'lon': float(result['lon'])
                }
                logger.info(f"Geocoded {city_name} via Nominatim to {coords}")
                return coords
            
            logger.warning(f"No Nominatim result for {city_name}")
            return None
            
        except Exception as e:
            logger.warning(f"Nominatim error for {city_name}: {e}, trying offline database")
            return None
    
    def fetch_pois_for_city(self, city_name: str, interests: List[str], 
                           radius_km: float = 50, limit: int = 100) -> List[Dict]:
        """
        Fetch POIs from OpenStreetMap Overpass API
        
        Args:
            city_name: Name of the city
            interests: List of user interests
            radius_km: Search radius in kilometers
            limit: Maximum number of POIs to fetch
            
        Returns:
            List of POI dictionaries
        """
        # First, get city coordinates
        coords = self.geocode_city(city_name)
        if not coords:
            logger.error(f"Could not geocode {city_name}")
            return []
        
        # Build Overpass query based on interests
        osm_tags = self._map_interests_to_tags(interests)
        if not osm_tags:
            logger.warning("No OSM tags for interests, using default")
            osm_tags = ["tourism=attraction"]
        
        query = self._build_overpass_query(
            coords['lat'], coords['lon'], 
            radius_km * 1000,  # Convert to meters
            osm_tags
        )
        
        try:
            logger.info(f"Fetching POIs for {city_name} from Overpass API")
            logger.debug(f"Query: {query[:200]}...")  # Log first 200 chars
            
            response = self.session.post(
                OVERPASS_URL, 
                data={'data': query},
                timeout=60  # Increased from 30 to 60 seconds
            )
            response.raise_for_status()
            
            data = response.json()
            pois = self._parse_overpass_response(data, city_name, interests)
            
            # Limit results
            pois = pois[:limit]
            
            logger.info(f"Fetched {len(pois)} POIs for {city_name}")
            return pois
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Overpass API timeout for {city_name}: {e}")
            return []
        except requests.exceptions.HTTPError as e:
            logger.error(f"Overpass API HTTP error for {city_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching POIs from Overpass: {e}", exc_info=True)
            return []
    
    def _map_interests_to_tags(self, interests: List[str]) -> List[str]:
        """Convert user interests to OSM tags"""
        tags = []
        for interest in interests:
            if interest in INTEREST_TAG_MAP:
                tags.extend(INTEREST_TAG_MAP[interest])
        return tags
    
    def _build_overpass_query(self, lat: float, lon: float, 
                              radius_m: int, tags: List[str]) -> str:
        """
        Build Overpass QL query
        
        Query format searches for nodes and ways within radius that match any of the tags
        """
        # Build individual queries for each tag
        queries = []
        for tag in tags:
            key, value = tag.split('=')
            queries.append(f'node["{key}"="{value}"](around:{radius_m},{lat},{lon});')
            queries.append(f'way["{key}"="{value}"](around:{radius_m},{lat},{lon});')
        
        # Combine into single query
        query = f"""
        [out:json][timeout:55];
        (
          {chr(10).join('  ' + q for q in queries)}
        );
        out center;
        """
        
        return query
    
    def _parse_overpass_response(self, data: Dict, city: str, 
                                 interests: List[str]) -> List[Dict]:
        """Parse Overpass API response into POI format"""
        pois = []
        
        elements = data.get('elements', [])
        
        for elem in elements:
            tags = elem.get('tags', {})
            
            # Skip if no name
            name = tags.get('name')
            if not name:
                continue
            
            # Get coordinates
            if 'lat' in elem and 'lon' in elem:
                lat, lon = elem['lat'], elem['lon']
            elif 'center' in elem:
                lat = elem['center']['lat']
                lon = elem['center']['lon']
            else:
                continue
            
            # Determine category and type
            category = self._determine_category(tags, interests)
            osm_type = self._get_osm_type(tags)
            
            # Estimate cost
            cost = self._estimate_cost(tags, osm_type)
            
            poi = {
                'name': name,
                'type': category,
                'osm_type': osm_type,
                'cost': cost,
                'duration': self._estimate_duration(category),
                'lat': lat,
                'lon': lon,
                'interests': [category],
                'city': city,
                'osm_id': f"{elem['type']}{elem['id']}",
                'address': tags.get('addr:street', ''),
                'description': tags.get('description', '')
            }
            
            pois.append(poi)
        
        return pois
    
    def _determine_category(self, tags: Dict, interests: List[str]) -> str:
        """Determine POI category from OSM tags"""
        # Check natural tag first (waterfalls, peaks, caves, etc.)
        if 'natural' in tags:
            natural = tags['natural']
            if natural in ['waterfall', 'hot_spring', 'geyser', 'water']:
                return 'nature'
            if natural == 'peak':
                return 'adventure'
            if natural == 'cave_entrance':
                return 'adventure'
            if natural in ['beach', 'coastline']:
                return 'nature'
        
        # Check waterway tag
        if 'waterway' in tags:
            waterway = tags['waterway']
            if waterway in ['waterfall', 'rapids']:
                return 'nature'

        # Check tourism tag
        if 'tourism' in tags:
            tourism = tags['tourism']
            if tourism in ['museum', 'gallery']:
                return 'museum'
            if tourism in ['attraction', 'monument']:
                return 'culture'
            if tourism == 'viewpoint':
                return 'adventure'
        
        # Check amenity tag
        if 'amenity' in tags:
            amenity = tags['amenity']
            if amenity in ['restaurant', 'cafe', 'fast_food']:
                return 'food'
            if amenity in ['bar', 'nightclub', 'pub']:
                return 'nightlife'
            if amenity == 'marketplace':
                return 'shopping'
            if amenity == 'place_of_worship':
                return 'culture'
        
        # Check other tags
        if 'historic' in tags:
            return 'history'
        if 'leisure' in tags:
            leisure = tags['leisure']
            if leisure in ['park', 'garden', 'nature_reserve']:
                return 'nature'
            if leisure == 'water_park':
                return 'adventure'
        if 'shop' in tags:
            return 'shopping'
        
        # Default to first interest or culture
        return interests[0] if interests else 'culture'
    
    def _get_osm_type(self, tags: Dict) -> str:
        """Get specific OSM type"""
        for key in ['natural', 'waterway', 'tourism', 'amenity', 'historic', 'leisure', 'shop']:
            if key in tags:
                return tags[key]
        return 'attraction'
    
    def _estimate_cost(self, tags: Dict, osm_type: str) -> int:
        """Estimate cost in rupees"""
        # Check if there's a fee tag
        if tags.get('fee') == 'no':
            return 0
        
        return COST_ESTIMATES.get(osm_type, COST_ESTIMATES['default'])
    
    def _estimate_duration(self, category: str) -> int:
        """Estimate visit duration in hours"""
        duration_map = {
            'museum': 2,
            'culture': 1,
            'food': 2,
            'shopping': 3,
            'nature': 2,
            'adventure': 3,
            'history': 2,
            'nightlife': 3,
            'waterfall': 1,
            'peak': 3,
            'cave_entrance': 2
        }
        return duration_map.get(category, 2)


# Singleton instance
_osm_service = None

def get_osm_service() -> OSMService:
    """Get singleton OSM service instance"""
    global _osm_service
    if _osm_service is None:
        _osm_service = OSMService()
    return _osm_service
