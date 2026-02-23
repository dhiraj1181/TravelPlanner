"""
Test the complete trip creation flow
"""
import requests
import json

def test_full_trip():
    url = "http://localhost:8000/generate_itinerary"
    
    # Test multiple cities
    test_cases = [
        {"destination": "Pune", "days": 2, "budget": 5000, "interests": ["museum", "food"]},
        {"destination": "Jaipur", "days": 3, "budget": 8000, "interests": ["history", "culture"]},
        {"destination": "Bangalore", "days": 2, "budget": 6000, "interests": ["food", "shopping"]},
    ]
    
    for test in test_cases:
        print("\n" + "=" * 70)
        print(f"Testing: {test['destination']} - {test['days']} days")
        print("=" * 70)
        
        try:
            response = requests.post(url, json=test, timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ SUCCESS!")
                print(f"   Destination: {data.get('destination')}")
                print(f"   Days: {data.get('days')}")
                print(f"   Budget: ₹{data.get('totalBudget')}")
                print(f"   Estimated: ₹{data.get('estimatedCost')}")
                print(f"   Green Signal: {data.get('greenSignal')}")
                
                day_by_day = data.get('dayByDay', [])
                print(f"   Total Days with POIs: {len(day_by_day)}")
                
                for day_data in day_by_day[:2]:  # Show first 2 days
                    pois = day_data.get('pois', [])
                    print(f"\n   📅 Day {day_data.get('day')}: {len(pois)} POIs")
                    for poi in pois[:3]:  # Show first 3 POIs
                        print(f"      ✓ {poi.get('name')} ({poi.get('type')}) - ₹{poi.get('cost')}")
                
                # Check if these are REAL names (not mock)
                first_day_pois = day_by_day[0].get('pois', []) if day_by_day else []
                if first_day_pois:
                    first_poi_name = first_day_pois[0].get('name', '')
                    if first_poi_name in ['City Museum', 'Local Restaurant', 'Shopping District']:
                        print(f"\n   ⚠️  WARNING: Using MOCK data (generic names)")
                    else:
                        print(f"\n   ✅ Using REAL OSM data (specific place names)")
            else:
                print(f"❌ FAILED: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_full_trip()
