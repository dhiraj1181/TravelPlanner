"""
Quick diagnostic test - check what's failing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.osm_service import get_osm_service

def quick_test():
    osm = get_osm_service()
    
    city = "Pune"
    interests = ["museum", "food"]
    
    print(f"\n🔍 Testing {city}...")
    print("=" * 60)
    
    # Step 1: Geocoding
    print(f"\n1️⃣ Geocoding...")
    coords = osm.geocode_city(city)
    if coords:
        print(f"   ✅ SUCCESS: {coords}")
    else:
        print(f"   ❌ FAILED: Could not geocode {city}")
        return
    
    # Step 2: POI Fetch
    print(f"\n2️⃣ Fetching POIs from Overpass API...")
    print(f"   Coordinates: {coords['lat']}, {coords['lon']}")
    print(f"   Interests: {interests}")
    
    try:
        pois = osm.fetch_pois_for_city(city, interests, radius_km=10, limit=5)
        
        if pois:
            print(f"   ✅ SUCCESS: Got {len(pois)} POIs")
            for poi in pois:
                print(f"      - {poi['name']} ({poi['type']}) - ₹{poi['cost']}")
        else:
            print(f"   ❌ FAILED: No POIs returned (check logs above for error)")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    quick_test()
