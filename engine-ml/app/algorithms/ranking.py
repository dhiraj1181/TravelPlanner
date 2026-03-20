"""
POI Ranking & Diversity Algorithm — Indian Context Edition

Two-phase selection:
  Phase 1 — Score: Rate each POI by importance (Indian context signals)
  Phase 2 — Balance: Pick proportionally from each interest category
             so every day has a VARIED mix, not just temples all day
"""
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Indian "Power Words" ─────────────────────────────────────
POWER_WORDS = [
    'mandir', 'temple', 'dham', 'ashram', 'math', 'gurudwara',
    'masjid', 'mosque', 'church', 'dargah', 'stupa', 'vihara',
    'falls', 'waterfall', 'jharna', 'lake', 'jheel', 'tal',
    'dam', 'bandh', 'river', 'nadi', 'peak', 'hill',
    'pahar', 'ghat', 'cave', 'gufa', 'spring', 'kund',
    'island', 'beach', 'van', 'forest', 'national park',
    'wildlife', 'sanctuary', 'reserve',
    'fort', 'qila', 'kila', 'palace', 'mahal', 'haveli',
    'museum', 'memorial', 'smarak', 'ruins', 'tomb',
    'mausoleum', 'tower', 'minar', 'gate', 'darwaza',
    'baoli', 'stepwell',
    'garden', 'bagh', 'park', 'udyan',
    'zoo', 'botanical',
    'viewpoint', 'point', 'view', 'lookout', 'ropeway', 'rock',
]

POWER_WORDS_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(w) for w in POWER_WORDS) + r')\b',
    re.IGNORECASE
)

# Type-based importance bonus
TYPE_SCORES = {
    'castle': 15, 'waterfall': 15, 'peak': 15, 'monument': 15,
    'memorial': 12, 'ruins': 12, 'archaeological_site': 12,
    'museum': 10, 'gallery': 10, 'attraction': 10,
    'place_of_worship': 8,
    'nature_reserve': 8, 'beach': 5, 'park': 5, 'garden': 5,
    'cave_entrance': 10, 'hot_spring': 10, 'viewpoint': 8,
    'water_park': 5,
    'restaurant': 0, 'cafe': 0, 'fast_food': 0,
    'bar': 0, 'nightclub': 0, 'pub': 0,
    'mall': 0, 'department_store': 0, 'marketplace': 0,
}

RICHNESS_TAGS = [
    'image', 'wikimedia_commons', 'phone', 'contact:phone',
    'religion', 'wheelchair', 'fee', 'tourism',
    'opening_hours', 'addr:street', 'description',
]


def score_poi(poi: dict) -> float:
    """
    Score a POI using Indian Context signals.
    Works for both fresh OSM POIs (raw_tags present) and cached DB POIs.
    
    GLOBAL:   Wikipedia +40, Wikidata +25, Website +10
    INDIAN:
      Name Rule     — multilingual name:hi + name:en → +20
      Keyword Rule  — power words like Falls/Mandir/Fort → +30
      Polygon Rule  — mapped as way/relation (larger) → +15
      Tag Richness  — image, religion, opening_hours etc → +5 each
    TYPE BONUS:  +0-15
    CACHE BONUS: address (+5), description (+5), high rating (+10)
    """
    score = 0.0
    
    # Merge raw_tags with synthesized fields from cached DB columns
    # This makes scoring work whether POI is fresh from OSM or from MySQL cache
    raw_tags = dict(poi.get('raw_tags') or {})
    if poi.get('address'):
        raw_tags.setdefault('addr:street', poi['address'])
    if poi.get('description'):
        raw_tags.setdefault('description', poi['description'])
    
    name = poi.get('name', '')

    # Global signals (only available for fresh OSM POIs)
    if raw_tags.get('wikipedia'):  score += 40
    if raw_tags.get('wikidata'):   score += 25
    if raw_tags.get('website') or raw_tags.get('url'): score += 10

    # ── Name Rule (+20) ─────────────────────────────────
    has_hindi = bool(raw_tags.get('name:hi'))
    has_english = bool(raw_tags.get('name:en'))
    if has_hindi and has_english:
        score += 20
    elif has_hindi or has_english:
        score += 10

    # ── Keyword Rule (+30) ──────────────────────────────
    if name and POWER_WORDS_PATTERN.search(name):
        score += 30

    # ── Polygon Rule (+15) ──────────────────────────────
    if poi.get('osm_element_type', 'node') in ('way', 'relation'):
        score += 15

    # ── Tag Richness Rule (+5 each) ─────────────────────
    for tag in RICHNESS_TAGS:
        if raw_tags.get(tag):
            score += 5

    # ── Cache-aware Type Bonus (+0-15) ──────────────────
    # Cached POIs store type in 'type' not 'osm_type' — try both
    osm_type = poi.get('osm_type') or poi.get('type', '')
    score += TYPE_SCORES.get(osm_type, 0)

    # ── Rating Bonus (cached DB POIs only) (+0-10) ──────
    rating = poi.get('rating')
    if rating and float(rating) >= 4.0:
        score += 10
    elif rating and float(rating) >= 3.5:
        score += 5

    return score


