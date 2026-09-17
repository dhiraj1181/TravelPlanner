"""
POI Clustering Algorithm — Agglomerative (Haversine-distance) Clustering
=========================================================================

WHY NOT K-MEANS
---------------
K-means clusters on raw (lat, lon) degrees.  Because 1° longitude ≠ 1° latitude
in kilometres (longitude degrees shrink toward the poles), K-means treats the
coordinate space as uniform Euclidean, which it is not.  The result: clusters
that look tight in (lat, lon) space can still span 60–80 km of real travel
distance per day — exactly the bug reported in the itinerary.

WHAT WE USE INSTEAD
-------------------
AgglomerativeClustering with a **pre-computed Haversine distance matrix** and
``linkage='complete'``.  Complete linkage minimises the *maximum* pairwise
distance inside each cluster, so it naturally produces the most geographically
compact day-groups possible given the POI set.

THREE-PHASE PIPELINE
--------------------
  Phase 1 — Agglomerative clustering on real km distances
  Phase 2 — Radius guard: any POI > MAX_DAY_RADIUS km from its day centroid
             is reassigned to the nearest other day
  Phase 3 — Category diversification: swap POIs between days so that no day
             is dominated (>60%) by a single POI type
"""
from sklearn.cluster import AgglomerativeClustering
from geopy.distance import geodesic
import numpy as np
import math
import logging

logger = logging.getLogger(__name__)

# Hard limit: a single day's POIs must all sit within this radius of the
# day's centroid.  30 km is roughly 1-hour drive in Indian city traffic.
MAX_DAY_RADIUS = 25.0

# POIs per day target used by balance_clusters()
_DEFAULT_TARGET_PER_DAY = 4


# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km between two coordinate pairs."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(min(a, 1.0)))


def _centroid(pois: list) -> tuple:
    """(lat, lon) arithmetic centroid of a POI list."""
    if not pois:
        return (0.0, 0.0)
    return (
        sum(p['lat'] for p in pois) / len(pois),
        sum(p['lon'] for p in pois) / len(pois),
    )


def _build_distance_matrix(pois: list) -> np.ndarray:
    """
    Build a symmetric N×N matrix of real Haversine distances (km).
    This is what AgglomerativeClustering will use instead of raw coordinates.
    """
    n = len(pois)
    D = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            d = _haversine(pois[i]['lat'], pois[i]['lon'],
                           pois[j]['lat'], pois[j]['lon'])
            D[i, j] = D[j, i] = d
    return D


# ───────────────────────────────────────────────────────────────────────────────
# PHASE 1 — Pre-processing: Geofence Outlier Purge
# ───────────────────────────────────────────────────────────────────────────────

def remove_outliers(
    places: list,
    city_lat: float,
    city_lon: float,
    max_radius_km: float = 25.0,
) -> list:
    """
    Geofence filter: drop any POI whose geodesic distance from the city
    geocentre exceeds max_radius_km.

    Uses ``geopy.distance.geodesic`` (Vincenty ellipsoid model) which is
    more accurate than a pure haversine for distances > 10 km.

    Args:
        places:        List of POI dicts, each with 'lat' and 'lon'.
        city_lat:      Geocentre latitude  (from Nominatim / offline DB).
        city_lon:      Geocentre longitude.
        max_radius_km: Hard cutoff in km (default 25 km ≈ 1-hour drive radius).

    Returns:
        Filtered list with only in-bounds POIs.
    """
    city_point = (city_lat, city_lon)
    kept, dropped = [], 0

    for poi in places:
        try:
            dist_km = geodesic(city_point, (poi['lat'], poi['lon'])).km
        except Exception:
            # Malformed coordinate — keep POI, let clustering deal with it
            kept.append(poi)
            continue

        if dist_km <= max_radius_km:
            kept.append(poi)
        else:
            dropped += 1
            logger.debug(
                f"Outlier purged: '{poi.get('name')}' "
                f"at {dist_km:.1f} km from city centre"
            )

    if dropped:
        logger.info(
            f"remove_outliers: kept {len(kept)}/{len(kept)+dropped} POIs "
            f"(≤{max_radius_km} km from geocentre); dropped {dropped} outliers"
        )
    return kept


