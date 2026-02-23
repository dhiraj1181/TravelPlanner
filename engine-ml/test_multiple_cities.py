"""
Test OSM for multiple Indian cities
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.osm_service import get_osm_service

def test_cities():
    cities = [
        "Mumbai",
        "Delhi",
        "Bangalore",
        "Pune",
        "Hyderabad",
        "Chennai",
        "Kolkata",
        "Jaipur",
        "Goa",
        "Agra"
    ]
    
    osm = get_osm_service()
    interests = ["museum", "food", "culture"]
    
    print("=" * 70)
    print("Testing OSM for Multiple Indian Cities")
    print("=" * 70)
    
    results = {}
    
    for city in cities:
        print(f"\n🔍 Testing {city}...")
        
        # Test geocoding
        coords = osm.geocode_city(city)
        if not coords:
            print(f"   ❌ Geocoding failed")
            results[city] = "Geocoding Failed"
            continue
        
        print(f"   ✅ Geocoded: {coords['lat']:.4f}, {coords['lon']:.4f}")
        
        # Test POI fetch
        pois = osm.fetch_pois_for_city(city, interests, radius_km=30, limit=20)
        
        if not pois:
            print(f"   ❌ No POIs found")
            results[city] = "No POIs"
        elif len(pois) < 5:
            print(f"   ⚠️  Only {len(pois)} POIs (too few)")
            results[city] = f"Only {len(pois)} POIs"
            for poi in pois:
                print(f"      - {poi['name']}")
        else:
            print(f"   ✅ Found {len(pois)} POIs")
            results[city] = f"✓ {len(pois)} POIs"
            for poi in pois[:3]:
                print(f"      - {poi['name']} ({poi['type']})")
    
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    for city, result in results.items():
        status = "✅" if result.startswith("✓") else "❌"
        print(f"{status} {city:15} - {result}")

if __name__ == "__main__":
    test_cities()
