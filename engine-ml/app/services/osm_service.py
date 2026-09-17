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

# Overpass API mirrors — tried in order; first success wins
# Ordered by reliability/speed; dead mirrors removed.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",           # primary (DE)
    "https://overpass.kumi.systems/api/interpreter",     # EU mirror (AT)
    "https://overpass.private.coffee/api/interpreter",  # fast EU mirror
    "https://overpass.openstreetmap.fr/api/interpreter", # FR mirror
]
# Per-mirror HTTP timeout (seconds). Short = fail fast, move to next mirror.
_MIRROR_TIMEOUT = 15

# Max tags per Overpass sub-query batch.
# Large batches (30+ tags) time out on major cities — keep to ≤7.
_MAX_TAGS_PER_BATCH = 7
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
    # NCR satellite cities -- DISTINCT cities, each with its own geocentre
    "noida": {"lat": 28.5355, "lon": 77.3910},
    "greater noida": {"lat": 28.4744, "lon": 77.5040},
    "gurgaon": {"lat": 28.4595, "lon": 77.0266},
    "gurugram": {"lat": 28.4595, "lon": 77.0266},
    "ghaziabad": {"lat": 28.6692, "lon": 77.4538},
    "trivandrum": {"lat": 8.5241, "lon": 76.9366},
    # Additional cities shown on landing page
    "manali": {"lat": 32.2396, "lon": 77.1887},
    "rishikesh": {"lat": 30.0869, "lon": 78.2676},
    "darjeeling": {"lat": 27.0360, "lon": 88.2627},
    "kerala": {"lat": 10.8505, "lon": 76.2711},
    "ooty": {"lat": 11.4102, "lon": 76.6950},
    "shimla": {"lat": 31.1048, "lon": 77.1734},
    "udaipur": {"lat": 24.5854, "lon": 73.7125},
    "pushkar": {"lat": 26.4898, "lon": 74.5511},
    "hampi": {"lat": 15.3350, "lon": 76.4600},
    "pondicherry": {"lat": 11.9416, "lon": 79.8083},
    "puducherry": {"lat": 11.9416, "lon": 79.8083},
    # East & North-East India
    "bhubaneswar": {"lat": 20.2961, "lon": 85.8245},
    "cuttack": {"lat": 20.4625, "lon": 85.8830},
    "puri": {"lat": 19.8135, "lon": 85.8312},
    "rourkela": {"lat": 22.2604, "lon": 84.8536},
    "imphal": {"lat": 24.8170, "lon": 93.9368},
    "shillong": {"lat": 25.5788, "lon": 91.8933},
    "aizawl": {"lat": 23.7271, "lon": 92.7176},
    "kohima": {"lat": 25.6747, "lon": 94.1100},
    "agartala": {"lat": 23.8315, "lon": 91.2868},
    "itanagar": {"lat": 27.0844, "lon": 93.6053},
    "gangtok": {"lat": 27.3389, "lon": 88.6065},
    "dibrugarh": {"lat": 27.4728, "lon": 94.9120},
    "siliguri": {"lat": 26.7271, "lon": 88.3953},
    "durgapur": {"lat": 23.5204, "lon": 87.3119},
    "asansol": {"lat": 23.6888, "lon": 86.9661},
    # South India
    "kochi": {"lat": 9.9312, "lon": 76.2673},
    "cochin": {"lat": 9.9312, "lon": 76.2673},
    "kozhikode": {"lat": 11.2588, "lon": 75.7804},
    "calicut": {"lat": 11.2588, "lon": 75.7804},
    "thrissur": {"lat": 10.5276, "lon": 76.2144},
    "kollam": {"lat": 8.8932, "lon": 76.6141},
    "kottayam": {"lat": 9.5916, "lon": 76.5222},
    "mangalore": {"lat": 12.9141, "lon": 74.8560},
    "mangaluru": {"lat": 12.9141, "lon": 74.8560},
    "hubli": {"lat": 15.3647, "lon": 75.1240},
    "dharwad": {"lat": 15.4589, "lon": 75.0078},
    "belgaum": {"lat": 15.8497, "lon": 74.4977},
    "belagavi": {"lat": 15.8497, "lon": 74.4977},
    "tumkur": {"lat": 13.3379, "lon": 77.1173},
    "tirupati": {"lat": 13.6288, "lon": 79.4192},
    "tirunelveli": {"lat": 8.7139, "lon": 77.7567},
    "vellore": {"lat": 12.9165, "lon": 79.1325},
    "thanjavur": {"lat": 10.7870, "lon": 79.1378},
    "tanjore": {"lat": 10.7870, "lon": 79.1378},
    "tiruchirappalli": {"lat": 10.7905, "lon": 78.7047},
    "trichy": {"lat": 10.7905, "lon": 78.7047},
    "salem": {"lat": 11.6643, "lon": 78.1460},
    "erode": {"lat": 11.3410, "lon": 77.7172},
    # North India
    "dehradun": {"lat": 30.3165, "lon": 78.0322},
    "haridwar": {"lat": 29.9457, "lon": 78.1642},
    "nainital": {"lat": 29.3803, "lon": 79.4636},
    "mussoorie": {"lat": 30.4598, "lon": 78.0664},
    "almora": {"lat": 29.5975, "lon": 79.6532},
    "kasauli": {"lat": 30.8993, "lon": 76.9657},
    "dharamsala": {"lat": 32.2190, "lon": 76.3234},
    "mcleod ganj": {"lat": 32.2427, "lon": 76.3234},
    "dalhousie": {"lat": 32.5382, "lon": 75.9737},
    "spiti": {"lat": 32.2461, "lon": 78.0339},
    "leh": {"lat": 34.1526, "lon": 77.5771},
    "ladakh": {"lat": 34.1526, "lon": 77.5771},
    "kargil": {"lat": 34.5539, "lon": 76.1349},
    "ambala": {"lat": 30.3782, "lon": 76.7767},
    "karnal": {"lat": 29.6857, "lon": 76.9905},
    "panipat": {"lat": 29.3909, "lon": 76.9635},
    "rohtak": {"lat": 28.8955, "lon": 76.6066},
    "hisar": {"lat": 29.1492, "lon": 75.7217},
    "mathura": {"lat": 27.4924, "lon": 77.6737},
    "vrindavan": {"lat": 27.5795, "lon": 77.7024},
    "ayodhya": {"lat": 26.7922, "lon": 82.1998},
    "gorakhpur": {"lat": 26.7606, "lon": 83.3732},
    # West India
    "nashik": {"lat": 19.9975, "lon": 73.7898},
    "kolhapur": {"lat": 16.7050, "lon": 74.2433},
    "sangli": {"lat": 16.8524, "lon": 74.5815},
    "akola": {"lat": 20.7002, "lon": 77.0082},
    "nanded": {"lat": 19.1383, "lon": 77.3210},
    "jamnagar": {"lat": 22.4707, "lon": 70.0577},
    "bhavnagar": {"lat": 21.7645, "lon": 72.1519},
    "anand": {"lat": 22.5645, "lon": 72.9289},
    "gandhinagar": {"lat": 23.2156, "lon": 72.6369},
    "mount abu": {"lat": 24.5926, "lon": 72.7156},
    "jaisalmer": {"lat": 26.9157, "lon": 70.9083},
    "bikaner": {"lat": 28.0229, "lon": 73.3119},
    "ajmer": {"lat": 26.4499, "lon": 74.6399},
    "bharatpur": {"lat": 27.2152, "lon": 77.4890},
    "alwar": {"lat": 27.5530, "lon": 76.6346},
    "chittorgarh": {"lat": 24.8887, "lon": 74.6269},
    # Central India
    "ujjain": {"lat": 23.1793, "lon": 75.7849},
    "gwalior": {"lat": 26.2183, "lon": 78.1828},
    "orchha": {"lat": 25.3516, "lon": 78.6404},
    "khajuraho": {"lat": 24.8318, "lon": 79.9199},
    "pachmarhi": {"lat": 22.4677, "lon": 78.4338},
    "amarkantak": {"lat": 22.6741, "lon": 81.7594},
    "rewa": {"lat": 24.5362, "lon": 81.3035},
    "satna": {"lat": 24.5703, "lon": 80.8322},
    "bilaspur": {"lat": 22.0796, "lon": 82.1391},
    "jagdalpur": {"lat": 19.0720, "lon": 82.0180},
}