# ───────────────────────────────────────────────────────────────────────────────
# PHASE 2 — Post-processing: Geographical Day Sorter
# ───────────────────────────────────────────────────────────────────────────────

def sort_days_geographically(clustered_pois: dict) -> dict:
    """
    Reorder day numbers so that:
      • Day 1 = the cluster whose centroid is CLOSEST to the global POI centre
      • Day 2 = next closest … Day N = furthest

    This eliminates the random cluster-ID assignment from Agglomerative
    Clustering and gives the user a logical "start central, explore outward"
    itinerary structure.

    Algorithm:
      1. Compute each day's centroid  (lat, lon).
      2. Compute global centre        (mean of all centroids).
      3. Sort days by geodesic distance from global centre (asc).
      4. Remap old day keys → new sequential day numbers 1 … N.

    Args:
        clustered_pois: {old_day_id: [poi, ...], ...}

    Returns:
        New dict {1: [poi,...], 2: [...], ...} with days sorted geo-logically.
    """
    if not clustered_pois:
        return {}

    # Step 1 — compute centroids
    day_centroids: list[tuple] = []   # (old_day_id, lat, lon)
    for day_id, pois in clustered_pois.items():
        if not pois:
            continue
        c_lat = sum(p['lat'] for p in pois) / len(pois)
        c_lon = sum(p['lon'] for p in pois) / len(pois)
        day_centroids.append((day_id, c_lat, c_lon))

    # Step 2 — global centre (mean of centroids)
    global_lat = sum(c[1] for c in day_centroids) / len(day_centroids)
    global_lon = sum(c[2] for c in day_centroids) / len(day_centroids)
    global_pt  = (global_lat, global_lon)

    # Step 3 — sort by geodesic distance from global centre
    def _dist_from_centre(entry):
        _, c_lat, c_lon = entry
        try:
            return geodesic(global_pt, (c_lat, c_lon)).km
        except Exception:
            return float('inf')

    sorted_centroids = sorted(day_centroids, key=_dist_from_centre)

    # Step 4 — build old_day_id → new_day_num mapping
    id_to_new_day = {
        old_id: new_day
        for new_day, (old_id, _, _) in enumerate(sorted_centroids, start=1)
    }

    # Log the remapping for debugging
    for old_id, new_day in id_to_new_day.items():
        _, c_lat, c_lon = next(c for c in day_centroids if c[0] == old_id)
        dist = _dist_from_centre((old_id, c_lat, c_lon))
        logger.info(
            f"Day sort: cluster {old_id} → Day {new_day} "
            f"(centroid {c_lat:.4f},{c_lon:.4f}, "
            f"{dist:.1f} km from global centre)"
        )

    # Step 5 — rebuild dict with new day numbers
    sorted_clustered: dict = {}
    for old_id, pois in clustered_pois.items():
        new_day = id_to_new_day.get(old_id, old_id)
        sorted_clustered[new_day] = pois

    return dict(sorted(sorted_clustered.items()))


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Agglomerative clustering
# ─────────────────────────────────────────────────────────────────────────────

def _agglomerative_cluster(pois: list, num_days: int) -> dict:
    """
    Group POIs into num_days clusters using Agglomerative Clustering on
    a pre-computed Haversine distance matrix.

    ``linkage='complete'`` (= maximum-linkage) minimises the largest pairwise
    distance inside each cluster → geographically tight day-groups.

    Returns a dict {day_number (1-indexed): [poi, ...]}
    """
    D = _build_distance_matrix(pois)

    model = AgglomerativeClustering(
        n_clusters=num_days,
        metric='precomputed',
        linkage='complete',   # minimise max intra-cluster distance
    )
    labels = model.fit_predict(D)

    clustered: dict = {}
    for i, poi in enumerate(pois):
        day = int(labels[i]) + 1   # 1-indexed
        clustered.setdefault(day, []).append(poi)

    # Log intra-cluster diameters so we can verify improvement
    for day, day_pois in clustered.items():
        if len(day_pois) < 2:
            continue
        max_d = max(
            _haversine(a['lat'], a['lon'], b['lat'], b['lon'])
            for i, a in enumerate(day_pois)
            for b in day_pois[i + 1:]
        )
        logger.info(f"Cluster Day {day}: {len(day_pois)} POIs, max spread = {max_d:.1f} km")

    return clustered


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Radius guard
# ─────────────────────────────────────────────────────────────────────────────

