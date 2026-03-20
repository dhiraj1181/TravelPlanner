"""
Combined test — verifies TSP 2-opt AND cluster radius guard.
Run: python test_optimizations.py
"""
from app.algorithms.tsp import optimize_daily_route, calculate_total_distance
from app.algorithms.clustering import cluster_pois_by_day, MAX_DAY_RADIUS, _haversine, _centroid

# ─── Test 1: TSP 2-opt removes the zigzag ────────────────────────────────────
print("=" * 55)
print("TEST 1: TSP 2-Opt improvement")
print("=" * 55)

# Arrange POIs so naive order creates obvious crossings
zigzag = [
    {"name": "A - South",      "lat": 23.30, "lon": 85.31},  # south
    {"name": "B - North",      "lat": 23.40, "lon": 85.30},  # north  (cross a→b crosses c→d)
    {"name": "C - South-East", "lat": 23.31, "lon": 85.40},  # south-east
    {"name": "D - North-West", "lat": 23.39, "lon": 85.20},  # north-west
    {"name": "E - Centre",     "lat": 23.35, "lon": 85.31},  # centre
]

before = calculate_total_distance(zigzag)
optimized = optimize_daily_route(zigzag)
after = calculate_total_distance(optimized)

print(f"Before: {before:.2f} km")
print(f"After:  {after:.2f} km")
print(f"Saved:  {round(before - after, 2):.2f} km ({round((before-after)/before*100,1)}%)")
print("Route:", " → ".join(p["name"] for p in optimized))
assert after <= before, "2-opt must not make the route longer!"
print("PASS ✅\n")

# ─── Test 2: Radius guard moves remote POI ───────────────────────────────────
print("=" * 55)
print("TEST 2: Cluster radius guard (68km outlier case)")
print("=" * 55)

# Simulate what happened: Morabadi (city) + Rajrappa (68km away) on same day
city_pois = [
    {"name": "Morabadi Museum", "lat": 23.370, "lon": 85.321, "osm_id": "1"},
    {"name": "Tagore Hill",     "lat": 23.355, "lon": 85.304, "osm_id": "2"},
    {"name": "Rock Garden",     "lat": 23.383, "lon": 85.333, "osm_id": "3"},
    {"name": "Rajrappa Temple", "lat": 23.650, "lon": 85.750, "osm_id": "4"},  # 68km away!
    {"name": "Birsa Zoo",       "lat": 23.319, "lon": 85.282, "osm_id": "5"},
    {"name": "Jagannath Temple","lat": 23.344, "lon": 85.310, "osm_id": "6"},
]

clustered = cluster_pois_by_day(city_pois, num_days=2)

print("Cluster results after radius guard:")
for day, pois in clustered.items():
    c = _centroid(pois)
    max_dist = max(_haversine(p["lat"], p["lon"], c[0], c[1]) for p in pois)
    names = [p["name"] for p in pois]
    print(f"  Day {day}: {names}")
    print(f"           Max dist from centroid: {max_dist:.1f} km (limit={MAX_DAY_RADIUS}km)")
    assert max_dist <= MAX_DAY_RADIUS + 5, f"Day {day} still has outlier POI {max_dist:.1f}km away!"

print("PASS ✅")
