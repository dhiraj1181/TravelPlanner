"""
Test ML engine generate_itinerary endpoint
"""
import requests
import json

url = "http://localhost:8000/generate_itinerary"

payload = {
    "destination": "Mumbai",
    "days": 3,
    "budget": 5000,
    "interests": ["museum", "food"]
}

print(f"Testing {url}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(url, json=payload, timeout=10)
    
    print(f"Status: {response.status_code}")
    print(f"Response:\n{response.text}")
    
except Exception as e:
    print(f"Error: {e}")
