"""
Test that the optimised Overpass query actually fetches Ranchi POIs.
Run: python test_overpass_speed.py
"""
import time
from app.services.osm_service import get_osm_service, OVERPASS_MIRRORS

osm = get_osm_service()

# Show the query we'll send
from app.services.osm_service import INTEREST_TAG_MAP
tags = []
for interest in ['museum', 'culture', 'nature', 'adventure']:
    tags.extend(INTEREST_TAG_MAP[interest])

query = osm._build_overpass_query(23.3569, 85.3243, 50000, tags)
line_count = query.count('\n')
nwr_count  = query.count('nwr[')
print(f"Query stats: {nwr_count} nwr sub-queries, {line_count} lines")
print(f"First 3 lines:\n{chr(10).join(query.split(chr(10))[:4])}")
print()

# Now actually fetch
print("Fetching from Overpass (testing mirror order)...")
t0 = time.time()
pois = osm.fetch_pois_for_city('ranchi', ['museum', 'culture', 'nature'], radius_km=50, limit=50)
elapsed = round(time.time() - t0, 1)
print(f"\nResult: {len(pois)} POIs in {elapsed}s")
if pois:
    print("Sample POIs:")
    for p in pois[:5]:
        print(f"  - {p['name']} ({p['type']}) @ ({p['lat']:.4f}, {p['lon']:.4f})")
