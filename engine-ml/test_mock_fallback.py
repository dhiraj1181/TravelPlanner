from app.algorithms.ranking import rank_and_filter_pois
from app.data.poi_data import _get_pois_from_mock

pois = _get_pois_from_mock('ranchi', ['nature', 'culture'])
print(f"Mock POIs loaded: {len(pois)}")
print("All have osm_id:", all('osm_id' in p for p in pois))

result = rank_and_filter_pois(pois, keep_top_n=5)
print(f"Ranked {len(result)} POIs:")
for p in result:
    print(f"  - {p['name']} ({p['type']})")
