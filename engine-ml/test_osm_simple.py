"""
Quick OSM API Test - No API key needed!
Tests OpenStreetMap integration
"""
import requests

def test_nominatim():
    """Test geocoding Mumbai"""
    print("\n🗺️  Testing Nominatim (Geocoding)...")
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': 'Mumbai, India',
        'format': 'json',
        'limit': 1
    }
    headers = {'User-Agent': 'TravelPro/1.0'}
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"✅ Mumbai coordinates: {data[0]['lat']}, {data[0]['lon']}")
        else:
            print("❌ No results")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_overpass():
    """Test fetching museums in Mumbai"""
    print("\n🏛️  Testing Overpass API (POI Data)...")
    url = "https://overpass-api.de/api/interpreter"
    
    # Query for museums near Mumbai
    query = """
    [out:json][timeout:25];
    (
      node["tourism"="museum"](around:10000,19.0760,72.8777);
    );
    out center 5;
    """
    
    response = requests.post(url, data={'data': query})
    if response.status_code == 200:
        data = response.json()
        pois = data.get('elements', [])
        print(f"✅ Found {len(pois)} museums near Mumbai")
        for poi in pois[:3]:
            name = poi.get('tags', {}).get('name', 'Unknown')
            print(f"   - {name}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_local_integration():
    """Test our local ML engine"""
    print("\n🚀 Testing Local ML Engine Integration...")
    url = "http://localhost:8000/generate_itinerary"
    
    payload = {
        "destination": "Mumbai",
        "days": 2,
        "budget": 5000,
        "interests": ["museum", "food"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            day1_pois = len(data.get('itinerary', {}).get('day_1', []))
            print(f"✅ Generated itinerary with {day1_pois} POIs on Day 1")
        else:
            print(f"⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 OSM API Test (NO API KEY REQUIRED!)")
    print("=" * 50)
    
    test_nominatim()
    test_overpass()
    test_local_integration()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)
