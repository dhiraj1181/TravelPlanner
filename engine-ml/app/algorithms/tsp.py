"""
TSP (Traveling Salesman Problem) Routing Algorithm
Optimizes visit order within each day to minimize travel distance.

Two-phase approach:
  Phase 1 — Nearest Neighbour: Fast greedy start (~1ms for ≤10 POIs)
  Phase 2 — 2-Opt improvement: Removes route crossings/zigzags
             Tries every edge pair and reverses segments that shorten the route.
             Eliminates the "star" patterns seen with NN alone.
"""
import math
import logging

logger = logging.getLogger(__name__)


def haversine_distance(poi1: dict, poi2: dict) -> float:
    """
    Calculate distance between two POIs using Haversine formula.
    Returns distance in kilometres.
    """
    R = 6371.0
    lat1 = math.radians(poi1['lat'])
    lon1 = math.radians(poi1['lon'])
    lat2 = math.radians(poi2['lat'])
    lon2 = math.radians(poi2['lon'])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def nearest_neighbor_tsp(pois: list) -> list:
    """
    Phase 1: Greedy nearest-neighbour starting from the best candidate.
    Tries every POI as the starting point and keeps the shortest result.
    This multi-start approach avoids the worst-case NN routes where a bad
    starting POI forces long backtracking.
    """
    if len(pois) <= 1:
        return pois

    best_route = None
    best_dist = float('inf')

    for start_idx in range(len(pois)):
        route = [pois[start_idx]]
        remaining = [p for i, p in enumerate(pois) if i != start_idx]

        while remaining:
            last = route[-1]
            nearest = min(remaining, key=lambda p: haversine_distance(last, p))
            route.append(nearest)
            remaining.remove(nearest)

        dist = calculate_total_distance(route)
        if dist < best_dist:
            best_dist = dist
            best_route = route

    return best_route


def two_opt_improve(route: list) -> list:
    """
    Phase 2: 2-opt improvement — removes crossing edges.

    For every pair of edges (i→i+1) and (k→k+1), test whether reversing
    the segment between them shortens the route. If yes, keep the reversal.
    Repeat until no improvement is found.

    Time complexity: O(n² × passes) — negligible for n ≤ 10 POIs/day.
    Typical improvement: 10-30% additional over nearest-neighbour alone,
    and completely eliminates the zigzag/star patterns.
    """
    if len(route) <= 3:
        return route

    best = route[:]
    improved = True

    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for k in range(i + 1, len(best)):
                # Reverse the segment between i and k
                new_route = best[:i] + best[i:k + 1][::-1] + best[k + 1:]
                if calculate_total_distance(new_route) < calculate_total_distance(best):
                    best = new_route
                    improved = True
                    break          # Restart inner loop after any improvement
            if improved:
                break              # Restart outer loop too

    return best


def optimize_daily_route(pois: list) -> list:
    """
    Full optimized route for one day:
      1. Multi-start nearest-neighbour (best of N starting points)
      2. 2-opt improvement pass (removes all crossing edges)

    For 5 POIs this runs in < 2ms and typically gives routes within
    5% of the true optimum.
    """
    if len(pois) <= 1:
        return pois

    # Check coords are present
    if not all(poi.get('lat') and poi.get('lon') for poi in pois):
        return pois

    before_dist = calculate_total_distance(pois)

    # Phase 1: multi-start nearest neighbour
    nn_route = nearest_neighbor_tsp(pois)
    nn_dist = calculate_total_distance(nn_route)

    # Phase 2: 2-opt improvement
    optimized = two_opt_improve(nn_route)
    after_dist = calculate_total_distance(optimized)

    saved = round(before_dist - after_dist, 2)
    saved_pct = round(saved / before_dist * 100, 1) if before_dist > 0 else 0
    logger.info(
        f"TSP: {len(pois)} POIs | before={before_dist:.1f}km "
        f"after={after_dist:.1f}km | saved {saved}km ({saved_pct}%)"
    )

    return optimized


def calculate_total_distance(pois: list) -> float:
    """Calculate total travel distance (km) for an ordered route."""
    if len(pois) <= 1:
        return 0.0
    total = sum(haversine_distance(pois[i], pois[i + 1]) for i in range(len(pois) - 1))
    return round(total, 2)
