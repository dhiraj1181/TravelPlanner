"""
TravelPro ML Engine - Main FastAPI Application
Generates optimized travel itineraries using clustering and TSP algorithms
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import logging

from app.models import ItineraryRequest, ItineraryResponse, DayItinerary, POI
from app.data.poi_data import get_pois_for_destination
from app.algorithms.clustering import cluster_pois_by_day, balance_clusters
from app.algorithms.tsp import optimize_daily_route
from app.algorithms.budget import predict_budget

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TravelPro ML Engine",
    description="AI-powered travel itinerary generation service",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "TravelPro ML Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "generate_itinerary": "POST /generate_itinerary",
            "get_pois": "POST /get_pois",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/generate_itinerary")
async def generate_itinerary(request: ItineraryRequest):
    """
    Generate an optimized travel itinerary
    
    Input:
        - destination: City name
        - days: Number of days
        - budget: Total budget
        - interests: List of interest categories
    
    Output:
        - itinerary: Dictionary of day-wise POI lists
        - total_cost: Estimated total cost
        - optimized_score: Quality metric
    """
    try:
        logger.info(f"Processing itinerary request for {request.destination}, {request.days} days")
        
        # Step 1: Get POIs for destination from OpenStreetMap
        pois = get_pois_for_destination(request.destination, request.interests, use_api=True)
        
        if not pois or len(pois) == 0:
            logger.warning(f"No POIs found for {request.destination}")
            raise HTTPException(
                status_code=404,
                detail=f"No points of interest found for {request.destination}"
            )
        
        logger.info(f"Found {len(pois)} POIs for {request.destination}")
        
        # Log POI names before clustering
        poi_names = [poi.get('name', 'UNKNOWN') for poi in pois[:5]]
        logger.info(f"First 5 POI names BEFORE clustering: {poi_names}")
        
        # Step 2: Cluster POIs into days
        clustered_pois = cluster_pois_by_day(pois, request.days)
        logger.info(f"Clustered POIs into {request.days} days")
        
        # Log POI names after clustering
        for day, day_pois in list(clustered_pois.items())[:2]:
            names = [poi.get('name', 'UNKNOWN') for poi in day_pois[:3]]
            logger.info(f"Day {day} POI names AFTER clustering: {names}")
        
        # Step 3: Balance clusters (5 POIs per day)
        balanced_clusters = balance_clusters(clustered_pois, request.days)
        
        # Step 4: Optimize route for each day using TSP
        itinerary = {}
        total_cost = 0
        
        for day_num, day_pois in balanced_clusters.items():
            # Optimize order of POIs for this day
            optimized_pois = optimize_daily_route(day_pois)
            
            # Convert to response format
            itinerary[f"day_{day_num}"] = [
                POI(
                    name=poi['name'],
                    type=poi.get('type', 'attraction'),
                    duration=poi.get('duration', 2),
                    cost=poi.get('cost', 0),
                    lat=poi.get('lat', 0.0),
                    lon=poi.get('lon', 0.0)
                )
                for poi in optimized_pois
            ]
            
            # Calculate day cost
            total_cost += sum(poi.get('cost', 0) for poi in optimized_pois)
            
            # Log warning if day has no POIs
            if len(optimized_pois) == 0:
                logger.warning(f"Day {day_num} has no POIs")
        
        # Step 5: Calculate budget prediction
        predicted_budget = predict_budget(pois, request.budget)
        
        # Create response matching ItineraryResponse schema
        response = ItineraryResponse(
            destination=request.destination,
            days=request.days,
            totalBudget=request.budget,
            estimatedCost=predicted_budget.get('estimated_cost', total_cost),
            greenSignal=predicted_budget.get('green_signal', True),
            dayByDay=[
                DayItinerary(
                    day=int(day.split('_')[1]),
                    date="",  # Will be calculated by frontend
                    pois=pois
                )
                for day, pois in itinerary.items()
            ]
        )
        
        logger.info(f"Successfully generated itinerary for {request.destination}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/get_pois")
async def get_pois(request: dict):
    """
    Get POIs for a city - used by destinations discovery page
    
    Request: { "destination": "Mumbai", "interests": [] }
    Returns: { "pois": [...], "city": "Mumbai", "count": 50 }
    """
    try:
        destination = request.get('destination', '')
        interests = request.get('interests', [])
        
        if not destination:
            raise HTTPException(status_code=400, detail="City name is required")
        
        logger.info(f"Fetching POIs for {destination}")
        
        # If no interests, get diverse selection
        if not interests:
            interests = ['museum', 'food', 'culture', 'nature', 'shopping', 'history']
        
        # Fetch POIs from OSM with caching (real data)
        pois = get_pois_for_destination(destination, interests, use_api=True)
        
        if not pois:
            logger.warning(f"No POIs found for {destination}")
            return {
                "pois": [],
                "city": destination,
                "count": 0
            }
        
        logger.info(f"Returning {len(pois)} POIs for {destination}")
        
        return {
            "pois": pois,
            "city": destination,
            "count": len(pois)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_pois: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Run with: uvicorn app.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
