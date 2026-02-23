"""
Budget Prediction and Feasibility Check
Estimates total cost and determines if trip is within budget
"""


def predict_budget(pois: list, user_budget: float) -> dict:
    """
    Predict total cost and check budget feasibility
    
    Args:
        pois: List of all POIs for the trip
        user_budget: User's budget limit in USD
        
    Returns:
        Dictionary with 'estimated_cost' and 'green_signal' keys
        - estimated_cost: Total estimated cost including buffer
        - green_signal: True if within budget, False otherwise
    """
    # Sum up POI costs
    total_poi_cost = sum(poi.get('cost', 0) for poi in pois)
    
    # Add 20% buffer for:
    # - Meals not at POIs
    # - Transportation between POIs
    # - Miscellaneous expenses
    # - Tips and unexpected costs
    buffer_multiplier = 1.20
    estimated_cost = total_poi_cost * buffer_multiplier
    
    # Round to 2 decimal places
    estimated_cost = round(estimated_cost, 2)
    
    # Determine feasibility (green signal)
    # Green = within budget, Red = over budget
    green_signal = estimated_cost <= user_budget
    
    return {
        'estimated_cost': estimated_cost,
        'green_signal': green_signal
    }


def calculate_budget_breakdown(pois_by_day: dict) -> dict:
    """
    Calculate budget breakdown by day
    
    Args:
        pois_by_day: Dictionary mapping day number to POI list
        
    Returns:
        Dictionary mapping day number to daily cost
    """
    breakdown = {}
    
    for day, pois in pois_by_day.items():
        daily_cost = sum(poi.get('cost', 0) for poi in pois)
        breakdown[day] = round(daily_cost, 2)
    
    return breakdown


def optimize_budget(pois: list, user_budget: float, max_cost_per_day: float = None) -> list:
    """
    Optimize POI selection to fit within budget
    Removes most expensive POIs if over budget
    
    Args:
        pois: List of POIs
        user_budget: User's budget limit
        max_cost_per_day: Optional maximum cost per day
        
    Returns:
        Optimized list of POIs within budget
    """
    # Check if already within budget
    budget_info = predict_budget(pois, user_budget)
    if budget_info['green_signal']:
        return pois
    
    # Sort POIs by cost (descending)
    sorted_pois = sorted(pois, key=lambda p: p.get('cost', 0), reverse=True)
    
    # Remove expensive POIs until within budget
    optimized = sorted_pois.copy()
    while optimized and not predict_budget(optimized, user_budget)['green_signal']:
        # Remove most expensive POI
        optimized.pop(0)
    
    return optimized
