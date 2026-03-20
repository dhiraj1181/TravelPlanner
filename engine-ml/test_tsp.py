"""
Quick test to verify TSP route optimization is working.
Run: python test_tsp.py
"""
from app.algorithms.tsp import nearest_neighbor_tsp, calculate_total_distance

# 5 real Ranchi POIs -- intentionally in a "bad" order
pois = [
    {"name": "Jagannath Temple", "lat": 23.3441, "lon": 85.3096},  # Old city (centre)
    {"name": "Hundru Falls",     "lat": 23.4503, "lon": 85.6003},  # Far east  (40 km away)
    {"name": "Tagore Hill",      "lat": 23.3551, "lon": 85.3044},  # Near temple (2 km)
    {"name": "Birsa Zoo",        "lat": 23.3193, "lon": 85.2817},  # West
    {"name": "Rock Garden",      "lat": 23.3832, "lon": 85.3328},  # North
]

before_dist = calculate_total_distance(pois)
optimized   = nearest_neighbor_tsp(pois)
after_dist  = calculate_total_distance(optimized)

print("=== BEFORE TSP (original random order) ===")
for i, p in enumerate(pois):
    arrow = " ->" if i < len(pois) - 1 else ""
    print(f"  {i+1}. {p['name']}{arrow}")
print(f"  Total travel: {before_dist} km\n")

print("=== AFTER TSP (optimized route) ===")
for i, p in enumerate(optimized):
    arrow = " ->" if i < len(optimized) - 1 else ""
    print(f"  {i+1}. {p['name']}{arrow}")
print(f"  Total travel: {after_dist} km\n")

saved_km  = round(before_dist - after_dist, 2)
saved_pct = round((before_dist - after_dist) / before_dist * 100, 1)
print(f"  Saved: {saved_km} km ({saved_pct}% less walking/driving)")
print()

# Sanity checks
assert len(optimized) == len(pois), "TSP must return same number of POIs"
assert after_dist <= before_dist,   "TSP must not make the route longer"
print("All assertions passed - TSP is working correctly!")
