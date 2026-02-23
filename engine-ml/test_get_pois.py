"""
Quick test for /get_pois endpoint
"""
import requests
import json

def test_get_pois():
    url = "http://localhost:8000/get_pois"
    
    payload = {
        "destination": "Mumbai",
        "interests": []
    }
    
    print(f"Testing {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"City: {data.get('city')}")
            print(f"Count: {data.get('count')}")
            
            pois = data.get('pois', [])
            if pois:
                print(f"\nFirst 5 POIs:")
                for i, poi in enumerate(pois[:5], 1):
                    print(f"{i}. {poi.get('name')} ({poi.get('type')}) - ₹{poi.get('cost', 0)} - {poi.get('duration', 2)}h")
            else:
                print("No POIs returned")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_get_pois()