def rank_and_filter_pois(pois: list, keep_top_n: int,
                         interests: list = None,
                         seen_poi_ids: set = None) -> list:
    """
    Two-tier diversity system:
    
    TIER 1 — Score-weighted random sampling
        Instead of always taking the same top-N, sample from the top 2×
        candidates using scores as weights. Famous places still appear
        often but not guaranteed every time — variety by default.
    
    TIER 2 — Seen POI penalty (personalization)
        POIs the user has already seen get −50 points, sinking them
        to the bottom of the ranking so they're rarely picked again.
    
    Args:
        pois:          All fetched POIs (with raw_tags)
        keep_top_n:    Total POIs to keep (= days × 5)
        interests:     User interests for category-balanced selection
        seen_poi_ids:  Set of osm_ids this user has already seen
    
    Returns:
        Filtered, diverse, personalized list of keep_top_n POIs
    """
    if not pois:
        return pois

    seen_poi_ids = seen_poi_ids or set()

    # ── Phase 1: Score ───────────────────────────────────
    for poi in pois:
        poi['score'] = score_poi(poi)
        # TIER 2: Penalize previously seen POIs
        if poi.get('osm_id') in seen_poi_ids:
            poi['score'] -= 50
            poi['_seen'] = True

    # Sort globally by score (best first)
    pois.sort(key=lambda p: p['score'], reverse=True)

    # ── Phase 2: Category-balanced selection ─────────────
    from collections import defaultdict

    buckets = defaultdict(list)
    for poi in pois:
        category = poi.get('type', 'culture')
        buckets[category].append(poi)

    active_interests = list(interests) if interests else []
    extra_categories = [c for c in buckets if c not in active_interests]
    ordered_categories = active_interests + extra_categories

    num_categories = len([c for c in ordered_categories if c in buckets])
    slots_per_category = max(1, keep_top_n // num_categories) if num_categories else keep_top_n

    # ── Phase 3: TIER 1 — Weighted random sampling ───────
    import random

    selected = []
    used_ids = set()

    # For each category bucket, sample using score-weights from top candidates
    pool_multiplier = 2  # Sample from top 2× candidates for variety
    for category in ordered_categories:
        if category not in buckets:
            continue
        # Get top candidates for this bucket
        candidates = [p for p in buckets[category] if p.get('osm_id', p.get('name', id(p))) not in used_ids]
        pool = candidates[:slots_per_category * pool_multiplier]
        if not pool:
            continue

        weights = [max(0.1, p['score'] + 60) for p in pool]  # +60 keeps negatives positive

        count = 0
        attempts = 0
        while count < slots_per_category and pool and attempts < slots_per_category * 4:
            attempts += 1
            pick = random.choices(pool, weights=weights, k=1)[0]
            pick_key = pick.get('osm_id', pick.get('name', id(pick)))
            if pick_key not in used_ids:
                selected.append(pick)
                used_ids.add(pick_key)
                count += 1

    # Fill any remaining slots from global pool (weighted)
    if len(selected) < keep_top_n:
        remaining_pool = [p for p in pois if p.get('osm_id', p.get('name', id(p))) not in used_ids]
        remaining_weights = [max(0.1, p['score'] + 60) for p in remaining_pool]
        while len(selected) < keep_top_n and remaining_pool:
            pick = random.choices(remaining_pool, weights=remaining_weights, k=1)[0]
            pick_key = pick.get('osm_id', pick.get('name', id(pick)))
            if pick_key not in used_ids:
                selected.append(pick)
                used_ids.add(pick_key)

    # ── Logging ──────────────────────────────────────────
    from collections import Counter
    category_mix = Counter(p.get('type', '?') for p in selected)
    seen_count = sum(1 for p in selected if p.get('_seen'))
    top5 = [(p['name'], p.get('type', '?'), int(p['score'])) for p in selected[:5]]
    logger.info(f"POI Ranking — Top 5 (name, type, score): {top5}")
    logger.info(f"Category mix: {dict(category_mix)}")
    logger.info(f"Previously seen POIs in selection: {seen_count}/{len(selected)}")
    logger.info(f"Selected {len(selected)} diverse POIs from {len(pois)} total")

    return selected

