"""
Test script for OpenStreetMap integration
Tests geocoding, POI fetching, and caching
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.osm_service import get_osm_service
from app.database.poi_cache import get_cache_manager
from app.data.poi_data import get_pois_for_destination

def test_geocoding():
    """Test city geocoding"""
    print("\n=== Testing Geocoding ===")
    osm = get_osm_service()
    
    cities = ["Mumbai", "Delhi", "Goa"]
    for city in cities:
        coords = osm.geocode_city(city)
        if coords:
            print(f"✅ {city}: {coords}")
        else:
            print(f"❌ {city}: Failed")

def test_poi_fetch():
    """Test POI fetching from OSM"""
    print("\n=== Testing POI Fetch (OSM API) ===")
    osm = get_osm_service()
    
    city = "Mumbai"
    interests = ["museum", "food"]
    
    print(f"Fetching POIs for {city} with interests: {interests}")
    pois = osm.fetch_pois_for_city(city, interests, radius_km=10, limit=10)
    
    if pois:
        print(f"✅ Fetched {len(pois)} POIs:")
        for i, poi in enumerate(pois[:5], 1):
            print(f"  {i}. {poi['name']} ({poi['type']}) - ₹{poi['cost']}")
    else:
        print("❌ No POIs fetched")

def test_caching():
    """Test cache operations"""
    print("\n=== Testing Cache ===")
    cache = get_cache_manager()
    
    # Check cache stats
    stats = cache.get_cache_stats()
    print(f"Current cache stats: {stats}")
    
    # Test cache freshness
    city = "Mumbai"
    is_fresh = cache.is_cache_fresh(city)
    print(f"Cache fresh for {city}: {is_fresh}")

def test_integrated_flow():
    """Test complete flow with caching"""
    print("\n=== Testing Integrated Flow ===")
    
    city = "Delhi"
    interests = ["culture", "history"]
    
    print(f"\n1st Request (should fetch from OSM):")
    pois1 = get_pois_for_destination(city, interests, use_api=True)
    print(f"Got {len(pois1)} POIs")
    
    print(f"\n2nd Request (should use cache):")
    pois2 = get_pois_for_destination(city, interests, use_api=True)
    print(f"Got {len(pois2)} POIs")
    
    if len(pois1) > 0 and len(pois2) > 0:
        print("✅ Integration test passed!")
    else:
        print("⚠️ Using mock data fallback")

if __name__ == "__main__":
    print("🧪 OSM Integration Test Suite\n")
    
    try:
        test_geocoding()
        test_poi_fetch()
        test_caching()
        test_integrated_flow()
        
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