def _apply_radius_guard(clustered_pois: dict) -> dict:
    """
    Scans every POI.  If it sits > MAX_DAY_RADIUS km from its day's centroid,
    it is moved to the day whose centroid it is closest to.
    Runs up to 3 passes so cascading reassignments can settle.
    """
    for _pass in range(3):
        moved = 0
        for day in list(clustered_pois.keys()):
            c_lat, c_lon = _centroid(clustered_pois[day])
            outliers = [
                p for p in clustered_pois[day]
                if _haversine(p['lat'], p['lon'], c_lat, c_lon) > MAX_DAY_RADIUS
            ]
            for poi in outliers:
                if len(clustered_pois[day]) <= 1:
                    break  # Never leave a day completely empty

                # Find the best alternative day (nearest centroid)
                best_day, best_dist = day, float('inf')
                for other_day, other_pois in clustered_pois.items():
                    if other_day == day:
                        continue
                    oc_lat, oc_lon = _centroid(other_pois)
                    dist = _haversine(poi['lat'], poi['lon'], oc_lat, oc_lon)
                    if dist < best_dist:
                        best_dist = dist
                        best_day = other_day

                if best_day != day:
                    clustered_pois[day].remove(poi)
                    clustered_pois[best_day].append(poi)
                    moved += 1
                    logger.info(
                        f"Radius guard: moved '{poi.get('name')}' "
                        f"day {day} → day {best_day} "
                        f"({best_dist:.1f} km from new centroid)"
                    )
        if moved == 0:
            break

    return clustered_pois


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def cluster_pois_by_day(pois: list, num_days: int) -> dict:
    """
    Cluster POIs into geographically tight daily groups.

    Pipeline:
      1. Agglomerative clustering on Haversine distance matrix
         (complete linkage = minimise max intra-cluster distance)
      2. Radius guard — move outlier POIs to closer days
      3. Ensure every day has ≥ 1 POI

    Args:
        pois:     List of POI dicts (must have 'lat', 'lon' keys)
        num_days: Number of days to group into

    Returns:
        {1: [poi, ...], 2: [...], ...}  (1-indexed day numbers)
    """
    if not pois:
        return {}

    if num_days >= len(pois):
        return {i + 1: [poi] for i, poi in enumerate(pois)}

    if num_days == 1:
        return {1: list(pois)}

    # ── Phase 1: Agglomerative clustering ────────────────────────────────────
    clustered_pois = _agglomerative_cluster(pois, num_days)

    # ── Ensure every requested day slot has at least one POI ─────────────────
    for day in range(1, num_days + 1):
        if day not in clustered_pois or len(clustered_pois[day]) == 0:
            max_day = max(clustered_pois, key=lambda d: len(clustered_pois[d]))
            if len(clustered_pois[max_day]) > 1:
                clustered_pois[day] = [clustered_pois[max_day].pop()]

    # ── Phase 2: Radius guard ─────────────────────────────────────────────────
    clustered_pois = _apply_radius_guard(clustered_pois)

    return clustered_pois


def balance_clusters(clustered_pois: dict,
                     target_per_day: int = _DEFAULT_TARGET_PER_DAY) -> dict:
    """
    Move excess POIs from over-full days to under-full days.
    Moves are done in geo-distance order: the POI closest to the receiving
    day's centroid is moved first, preserving spatial coherence.

    Args:
        clustered_pois: Day → POI list
        target_per_day: Desired POI count per day

    Returns:
        Rebalanced dict
    """
    for day in list(clustered_pois.keys()):
        while len(clustered_pois[day]) > target_per_day:
            min_day = min(clustered_pois, key=lambda d: len(clustered_pois[d]))
            if len(clustered_pois[min_day]) >= len(clustered_pois[day]) - 1:
                break  # Already balanced enough

            # Pick the POI from `day` that is closest to min_day's centroid
            mc_lat, mc_lon = _centroid(clustered_pois[min_day])
            poi_to_move = min(
                clustered_pois[day],
                key=lambda p: _haversine(p['lat'], p['lon'], mc_lat, mc_lon)
            )
            clustered_pois[day].remove(poi_to_move)
            clustered_pois[min_day].append(poi_to_move)

    return clustered_pois


