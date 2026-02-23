"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List


class POI(BaseModel):
    """Point of Interest - A place to visit"""
    name: str
    type: str
    cost: float
    duration: int  # hours
    lat: float
    lon: float


class DayItinerary(BaseModel):
    """Itinerary for one day"""
    day: int
    date: str
    pois: List[POI]


class ItineraryRequest(BaseModel):
    """Request payload from Spring Boot backend"""
    destination: str = Field(..., description="Destination city/country")
    days: int = Field(..., gt=0, le=14, description="Number of days (1-14)")
    budget: float = Field(..., gt=0, description="Budget in USD")
    interests: List[str] = Field(..., min_length=1, description="List of user interests")
    
    class Config:
        json_schema_extra = {
            "example": {
                "destination": "Paris",
                "days": 3,
                "budget": 1500,
                "interests": ["museum", "food", "culture"]
            }
        }


class ItineraryResponse(BaseModel):
    """Response payload to Spring Boot backend"""
    destination: str
    days: int
    totalBudget: float
    estimatedCost: float
    greenSignal: bool  # True if within budget
    dayByDay: List[DayItinerary]
    
    class Config:
        json_schema_extra = {
            "example": {
                "destination": "Paris",
                "days": 3,
                "totalBudget": 1500,
                "estimatedCost": 1320.50,
                "greenSignal": True,
                "dayByDay": [
                    {
                        "day": 1,
                        "date": "2025-07-01",
                        "pois": [
                            {
                                "name": "Louvre Museum",
                                "type": "museum",
                                "cost": 17.0,
                                "duration": 3,
                                "lat": 48.8606,
                                "lon": 2.3376
                            }
                        ]
                    }
                ]
            }
        }
