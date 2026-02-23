"""
Test ONE city with detailed output and check the server logs
"""
import requests
import json
import time

url = "http://localhost:8000/generate_itinerary"

payload = {
    "destination": "Jaipur",
    "days": 2,
    "budget": 5000,
    "interests": ["history", "culture"]
}

print("\n" + "=" * 70)
print(f"Testing: {payload['destination']}")
print("=" * 70)
print(f"\nRequest: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Status: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        print("📌 Response received!")
        print(f"   Destination: {data.get('destination')}")
        print(f"   Days: {data.get('days')}")
        
        day_by_day = data.get('dayByDay', [])
        print(f"   Total Days: {len(day_by_day)}\n")
        
        for day_data in day_by_day:
            pois = day_data.get('pois', [])
            print(f"   Day {day_data.get('day')}: {len(pois)} POIs")
            for poi in pois:
                name = poi.get('name')
                poi_type = poi.get('type')
                cost = poi.get('cost')
                print(f"      • {name} ({poi_type}) - ₹{cost}")
        
        # Check for mock data
        first_day_pois = day_by_day[0].get('pois', []) if day_by_day else []
        if first_day_pois:
            first_name = first_day_pois[0].get('name', '')
            if first_name in ['City Museum', 'Local Restaurant', 'Shopping District', 'Historical Monument']:
                print(f"\n❌ MOCK DATA DETECTED: '{first_name}'")
            else:
                print(f"\n✅ REAL OSM DATA: '{first_name}'")
    else:
        print(f"❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Connection error - is ML engine running?")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 70)
print("⚠️  Now check the ML engine terminal for debug logs!")
print("   Look for lines with 'POI names BEFORE clustering'")
print("=" * 70 + "\n")
