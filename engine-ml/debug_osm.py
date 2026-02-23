"""
Debug OSM integration - check why it's failing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.osm_service import get_osm_service
from app.database.poi_cache import get_cache_manager

def test_osm_direct():
    print("=" * 60)
    print("Testing OSM Service Directly")
    print("=" * 60)
    
    osm = get_osm_service()
    
    # Test 1: Geocoding
    print("\n1. Testing Geocoding...")
    coords = osm.geocode_city("Mumbai")
    if coords:
        print(f"✅ Geocoded Mumbai: {coords}")
    else:
        print("❌ Geocoding failed!")
        return
    
    # Test 2: Fetch POIs
    print("\n2. Testing POI Fetch...")
    interests = ["museum", "food", "culture"]
    pois = osm.fetch_pois_for_city("Mumbai", interests, radius_km=20, limit=10)
    
    if pois:
        print(f"✅ Fetched {len(pois)} POIs:")
        for poi in pois[:5]:
            print(f"   - {poi['name']} ({poi['type']}) - ₹{poi['cost']}")
    else:
        print("❌ POI fetch failed!")
        return
    
    # Test 3: Database cache
    print("\n3. Testing Database Cache...")
    try:
        cache = get_cache_manager()
        if cache.connection:
            print("✅ Database connection established")
            
            # Try to save
            saved = cache.save_pois("Mumbai", pois)
            print(f"   Saved {saved} POIs to cache")
            
            # Try to retrieve
            cached_pois = cache.get_cached_pois("Mumbai", interests)
            print(f"   Retrieved {len(cached_pois)} cached POIs")
        else:
            print("❌ No database connection")
    except Exception as e:
        print(f"❌ Cache error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_osm_direct()
