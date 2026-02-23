"""
TSP (Traveling Salesman Problem) Routing Algorithm
Optimizes the visit order within each day to minimize travel distance
"""
import math


def haversine_distance(poi1: dict, poi2: dict) -> float:
    """
    Calculate distance between two POIs using Haversine formula
    
    Args:
        poi1: First POI with 'lat' and 'lon' keys
        poi2: Second POI with 'lat' and 'lon' keys
        
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1 = math.radians(poi1['lat'])
    lon1 = math.radians(poi1['lon'])
    lat2 = math.radians(poi2['lat'])
    lon2 = math.radians(poi2['lon'])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance


def nearest_neighbor_tsp(pois: list) -> list:
    """
    Optimize POI visit order using Nearest Neighbor heuristic
    Greedy algorithm that always visits the closest unvisited POI next
    
    Args:
        pois: List of POIs to order
        
    Returns:
        Ordered list of POIs minimizing total travel distance
    """
    if len(pois) <= 1:
        return pois
    
    # Handle POIs with no coordinates (default data)
    has_coords = all(poi.get('lat', 0) != 0 or poi.get('lon', 0) != 0 for poi in pois)
    if not has_coords:
        # Return as-is if no real coordinates
        return pois
    
    # Start with the first POI
    route = [pois[0]]
    remaining = pois[1:]
    
    # Greedily select nearest unvisited POI
    while remaining:
        last_poi = route[-1]
        
        # Find nearest POI from remaining
        nearest_poi = min(remaining, 
                         key=lambda p: haversine_distance(last_poi, p))
        
        # Add to route and remove from remaining
        route.append(nearest_poi)
        remaining.remove(nearest_poi)
    
    return route


def optimize_daily_route(pois: list) -> list:
    """
    Optimize route for a single day
    Wrapper function that can be extended with more sophisticated algorithms
    
    Args:
        pois: List of POIs for one day
        
    Returns:
        Optimized list of POIs
    """
    return nearest_neighbor_tsp(pois)


def calculate_total_distance(pois: list) -> float:
    """
    Calculate total travel distance for a route
    
    Args:
        pois: Ordered list of POIs
        
    Returns:
        Total distance in kilometers
    """
    if len(pois) <= 1:
        return 0.0
    
    total = 0.0
    for i in range(len(pois) - 1):
        total += haversine_distance(pois[i], pois[i+1])
    
    return round(total, 2)