def diversify_by_category(clustered_pois: dict, max_passes: int = 3) -> dict:
    """
    Post-clustering diversity pass.

    K-Means (now Agglomerative) groups POIs by geography, which can put all
    temples on Day 1 and all parks on Day 2.  This function detects
    category-dominated days and swaps POIs between days to ensure every day
    has a category mix, while trying to keep the swap geographically sensible
    (prefer swapping POIs that are close to the receiving day's centroid).

    Algorithm (runs up to max_passes times):
      1. For each day, find the over-represented category (dominant)
      2. Find another day dominated by a DIFFERENT category
      3. Swap one POI from each — improving both days' diversity
      4. Repeat until no more beneficial swaps exist

    Args:
        clustered_pois: Day → POI list
        max_passes:     Swap iterations

    Returns:
        More category-diverse clustered_pois dict
    """

    def get_category_counts(day_pois):
        counts: dict = {}
        for p in day_pois:
            cat = p.get('type', 'culture')
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def dominant_category(counts):
        if not counts:
            return None, 0
        return max(counts.items(), key=lambda x: x[1])

    swaps_total = 0
    for pass_num in range(max_passes):
        swaps_this_pass = 0
        days = list(clustered_pois.keys())

        for day_a in days:
            pois_a = clustered_pois[day_a]
            if len(pois_a) < 2:
                continue

            counts_a = get_category_counts(pois_a)
            dom_cat_a, dom_count_a = dominant_category(counts_a)

            # Only act if >60% of the day is one category
            if dom_count_a / len(pois_a) <= 0.6:
                continue

            # Candidate to swap out: dominant category, closest to day_a centroid
            c_lat_a, c_lon_a = _centroid(pois_a)
            swap_out_candidates = [p for p in pois_a if p.get('type') == dom_cat_a]
            if not swap_out_candidates:
                continue
            swap_out = min(
                swap_out_candidates,
                key=lambda p: _haversine(p['lat'], p['lon'], c_lat_a, c_lon_a)
            )

            best_day_b = None
            best_swap_in = None
            best_geo_score = float('inf')

            for day_b in days:
                if day_b == day_a:
                    continue
                pois_b = clustered_pois[day_b]
                if len(pois_b) < 2:
                    continue

                counts_b = get_category_counts(pois_b)
                dom_cat_b, dom_count_b = dominant_category(counts_b)

                if dom_cat_b == dom_cat_a:
                    continue
                if dom_count_b / len(pois_b) <= 0.6:
                    continue

                c_lat_b, c_lon_b = _centroid(pois_b)
                swap_in_candidates = [p for p in pois_b if p.get('type') == dom_cat_b]
                if not swap_in_candidates:
                    continue

                # Choose the swap_in POI closest to day_a's centroid
                swap_in = min(
                    swap_in_candidates,
                    key=lambda p: _haversine(p['lat'], p['lon'], c_lat_a, c_lon_a)
                )
                geo_score = _haversine(swap_in['lat'], swap_in['lon'], c_lat_a, c_lon_a)

                if geo_score < best_geo_score:
                    best_geo_score = geo_score
                    best_day_b = day_b
                    best_swap_in = swap_in

            if best_day_b and best_swap_in:
                clustered_pois[day_a].remove(swap_out)
                clustered_pois[best_day_b].remove(best_swap_in)
                clustered_pois[day_a].append(best_swap_in)
                clustered_pois[best_day_b].append(swap_out)
                swaps_this_pass += 1

        swaps_total += swaps_this_pass
        logger.info(f"Diversity pass {pass_num + 1}: {swaps_this_pass} swaps done")
        if swaps_this_pass == 0:
            break

    logger.info(
        f"Category diversification complete: {swaps_total} total swaps "
        f"across {max_passes} passes"
    )
    return clustered_pois
