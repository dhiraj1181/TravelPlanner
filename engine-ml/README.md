# ML Engine - FastAPI Service

Generates optimized travel itineraries using clustering and routing algorithms.

## Run

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Server starts on `http://localhost:8000`

## Configuration

### OpenTripMap API (Optional)

To fetch real POI data from OpenTripMap instead of using mock data:

1. Get free API key: https://opentripmap.io/product
2. Set environment variable:

**Windows:**
```powershell
$env:OPENTRIPMAP_API_KEY="your_api_key_here"
```

**Linux/Mac:**
```bash
export OPENTRIPMAP_API_KEY="your_api_key_here"
```

3. Restart the ML engine

Without API key, the system uses built-in mock POI data for Paris, Tokyo, London, and New York.

## API

### POST /generate_itinerary

**Request:**
```json
{
  "destination": "Paris",
  "days": 3,
  "budget": 1500,
  "interests": ["museum", "food"]
}
```

**Response:**
```json
{
  "estimated_cost": 1350.50,
  "green_signal": true,
  "day_by_day": [
    {
      "day": 1,
      "pois": [
        {
          "name": "Louvre Museum",
          "type": "museum",
          "lat": 48.8606,
          "lon": 2.3376,
          "cost": 17.0,
          "duration": 180
        }
      ]
    }
  ]
}
```

## Features

### POI Data Sources
- **OpenTripMap API** (with API key) - Real-time data for any destination
- **Mock Database** (fallback) - Pre-loaded data for popular cities

### Algorithms
- **K-means Clustering**: Groups attractions by geographic proximity
- **TSP Routing**: Optimizes visit order using nearest neighbor
- **Budget Prediction**: Estimates total cost with 20% buffer

### Interest Filtering
Supports: museum, food, culture, history, nature, shopping, adventure, nightlife

## Tech

- FastAPI
- NumPy
- scikit-learn
- httpx
