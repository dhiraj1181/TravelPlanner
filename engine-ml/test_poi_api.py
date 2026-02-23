"""
Test script for OpenTripMap API integration
"""
import sys
sys.path.append('.')

from app.services.poi_api import get_service

def test_geocoding():
    """Test geocoding Paris"""
    print("\n=== Testing Geocoding ===")
    service = get_service()
    coords = service.geocode_destination("Paris")
    print(f"Paris coordinates: {coords}")
    assert coords is not None
    assert "lat" in coords and "lon" in coords
    print("✓ Geocoding successful!")

def test_fetch_pois():
    """Test fetching POIs for Paris"""
    print("\n=== Testing POI Fetching ===")
    service = get_service()
    
    # First geocode
    coords = service.geocode_destination("Paris")
    print(f"Coordinates: {coords}")
    
    # Fetch POIs
    pois = service.fetch_pois_by_radius(
        lat=coords["lat"],
        lon=coords["lon"],
        interests=["museum", "food"],
        radius=5000,
        limit=10
    )
    
    print(f"Fetched {len(pois)} POIs")
    if pois:
        print("\nFirst POI:")
        print(pois[0])
        print("✓ POI fetching successful!")
    else:
        print("⚠ No POIs returned")

def test_normalization():
    """Test POI data normalization"""
    print("\n=== Testing POI Normalization ===")
    service = get_service()
    
    # Sample API POI
    api_poi = {
        "name": "Louvre Museum",
        "kinds": "museums,cultural",
        "point": {"lat": 48.8606, "lon": 2.3376}
    }
    
    normalized = service.normalize_poi_data(api_poi, "museum")
    print(f"Normalized POI: {normalized}")
    
    assert "name" in normalized
    assert "type" in normalized
    assert "cost" in normalized
    assert "duration" in normalized
    assert "lat" in normalized
    assert "lon" in normalized
    assert "interests" in normalized
    print("✓ Normalization successful!")

def test_full_integration():
    """Test full POI data integration"""
    print("\n=== Testing Full Integration ===")
    from app.data.poi_data import get_pois_for_destination
    
    pois = get_pois_for_destination("Paris", ["museum", "food"], use_api=True)
    print(f"Got {len(pois)} POIs for Paris")
    
    if pois:
        print("\nFirst 3 POIs:")
        for i, poi in enumerate(pois[:3], 1):
            print(f"{i}. {poi['name']} ({poi['type']}) - ${poi['cost']}, {poi['duration']}h")
        print("✓ Full integration successful!")
    else:
        print("⚠ No POIs returned, falling back to mock data")

if __name__ == "__main__":
    try:
        print("=== OpenTripMap API Integration Tests ===\n")
        
        test_geocoding()
        test_fetch_pois()
        test_normalization()
        test_full_integration()
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
