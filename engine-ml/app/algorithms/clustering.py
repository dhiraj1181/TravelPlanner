"""
POI Clustering Algorithm using K-means
Groups POIs into daily clusters based on geographic proximity.

Two-phase approach:
  Phase 1 — K-Means clusters POIs geographically into N day-groups
  Phase 2 — Radius guard: if any POI is > MAX_DAY_RADIUS km from its
             cluster centroid, it's reassigned to its nearest viable cluster.
             Prevents remote POIs (e.g. Rajrappa, 68km away) being placed
             on the same day as city-centre attractions.
"""
from sklearn.cluster import KMeans
import numpy as np
import math
import logging

logger = logging.getLogger(__name__)

# Maximum acceptable km radius for a single day's cluster.
# POIs beyond this from their centroid are reassigned.
MAX_DAY_RADIUS = 30.0


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Fast haversine distance in km between two coordinate pairs."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _centroid(pois: list) -> tuple:
    """Return (lat, lon) centroid of a list of POIs."""
    if not pois:
        return (0.0, 0.0)
    return (sum(p['lat'] for p in pois) / len(pois),
            sum(p['lon'] for p in pois) / len(pois))


def _apply_radius_guard(clustered_pois: dict) -> dict:
    """
    Radius guard (Phase 2):
    Scans every POI. If it is > MAX_DAY_RADIUS km from its day's centroid,
    it is moved to the day whose centroid it is closest to.
    Runs up to 3 passes so cascading reassignments settle.
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
                    break  # Never empty a day
                # Find best alternative day
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
                        f"from day {day} → day {best_day} "
                        f"(was {best_dist:.1f}km from centroid)"
                    )
        if moved == 0:
            break
    return clustered_pois


def cluster_pois_by_day(pois: list, num_days: int) -> dict:
    """
    Cluster POIs into daily groups using K-means + radius guard.

    Args:
        pois: List of POI dictionaries with 'lat' and 'lon' keys
        num_days: Number of days to cluster into

    Returns:
        Dictionary mapping day number (1-indexed) to list of POIs
    """
    if not pois:
        return {}

    if num_days >= len(pois):
        return {i + 1: [poi] for i, poi in enumerate(pois)}

    if num_days == 1:
        return {1: pois}

    # ── Phase 1: K-Means ─────────────────────────────────────────────────
    coordinates = np.array([[poi['lat'], poi['lon']] for poi in pois])
    kmeans = KMeans(n_clusters=num_days, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coordinates)

    clustered_pois = {}
    for i, poi in enumerate(pois):
        day = int(labels[i]) + 1
        clustered_pois.setdefault(day, []).append(poi)

    # Ensure every day has at least one POI
    for day in range(1, num_days + 1):
        if day not in clustered_pois or len(clustered_pois[day]) == 0:
            max_day = max(clustered_pois.keys(), key=lambda d: len(clustered_pois[d]))
            if len(clustered_pois[max_day]) > 1:
                clustered_pois[day] = [clustered_pois[max_day].pop()]

    # ── Phase 2: Radius guard — reassign remote outlier POIs ─────────────
    clustered_pois = _apply_radius_guard(clustered_pois)

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
    # Move excess POIs from over-full days to under-full days
    for day in list(clustered_pois.keys()):
        while len(clustered_pois[day]) > target_per_day:
            # Find shortest day
            min_day = min(clustered_pois.keys(),
                         key=lambda d: len(clustered_pois[d]))
            # Only move if it would actually help (min_day is shorter)
            if len(clustered_pois[min_day]) >= len(clustered_pois[day]) - 1:
                break
            poi_to_move = clustered_pois[day].pop(0)  # Move from front to keep geo order
            clustered_pois[min_day].append(poi_to_move)
    
    return clustered_pois


def diversify_by_category(clustered_pois: dict, max_passes: int = 3) -> dict:
    """
    Post-clustering diversity pass.
    
    K-Means groups POIs by geography, which can put all temples on Day 1
    and all parks on Day 2. This function detects category-dominated days
    and swaps POIs between days to ensure every day has a category mix.
    
    Algorithm (runs up to max_passes times):
        1. For each day, find the over-represented category (dominant)
        2. Find another day that has excess of a DIFFERENT category
        3. Swap one POI from each — improving both days' diversity
        4. Repeat until no more beneficial swaps exist
    
    Args:
        clustered_pois: Day → POI list from K-Means + balance_clusters
        max_passes:     Number of swap iterations (more = more diverse)
    
    Returns:
        More category-diverse clustered_pois dict
    """
    import logging
    logger = logging.getLogger(__name__)

    def get_category_counts(day_pois):
        counts = {}
        for p in day_pois:
            cat = p.get('type', 'culture')
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def dominant_category(counts):
        """Return (category, count) of the most-represented type."""
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

            # Find a candidate POI from day_a to swap out (dominant category)
            swap_out = next(
                (p for p in reversed(pois_a) if p.get('type') == dom_cat_a),
                None
            )
            if not swap_out:
                continue

            # Find another day that has excess of a DIFFERENT category
            best_day_b = None
            best_swap_in = None

            for day_b in days:
                if day_b == day_a:
                    continue
                pois_b = clustered_pois[day_b]
                if len(pois_b) < 2:
                    continue

                counts_b = get_category_counts(pois_b)
                dom_cat_b, dom_count_b = dominant_category(counts_b)

                # day_b must also be dominated but by a DIFFERENT category
                if dom_cat_b == dom_cat_a:
                    continue
                if dom_count_b / len(pois_b) <= 0.6:
                    continue

                # Find its swap candidate (dominant category of day_b)
                swap_in = next(
                    (p for p in reversed(pois_b) if p.get('type') == dom_cat_b),
                    None
                )
                if swap_in:
                    best_day_b = day_b
                    best_swap_in = swap_in
                    break  # Take first valid match (already score-sorted)

            if best_day_b and best_swap_in:
                # Execute the swap
                clustered_pois[day_a].remove(swap_out)
                clustered_pois[best_day_b].remove(best_swap_in)
                clustered_pois[day_a].append(best_swap_in)
                clustered_pois[best_day_b].append(swap_out)
                swaps_this_pass += 1

        swaps_total += swaps_this_pass
        logger.info(f"Diversity pass {pass_num + 1}: {swaps_this_pass} swaps done")
        if swaps_this_pass == 0:
            break  # Converged, no more improvements

    logger.info(f"Category diversification complete: {swaps_total} total swaps across {max_passes} passes")
    return clustered_pois