# ── Alias / alternate-spelling map ──────────────────────────────────────────
# Maps common misspellings, alternate names, and old names → canonical key
# in INDIAN_CITIES_COORDS.  All keys are lowercase.
CITY_ALIASES: Dict[str, str] = {
    # Misspellings (common user typos)
    "bhuneswar": "bhubaneswar",
    "bhuvaneshwar": "bhubaneswar",
    "bhuvneshwar": "bhubaneswar",
    "bhubneshwar": "bhubaneswar",
    "bhuneshwar": "bhubaneswar",
    "bhubaneswar": "bhubaneswar",
    "vishakhapatnam": "visakhapatnam",
    "vizag": "visakhapatnam",
    "vizakhapatnam": "visakhapatnam",
    "banglore": "bangalore",
    "bangaluru": "bengaluru",
    "bangluru": "bengaluru",
    "dilli": "delhi",
    "new delhi": "delhi",
    "ncr": "delhi",
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "calcutta": "kolkata",
    "kolkatta": "kolkata",
    "madras": "chennai",
    "poona": "pune",
    "mysuru": "mysore",
    "mysore": "mysore",
    "trichy": "tiruchirappalli",
    "trichirappalli": "tiruchirappalli",
    "tanjore": "thanjavur",
    "calicut": "kozhikode",
    "cochin": "kochi",
    "ernakulam": "kochi",
    "trivandrum": "thiruvananthapuram",
    "ahemdabad": "ahmedabad",
    "ahamadabad": "ahmedabad",
    # NCR typo-only aliases (these cities are DISTINCT from Delhi — map to their own entry)
    "gurugram": "gurgaon",      # official rename; same coordinates
    "greater noida": "greater noida",
    "ghaziabad": "ghaziabad",
    "faridabadabad": "faridabad",  # typo fix only
    "allahbad": "allahabad",
    "prayagraj": "prayagraj",
    "mcleodganj": "mcleod ganj",
    "dharamshala": "dharamsala",
    "dharmshala": "dharamsala",
    "jamshedpur": "ranchi",   # closest city in DB
    "bokaro": "ranchi",
    "hazaribagh": "ranchi",
    "ooty": "ooty",
    "udhagamandalam": "ooty",
    "pondichery": "puducherry",
    "pondy": "puducherry",
    "pondichery": "puducherry",
    "manali": "manali",
    "kasol": "manali",
    "solang": "manali",
    "leh ladakh": "leh",
    "ladhak": "ladakh",
    "ladhakh": "ladakh",
    "mclo": "mcleod ganj",
    # Common abbreviations / alternative spellings
    "blr": "bangalore",
    "del": "delhi",
    "bom": "mumbai",
    "ccu": "kolkata",
    "maa": "chennai",
    "hyd": "hyderabad",
    "pnq": "pune",
    "amd": "ahmedabad",
    "jai": "jaipur",
    "vns": "varanasi",
    "ixb": "siliguri",
    "bbi": "bhubaneswar",
}


