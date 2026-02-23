"""
POI Clustering Algorithm using K-means
Groups POIs into daily clusters based on geographic proximity
"""
from sklearn.cluster import KMeans
import numpy as np


def cluster_pois_by_day(pois: list, num_days: int) -> dict:
    """
    Cluster POIs into daily groups using K-means clustering
    
    Args:
        pois: List of POI dictionaries with 'lat' and 'lon' keys
        num_days: Number of days to cluster into
        
    Returns:
        Dictionary mapping day number (1-indexed) to list of POIs
        Example: {1: [poi1, poi2], 2: [poi3, poi4], ...}
    """
    if not pois:
        return {}
    
    # Handle edge case: more days than POIs
    if num_days >= len(pois):
        # One POI per day
        clustered = {}
        for i, poi in enumerate(pois):
            day = i + 1
            clustered[day] = [poi]
        return clustered
    
    # Handle edge case: only one day
    if num_days == 1:
        return {1: pois}
    
    # Extract coordinates for clustering
    coordinates = np.array([[poi['lat'], poi['lon']] for poi in pois])
    
    # Apply K-means clustering
    # n_clusters = number of days
    # random_state for reproducibility
    kmeans = KMeans(n_clusters=num_days, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coordinates)
    
    # Group POIs by cluster label (day)
    clustered_pois = {}
    for i, poi in enumerate(pois):
        day = int(labels[i]) + 1  # Convert 0-indexed to 1-indexed
        if day not in clustered_pois:
            clustered_pois[day] = []
        clustered_pois[day].append(poi)
    
    # Ensure all days have at least one POI
    # If a day has no POIs, borrow from the largest cluster
    for day in range(1, num_days + 1):
        if day not in clustered_pois or len(clustered_pois[day]) == 0:
            # Find day with most POIs
            max_day = max(clustered_pois.keys(), key=lambda d: len(clustered_pois[d]))
            # Move one POI to the empty day
            if len(clustered_pois[max_day]) > 1:
                poi_to_move = clustered_pois[max_day].pop()
                clustered_pois[day] = [poi_to_move]
    
    return clustered_pois


def balance_clusters(clustered_pois: dict, target_per_day: int = 4) -> dict:
    """
    Balance POI distribution across days
    Ensures each day has roughly the same number of POIs
    
    Args:
        clustered_pois: Dictionary of day -> POI list
        target_per_day: Target number of POIs per day
        
    Returns:
        Balanced dictionary of day -> POI list
    """
    # Find days with too many POIs
    for day in clustered_pois:
        while len(clustered_pois[day]) > target_per_day + 1:
            # Find day with fewest POIs
            min_day = min(clustered_pois.keys(), 
                         key=lambda d: len(clustered_pois[d]))
            
            # Don't move if it would make min_day too large
            if len(clustered_pois[min_day]) >= target_per_day:
                break
            
            # Move one POI from current day to min_day
            poi_to_move = clustered_pois[day].pop()
            clustered_pois[min_day].append(poi_to_move)
    
    return clustered_pois
