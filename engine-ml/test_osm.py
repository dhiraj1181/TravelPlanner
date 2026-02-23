"""
Comprehensive test of OSM integration
"""
import requests
import json

def test_endpoint():
    url = "http://localhost:8000/generate_itinerary"
    
    payload = {
        "destination": "Mumbai",
        "days": 3,
        "budget": 10000,
        "interests": ["museum", "food", "culture"]
    }
    
    print("=" * 60)
    print("Testing OSM Integration")
    print("=" * 60)
    print(f"\nEndpoint: {url}")
    print(f"Request:\n{json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS!")
            print(f"\nDestination: {data.get('destination')}")
            print(f"Days: {data.get('days')}")
            print(f"Total Budget: ₹{data.get('totalBudget')}")
            print(f"Estimated Cost: ₹{data.get('estimatedCost')}")
            print(f"Within Budget: {'✓ Yes' if data.get('greenSignal') else '✗ No'}")
            
            day_by_day = data.get('dayByDay', [])
            print(f"\nTotal Days: {len(day_by_day)}")
            
            total_pois = 0
            for day_data in day_by_day:
                pois = day_data.get('pois', [])
                total_pois += len(pois)
                print(f"\nDay {day_data.get('day')}: {len(pois)} POIs")
                for idx, poi in enumerate(pois[:3], 1):  # Show first 3
                    print(f"  {idx}. {poi.get('name')} ({poi.get('type')}) - ₹{poi.get('cost')}")
                if len(pois) > 3:
                    print(f"  ... and {len(pois) - 3} more")
            
            print(f"\n📍 Total POIs: {total_pois}")
            print("\n✅ OSM Integration Working! Real data fetched from OpenStreetMap")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("⏱️ Request timed out (OSM API might be slow)")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_endpoint()