class OSMService:
    """Service for fetching POI data from OpenStreetMap"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TravelPro/1.0 (Travel Planning App)'
        })
    
    @staticmethod
    def _normalise_city(city_name: str) -> str:
        """Lowercase, strip, collapse whitespace."""
        return ' '.join(city_name.lower().strip().split())

    def geocode_city(self, city_name: str) -> Optional[Dict[str, float]]:
        """
        Resolve a city name to (lat, lon) using a 4-stage pipeline:

          1. Alias map   — catches misspellings & alternate names instantly
          2. Offline DB  — 200+ Indian cities; zero network cost
          3. Nominatim   — REST geocoding (countrycode=IN for accuracy)
          4. Nominatim retry — wider search without countrycode restriction

        Returns dict with 'lat'/'lon', or None if all stages fail.
        """
        city_norm = self._normalise_city(city_name)

        # Stage 1 — alias mapping (handles typos like 'bhuneswar')
        if city_norm in CITY_ALIASES:
            canonical = CITY_ALIASES[city_norm]
            logger.info(f"Alias match: '{city_name}' → '{canonical}'")
            city_norm = canonical

        # Stage 2 — offline coordinate database
        if city_norm in INDIAN_CITIES_COORDS:
            logger.info(f"Offline DB hit for '{city_norm}'")
            return INDIAN_CITIES_COORDS[city_norm]

        # Stage 3 — Nominatim (India-scoped)
        coords = self._nominatim_lookup(city_name, countrycode='IN')
        if coords:
            logger.info(f"Nominatim (IN) resolved '{city_name}' → {coords}")
            # Cache in-memory so repeat requests are instant
            INDIAN_CITIES_COORDS[city_norm] = coords
            return coords

        # Stage 4 — Nominatim without country restriction (catches edge cases)
        coords = self._nominatim_lookup(city_name, countrycode=None)
        if coords:
            logger.info(f"Nominatim (global) resolved '{city_name}' → {coords}")
            INDIAN_CITIES_COORDS[city_norm] = coords
            return coords

        logger.error(
            f"Could not geocode '{city_name}'. "
            "Check spelling — e.g. 'Bhubaneswar' not 'bhuneswar'."
        )
        return None

    def _nominatim_lookup(
        self, city_name: str, countrycode: Optional[str]
    ) -> Optional[Dict[str, float]]:
        """Single Nominatim HTTP call.  Returns coords dict or None."""
        params: Dict = {
            'q': city_name,
            'format': 'json',
            'limit': 1,
            'addressdetails': 0,
        }
        if countrycode:
            params['countrycodes'] = countrycode

        scope = f"countrycode={countrycode}" if countrycode else "global"
        logger.info(f"Nominatim lookup [{scope}]: {city_name}")
        try:
            resp = self.session.get(NOMINATIM_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data:
                return {
                    'lat': float(data[0]['lat']),
                    'lon': float(data[0]['lon'])
                }
            logger.warning(f"Nominatim [{scope}]: no result for '{city_name}'")
        except Exception as exc:
            logger.warning(f"Nominatim [{scope}] error for '{city_name}': {exc}")
        return None
    
    def _query_overpass(self, query: str) -> Optional[Dict]:
        """
        Try each Overpass mirror in order; return the first successful JSON response.
        Returns None if every mirror fails.
        """
        for mirror_idx, mirror_url in enumerate(OVERPASS_MIRRORS):
            try:
                logger.info(
                    f"Trying Overpass mirror {mirror_idx + 1}/{len(OVERPASS_MIRRORS)}: "
                    f"{mirror_url.split('/')[2]}"
                )
                response = self.session.post(
                    mirror_url,
                    data={'data': query},
                    timeout=_MIRROR_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                logger.warning(f"Mirror {mirror_url.split('/')[2]} timed out, trying next...")
                if mirror_idx < len(OVERPASS_MIRRORS) - 1:
                    time.sleep(1)
            except requests.exceptions.HTTPError as e:
                logger.warning(f"Mirror {mirror_url.split('/')[2]} HTTP error: {e}, trying next...")
                if mirror_idx < len(OVERPASS_MIRRORS) - 1:
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Mirror {mirror_url.split('/')[2]} error: {e}, trying next...")
        logger.error("All Overpass mirrors failed")
        return None

    def fetch_pois_for_city(self, city_name: str, interests: List[str],
                            radius_km: float = 30, limit: int = 200) -> List[Dict]:
        """
        Fetch POIs from OpenStreetMap via Overpass API.

        Uses BATCHED queries: instead of one request with 30+ sub-queries
        (which times out on large cities), sends multiple small requests
        with at most _MAX_TAGS_PER_BATCH tags each. Results are merged,
        de-duplicated by OSM ID, and trimmed to `limit`.

        Args:
            city_name:  City to search
            interests:  Interest categories (museum, food, nature …)
            radius_km:  Search radius from city centre (default 30 km)
            limit:      Maximum POIs to return
        """
        coords = self.geocode_city(city_name)
        if not coords:
            logger.error(f"Could not geocode {city_name}")
            return []

        osm_tags = self._map_interests_to_tags(interests)
        if not osm_tags:
            logger.warning("No OSM tags for interests, using default")
            osm_tags = ["tourism=attraction"]

        radius_m = int(radius_km * 1000)

        # ─ Split tags into small batches so each query is light ───────────────
        batches = [
            osm_tags[i:i + _MAX_TAGS_PER_BATCH]
            for i in range(0, len(osm_tags), _MAX_TAGS_PER_BATCH)
        ]
        logger.info(
            f"Fetching POIs for {city_name}: {len(osm_tags)} tags → "
            f"{len(batches)} batches (max {_MAX_TAGS_PER_BATCH} tags each)"
        )

        all_pois: List[Dict] = []
        seen_ids: set = set()

        for batch_num, batch_tags in enumerate(batches, 1):
            query = self._build_overpass_query(
                coords['lat'], coords['lon'], radius_m, batch_tags
            )
            logger.debug(f"Batch {batch_num}/{len(batches)}: {batch_tags}")

            data = self._query_overpass(query)
            if data is None:
                logger.warning(f"Batch {batch_num} failed on all mirrors, skipping")
                continue

            batch_pois = self._parse_overpass_response(
                data, city_name, interests,
                city_lat=coords['lat'], city_lon=coords['lon']
            )

            # De-duplicate by osm_id across batches
            for poi in batch_pois:
                oid = poi.get('osm_id')
                if oid and oid not in seen_ids:
                    seen_ids.add(oid)
                    all_pois.append(poi)

            logger.info(f"Batch {batch_num}/{len(batches)}: +{len(batch_pois)} POIs (total {len(all_pois)})")

            # Stop early if we already have enough
            if len(all_pois) >= limit:
                break

        logger.info(f"Finished: {len(all_pois)} unique POIs for {city_name}")
        return all_pois[:limit]
    
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
        Build an optimised Overpass QL query.

        Uses `nwr` (node + way + relation in one keyword) instead of
        separate `node` + `way` lines, halving the number of sub-queries:

          Before: 34 tags × 2 (node+way)  = 68 sub-queries  ← times out
          After:  34 tags × 1 (nwr)       = 34 sub-queries  ← fast

        Timeout set to 25 s so failures surface quickly instead of
        hanging for a full minute.
        """
        queries = []
        for tag in tags:
            key, value = tag.split('=')
            queries.append(
                f'nwr["{key}"="{value}"](around:{radius_m},{lat},{lon});'
            )

        query = (
            f"[out:json][timeout:{_MIRROR_TIMEOUT}];\n"
            f"(\n"
            + "\n".join(f"  {q}" for q in queries)
            + "\n);\nout center;"
        )
        return query
    
    # Common generic single-word names that are not real POI names
    _JUNK_NAMES = {
        'shop', 'store', 'restaurant', 'hotel', 'cafe', 'bar', 'atm',
        'bank', 'hospital', 'school', 'college', 'office', 'market',
        'temple', 'church', 'mosque', 'mandir', 'masjid', 'parking',
        'petrol', 'fuel', 'null', 'none', 'unnamed', 'unknown',
    }

    def _is_good_name(self, name: str) -> bool:
        """Return False for low-quality POI names that are generic/meaningless."""
        if not name or len(name.strip()) < 3:
            return False
        stripped = name.strip()
        # Pure numeric names (e.g. "123", "A-45")
        if stripped.replace('-', '').replace(' ', '').isdigit():
            return False
        # Single-word generic nouns
        if stripped.lower() in self._JUNK_NAMES:
            return False
        return True

    def _within_city_radius(self, lat: float, lon: float,
                            city_lat: float, city_lon: float,
                            max_km: float = 30.0) -> bool:
        """Return True if (lat,lon) is within max_km of city centre.

        30 km matches the default Overpass search radius so that OSM ways
        whose centre point is computed far from the search area (large rivers,
        forests, etc.) are rejected.  Tighter than the old 60 km limit which
        was accidentally including towns like Lonavala (65 km from Pune) and
        Mahabaleshwar (120 km from Pune) via the background-fetch 50 km radius.
        """
        import math
        R = 6371.0
        phi1, phi2 = math.radians(city_lat), math.radians(lat)
        dphi = math.radians(lat - city_lat)
        dlam = math.radians(lon - city_lon)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
        dist = R * 2 * math.asin(math.sqrt(a))
        return dist <= max_km

    def _parse_overpass_response(self, data: Dict, city: str,
                                 interests: List[str],
                                 city_lat: float = None,
                                 city_lon: float = None) -> List[Dict]:
        """
        Parse Overpass API response into POI format.

        Quality filters applied:
          1. Must have a name
          2. Name must pass _is_good_name (not generic/numeric)
          3. Coordinates must be within 60 km of city centre
             (catches wrong-continent centre points for large OSM ways)
        """
        pois = []
        skipped_coord = 0
        skipped_name = 0

        elements = data.get('elements', [])

        for elem in elements:
            tags = elem.get('tags', {})

            # ── Filter 1: Must have a usable name ─────────────────────────
            name = tags.get('name')
            if not name or not self._is_good_name(name):
                skipped_name += 1
                continue

            # ── Filter 2: Resolve coordinates ──────────────────────────────
            if 'lat' in elem and 'lon' in elem:
                lat, lon = elem['lat'], elem['lon']
            elif 'center' in elem:
                lat = elem['center']['lat']
                lon = elem['center']['lon']
            else:
                continue

            # ── Filter 3: Coordinate boundary check ────────────────────────
            # Large OSM ways (rivers, forests) can have wildly wrong centre
            # points. Reject anything outside 60 km of the searched city.
            if city_lat is not None and city_lon is not None:
                if not self._within_city_radius(lat, lon, city_lat, city_lon):
                    skipped_coord += 1
                    logger.debug(
                        f"Rejected out-of-range POI '{name}' "
                        f"at ({lat:.4f},{lon:.4f}) — >60km from {city}"
                    )
                    continue

            # Determine category and type
            category = self._determine_category(tags, interests)
            osm_type = self._get_osm_type(tags)
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
                'osm_element_type': elem.get('type', 'node'),
                'address': tags.get('addr:street', ''),
                'description': tags.get('description', ''),
                'wikipedia': tags.get('wikipedia', ''),
                'wikidata': tags.get('wikidata', ''),
                'raw_tags': tags
            }
            pois.append(poi)

        if skipped_coord or skipped_name:
            logger.info(
                f"POI quality filter: kept {len(pois)}, "
                f"rejected {skipped_name} bad-name, "
                f"{skipped_coord} out-of-range"
            )
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
