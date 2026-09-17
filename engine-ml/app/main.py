"""
TravelPro ML Engine - Main FastAPI Application
Generates optimized travel itineraries using clustering and TSP algorithms
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import logging
import random
import asyncio

from app.models import ItineraryRequest, ItineraryResponse, DayItinerary, POI
from app.data.poi_data import get_pois_for_destination
from app.algorithms.clustering import (
    cluster_pois_by_day,
    balance_clusters,
    diversify_by_category,
    remove_outliers,
    sort_days_geographically,
)
from app.algorithms.tsp import optimize_daily_route
from app.algorithms.budget import predict_budget
from app.algorithms.ranking import rank_and_filter_pois
from app.database.user_history import get_seen_poi_ids, save_seen_pois

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TravelPro ML Engine",
    description="AI-powered travel itinerary generation service",
    version="1.0.0"
)

# Configure CORS — allow all localhost ports (dev) and any deployed origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5500",
        "http://localhost:5501",
        "http://localhost:5502",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:5501",
        "http://127.0.0.1:5502",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=False,   # we use Authorization header (JWT), not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DuckDuckGo image cache: query → (url|None, fetched_at) ────────────────────
_ddg_image_cache: dict = {}
_DDG_CACHE_TTL_H = 48   # re-fetch after 48 h

def _ddg_fetch_image(query: str) -> str | None:
    """
    Synchronous DuckDuckGo image search — run via asyncio.to_thread().
    Returns the first http image URL that is not an SVG, or None.
    """
    entry = _ddg_image_cache.get(query)
    if entry:
        url, ts = entry
        if datetime.now() - ts < timedelta(hours=_DDG_CACHE_TTL_H):
            return url
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.images(query, max_results=5, safesearch="moderate"):
                url = r.get("image", "")
                if url and url.startswith("http") and not url.lower().endswith(".svg"):
                    _ddg_image_cache[query] = (url, datetime.now())
                    return url
    except Exception as e:
        logger.warning(f"DDG image search failed for '{query}': {e}")
    _ddg_image_cache[query] = (None, datetime.now())
    return None


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "TravelPro ML Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "generate_itinerary": "POST /generate_itinerary",
            "get_pois": "POST /get_pois",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/poi-image")
async def poi_image(name: str, city: str = ""):
    """
    Return a real image URL for a POI using DuckDuckGo image search.
    Results are cached in-memory for 48 h.

    Response:
        { "url": "<image-url>" }  — real image found
        { "url": null }           — no image found; frontend shows letter-avatar
    """
    query = f"{name} {city}".strip() if city else name
    logger.info(f"POI-image: '{query}'")
    try:
        url = await asyncio.wait_for(
            asyncio.to_thread(_ddg_fetch_image, query),
            timeout=8.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"DDG image error for '{query}': {e}")
        url = None
    return {"url": url}


@app.post("/generate_itinerary")
async def generate_itinerary(request: ItineraryRequest):
    """
    Generate an optimized travel itinerary
    
    Input:
        - destination: City name
        - days: Number of days
        - budget: Total budget
        - interests: List of interest categories
    
    Output:
        - itinerary: Dictionary of day-wise POI lists
        - total_cost: Estimated total cost
        - optimized_score: Quality metric
    """
    try:
        logger.info(f"Processing itinerary request for {request.destination}, {request.days} days")
        
        # Step 1: Get POIs for destination from OpenStreetMap
        pois = get_pois_for_destination(request.destination, request.interests, use_api=True)
        
        if not pois or len(pois) == 0:
            logger.warning(f"No POIs found for {request.destination}")
            raise HTTPException(
                status_code=404,
                detail=f"No points of interest found for {request.destination}"
            )
        
        logger.info(f"Found {len(pois)} POIs for {request.destination}")
        
        # Log POI names before ranking
        poi_names = [poi.get('name', 'UNKNOWN') for poi in pois[:5]]
        logger.info(f"First 5 POI names BEFORE ranking: {poi_names}")
        
        # Step 2: Load user's seen POI history (Tier 2 personalization)
        seen_poi_ids = get_seen_poi_ids(request.user_id, request.destination)
        logger.info(f"User ID: {request.user_id} | Seen POIs for {request.destination}: {len(seen_poi_ids)}")

        # ── Step 3: Rank POIs ─────────────────────────────────────────────────
        # Rank 3× more than needed so the 25 km geofence still leaves ≥ 5 per day.
        POIS_PER_DAY = 5
        MIN_NEEDED   = request.days * POIS_PER_DAY
        keep_top_n   = MIN_NEEDED * 3           # e.g. 5 days × 5 × 3 = 75 candidates

        # Keep a snapshot of the full fetched pool for the fallback step
        all_fetched_pois = list(pois)

        pois = rank_and_filter_pois(pois, keep_top_n=keep_top_n,
                                    interests=request.interests,
                                    seen_poi_ids=seen_poi_ids)
        logger.info(f"After ranking: kept top {len(pois)} diverse POIs")

        # ── PHASE 1: Geofence Outlier Purge ──────────────────────────────────
        # Drop any POI farther than 25 km from the city geocentre.
        city_coords = None
        try:
            from app.services.osm_service import get_osm_service
            osm_svc     = get_osm_service()
            city_coords = osm_svc.geocode_city(request.destination)
            if city_coords:
                pois = remove_outliers(
                    pois,
                    city_lat=city_coords['lat'],
                    city_lon=city_coords['lon'],
                    max_radius_km=25.0,
                )
        except Exception as geo_err:
            logger.warning(f"Geofence filter skipped: {geo_err}")

        # ── Fallback: supplement if geofence trimmed below minimum ───────────
        # If outlier removal left us with fewer than days×5, pull extra POIs
        # from the original full pool using a relaxed 40 km radius.
        if len(pois) < MIN_NEEDED and city_coords:
            shortfall = MIN_NEEDED - len(pois)
            logger.info(
                f"Supplementing: need {shortfall} more POIs "
                f"(have {len(pois)}/{MIN_NEEDED}) — relaxing geofence to 40 km"
            )
            existing_ids = {p.get('osm_id', p.get('name')) for p in pois}
            supplemental_pool = [
                p for p in all_fetched_pois
                if p.get('osm_id', p.get('name')) not in existing_ids
            ]
            supplemental_pool = remove_outliers(
                supplemental_pool,
                city_lat=city_coords['lat'],
                city_lon=city_coords['lon'],
                max_radius_km=40.0,    # relaxed radius for supplements only
            )
            # Rank the supplements and take only what we still need
            supplemental_pool = rank_and_filter_pois(
                supplemental_pool,
                keep_top_n=shortfall * 2,
                interests=request.interests,
                seen_poi_ids=seen_poi_ids,
            )
            pois = pois + supplemental_pool[:shortfall]
            logger.info(f"After supplement: {len(pois)} POIs total")

        # ── Hard cap: feed EXACTLY days×5 POIs into clustering ───────────────
        # We ranked 3× as a buffer for the geofence; now trim back to the
        # precise target so every day gets exactly POIS_PER_DAY (5) POIs.
        pois = pois[:MIN_NEEDED]
        logger.info(f"Final pool before clustering: {len(pois)} POIs ({request.days} days × {POIS_PER_DAY})")


        if not pois:
            raise HTTPException(
                status_code=404,
                detail=f"No POIs within city bounds for {request.destination}"
            )

        # ── Cluster POIs into days (Agglomerative / Haversine) ────────────────
        clustered_pois = cluster_pois_by_day(pois, request.days)
        logger.info(f"Clustered POIs into {request.days} days")

        # Log first two days for debugging
        for day, day_pois in list(clustered_pois.items())[:2]:
            names = [poi.get('name', 'UNKNOWN') for poi in day_pois[:3]]
            logger.info(f"Day {day} POI names AFTER clustering: {names}")

        # Balance: always aim for exactly POIS_PER_DAY (5) per day
        balanced_clusters = balance_clusters(clustered_pois, POIS_PER_DAY)

        # Diversify: no day dominated by one category
        balanced_clusters = diversify_by_category(balanced_clusters)

        # ── PHASE 2: Geographical Day Sorter ─────────────────────────────────
        # Renumber days so Day 1 = most central cluster, Day N = most remote.
        balanced_clusters = sort_days_geographically(balanced_clusters)

        
        # Step 4: Optimize route for each day using TSP
        itinerary = {}
        total_cost = 0
        
        for day_num, day_pois in balanced_clusters.items():
            # Optimize order of POIs for this day
            optimized_pois = optimize_daily_route(day_pois)
            
            # Nightlife always happens at night — move bars/clubs to end of day
            optimized_pois.sort(key=lambda p: 1 if p.get('type') == 'nightlife' else 0)
            
            # Convert to response format
            itinerary[f"day_{day_num}"] = [
                POI(
                    name=poi['name'],
                    type=poi.get('type', 'attraction'),
                    duration=poi.get('duration', 2),
                    cost=poi.get('cost', 0),
                    lat=poi.get('lat', 0.0),
                    lon=poi.get('lon', 0.0)
                )
                for poi in optimized_pois
            ]
            
            # Calculate day cost
            total_cost += sum(poi.get('cost', 0) for poi in optimized_pois)
            
            # Log warning if day has no POIs
            if len(optimized_pois) == 0:
                logger.warning(f"Day {day_num} has no POIs")
        
        # Step 5: Calculate budget prediction
        predicted_budget = predict_budget(pois, request.budget)
        
        # Create response matching ItineraryResponse schema
        response = ItineraryResponse(
            destination=request.destination,
            days=request.days,
            totalBudget=request.budget,
            estimatedCost=predicted_budget.get('estimated_cost', total_cost),
            greenSignal=predicted_budget.get('green_signal', True),
            dayByDay=[
                DayItinerary(
                    day=int(day.split('_')[1]),
                    date="",  # Will be calculated by frontend
                    pois=pois
                )
                for day, pois in itinerary.items()
            ]
        )
        
        # Save selected POIs to user history so next search gets different places
        if request.user_id:
            selected_osm_ids = [p.get('osm_id') for p in pois if p.get('osm_id')]
            save_seen_pois(request.user_id, request.destination, selected_osm_ids)

        logger.info(f"Successfully generated itinerary for {request.destination}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/get_pois")
async def get_pois(request: dict):
    """
    Get POIs for a city - used by destinations discovery page
    
    Request: { "destination": "Mumbai", "interests": [] }
    Returns: { "pois": [...], "city": "Mumbai", "count": 50 }
    """
    try:
        destination = request.get('destination', '')
        interests = request.get('interests', [])
        
        if not destination:
            raise HTTPException(status_code=400, detail="City name is required")
        
        logger.info(f"Fetching POIs for {destination}")
        
        # If no interests, get diverse selection
        if not interests:
            interests = ['museum', 'food', 'culture', 'nature', 'shopping', 'history']
        
        # Fetch POIs from OSM with caching (real data)
        pois = get_pois_for_destination(destination, interests, use_api=True)
        
        if not pois:
            logger.warning(f"No POIs found for {destination}")
            return {
                "pois": [],
                "city": destination,
                "count": 0
            }
        
        logger.info(f"Returning {len(pois)} POIs for {destination}")
        
        return {
            "pois": pois,
            "city": destination,
            "count": len(pois)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_pois: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


def _fetch_and_cache_osm_pois(city: str):
    """
    Background task: fetch up to 200 real POIs from OSM for a city and
    persist them to the DB cache so every future request is instant.
    Runs in a separate thread — does NOT block the HTTP response.
    """
    try:
        logger.info(f"[BG] Starting OSM fetch for '{city}'")
        all_interests = ['museum', 'food', 'culture', 'nature', 'shopping', 'history', 'adventure', 'nightlife']
        from app.services.osm_service import get_osm_service
        from app.database.poi_cache import get_cache_manager

        osm = get_osm_service()
        pois = osm.fetch_pois_for_city(city, all_interests, radius_km=25, limit=200)

        if pois:
            cache = get_cache_manager()
            saved = cache.save_pois(city, pois)
            logger.info(f"[BG] Saved {saved} real OSM POIs for '{city}' to DB")
        else:
            logger.warning(f"[BG] OSM returned no POIs for '{city}'")
    except Exception as e:
        logger.error(f"[BG] OSM fetch failed for '{city}': {e}", exc_info=True)


@app.get("/preview_pois/{city}")
async def preview_pois(city: str, background_tasks: BackgroundTasks):
    """
    Return up to 10 real POI names/types for a city — no auth required.
    Used by the landing page (index.html) to tease content before login.

    Real-data strategy:
      1. Check DB cache (real OSM data already stored) → instant response.
      2. Cache miss → kick off a background OSM fetch (200 POIs → DB),
         return status='fetching' immediately so the client can retry
         after ~20s once OSM data is ready.
      3. Mock fallback only if city has no OSM coords and OSM is unreachable.
    """
    try:
        logger.info(f"Preview POIs request for: {city}")
        all_interests = ['museum', 'food', 'culture', 'nature', 'shopping', 'history', 'adventure', 'nightlife']

        # ── Step 1: Check DB cache only (real OSM data, instant) ──────────
        try:
            from app.database.poi_cache import get_cache_manager
            cache = get_cache_manager()
            if cache.is_cache_fresh(city, max_age_hours=720):   # 30-day TTL
                cached_pois = cache.get_cached_pois(city, all_interests)
                if cached_pois:
                    logger.info(f"Cache HIT for '{city}': {len(cached_pois)} POIs")

                    # ── Diverse selection: 1 guaranteed per category ──────────
                    # Group by type, shuffle each group for variety
                    from collections import defaultdict
                    by_type: dict = defaultdict(list)
                    for p in cached_pois:
                        by_type[p.get("type", "attraction")].append(p)
                    for grp in by_type.values():
                        random.shuffle(grp)

                    # Pick 1 from each category (guarantees diversity)
                    guaranteed = [grp.pop() for grp in by_type.values()]
                    random.shuffle(guaranteed)

                    # Fill remaining slots (up to 10 total) from the leftover pool
                    leftover = [p for grp in by_type.values() for p in grp]
                    random.shuffle(leftover)
                    sample = (guaranteed + leftover)[:10]

                    preview = [
                        {"name": p["name"], "type": p.get("type", "attraction")}
                        for p in sample
                    ]

                    return {
                        "city": city,
                        "status": "ready",
                        "total_found": len(cached_pois),
                        "preview": preview
                    }
        except Exception as cache_err:
            logger.warning(f"Cache check failed for '{city}': {cache_err}")

        # ── Step 2: Cache miss — trigger background OSM fetch ─────────────
        logger.info(f"Cache MISS for '{city}' — queuing background OSM fetch")
        background_tasks.add_task(_fetch_and_cache_osm_pois, city)

        # Return immediately with 'fetching' status so frontend can retry
        return {
            "city": city,
            "status": "fetching",          # frontend polls again after retry_after seconds
            "retry_after": 20,             # OSM usually completes in 10-20s
            "total_found": 0,
            "preview": []
        }

    except Exception as e:
        logger.error(f"Error in preview_pois for {city}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching POIs: {str(e)}")



@app.get("/api/discover")
async def discover_city(city: str, background_tasks: BackgroundTasks):
    """
    Teaser endpoint — validates the city with Nominatim, then returns up to 8
    real POIs (with lat/lon and category) for the landing-page card grid.

    Responses:
      200 { status:"ready",   city, places:[...8 POIs...] }
      200 { status:"fetching", city, retry_after }   — OSM fetch kicked off BG
      404  city not found by Nominatim
      503  geocoder service unavailable
    """
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderServiceError, GeocoderTimedOut
    from collections import defaultdict

    # ── Step 1: Validate city with Nominatim ──────────────────────────────
    try:
        geolocator = Nominatim(user_agent="TravelPro_Dev/1.0", timeout=6)
        location = geolocator.geocode(city)
    except (GeocoderTimedOut, GeocoderServiceError) as geo_err:
        logger.warning(f"Geocoder unavailable for '{city}': {geo_err}")
        raise HTTPException(
            status_code=503,
            detail="Location service is temporarily unavailable. Please try again in a moment."
        )
    except Exception as geo_err:
        logger.error(f"Unexpected geocoder error for '{city}': {geo_err}")
        raise HTTPException(status_code=503, detail="Location lookup failed. Please try again.")

    if location is None:
        raise HTTPException(
            status_code=404,
            detail=f"Hmm, we couldn't find a place called '{city}'. Please check the spelling and try again."
        )

    verified_city_name = location.address  # e.g. "Jaipur, Rajasthan, India"
    logger.info(f"Discover: '{city}' → '{verified_city_name}' ({location.latitude:.4f}, {location.longitude:.4f})")

    # ── Step 2: Serve from DB cache if available ───────────────────────────
    try:
        from app.database.poi_cache import get_cache_manager
        cache = get_cache_manager()
        all_interests = ['museum', 'food', 'culture', 'nature', 'shopping', 'history', 'adventure', 'nightlife']

        if cache.is_cache_fresh(city, max_age_hours=720):

            # Priority order for diversity (food last — most common)
            ORDERED_INTERESTS = [
                'museum', 'history', 'culture', 'nature',
                'adventure', 'shopping', 'nightlife', 'food'
            ]

            # Pre-fetch all POIs grouped by category (one DB call per category)
            pool: dict = {}   # interest → shuffled list of POIs
            for interest in ORDERED_INTERESTS:
                cat_pois = cache.get_cached_pois(city, [interest])
                random.shuffle(cat_pois)
                if cat_pois:
                    pool[interest] = cat_pois

            logger.info(
                f"Discover pool for '{city}': "
                + ", ".join(f"{k}={len(v)}" for k, v in pool.items())
            )

            # Expanding-cap selection:
            # cap=1 → take 1 from each type that has data (guaranteed diversity)
            # cap=2 → take 1 more from each type still under cap, cycling interest order
            # cap=3 → ... until we reach 10 or every bucket is exhausted
            # MAX_PER_TYPE=2 → hard limit; no type appears more than twice
            selected     = []
            selected_ids = set()
            type_counts: dict = defaultdict(int)
            MAX_PER_TYPE = 2
            cap = 1

            while len(selected) < 10 and cap <= MAX_PER_TYPE:
                made_progress = False
                for interest in ORDERED_INTERESTS:
                    if len(selected) >= 10:
                        break
                    if interest not in pool:
                        continue
                    candidates = [
                        p for p in pool[interest]
                        if p['name'] not in selected_ids
                    ]
                    if type_counts[interest] < cap and candidates:
                        pick = random.choice(candidates)
                        selected.append(pick)
                        selected_ids.add(pick['name'])
                        type_counts[interest] += 1
                        made_progress = True
                if not made_progress:
                    break
                cap += 1

            logger.info(
                f"Discover: {len(selected)} POIs for '{city}' "
                f"→ {dict(type_counts)}"
            )

            if selected:
                # Interleave by type so same-type cards don't cluster in the grid
                type_groups: dict = defaultdict(list)
                for p in selected:
                    type_groups[p.get('type', 'food')].append(p)
                # Zip across groups so each "row" picks one from each type
                cols = sorted(type_groups.values(), key=len, reverse=True)
                from itertools import zip_longest
                interleaved = [
                    item for row in zip_longest(*cols)
                    for item in row if item is not None
                ]
                places = [
                    {
                        "name": p["name"],
                        "type": p.get("type", "attraction"),
                        "lat":  p.get("lat", location.latitude),
                        "lon":  p.get("lon", location.longitude),
                        "cost": p.get("cost", 0),
                    }
                    for p in interleaved[:10]
                ]
                return {
                    "status": "ready",
                    "city":   verified_city_name,
                    "places": places,
                }
    except Exception as cache_err:
        logger.warning(f"Cache lookup failed in /api/discover for '{city}': {cache_err}")

    # ── Step 3: Cache miss — trigger background OSM fetch ──────────────────
    logger.info(f"Discover: cache miss for '{city}' — queuing OSM background fetch")
    background_tasks.add_task(_fetch_and_cache_osm_pois, city)

    return {
        "status":      "fetching",
        "city":        verified_city_name,
        "places":      [],
        "retry_after": 20,
    }


# Day theme labels for the reference itinerary display
_DAY_THEMES = [
    ("🏛️ Culture & History", ["museum", "history", "culture"]),
    ("🌿 Nature & Adventure", ["nature", "adventure"]),
    ("🍽️ Food & Nightlife",  ["food", "nightlife", "shopping"]),
]


@app.get("/reference_itinerary/{city}")
async def reference_itinerary(city: str, background_tasks: BackgroundTasks):
    """
    Return a 2-day sample (reference) itinerary for a city — no auth required.
    Used by destination cards on the landing page to show a teaser routine.

    Strategy:
      - Pull up to 30 cached POIs from DB (real OSM data), grouped by category.
      - Distribute them across 2 themed days (Day 1: culture/history/museums,
        Day 2: nature/adventure/food/nightlife).
      - Each day shows 4-5 POIs.
      - Cache miss → queue background OSM fetch, return status='fetching'.
    """
    try:
        logger.info(f"Reference itinerary request for: {city}")
        all_interests = ['museum', 'food', 'culture', 'nature', 'shopping',
                         'history', 'adventure', 'nightlife']

        # ── Check DB cache ─────────────────────────────────────────────────
        try:
            from app.database.poi_cache import get_cache_manager
            from collections import defaultdict
            cache = get_cache_manager()

            if cache.is_cache_fresh(city, max_age_hours=720):
                cached_pois = cache.get_cached_pois(city, all_interests)
                if cached_pois:
                    # ── Diverse mixed pool: 1 per category guaranteed ────────
                    from collections import defaultdict
                    by_type: dict = defaultdict(list)
                    for p in cached_pois:
                        by_type[p.get("type", "culture")].append(p)
                    for grp in by_type.values():
                        random.shuffle(grp)

                    # 1 guaranteed from each type, then fill from leftovers
                    guaranteed = [grp.pop() for grp in by_type.values()]
                    leftover   = [p for grp in by_type.values() for p in grp]
                    random.shuffle(leftover)

                    pool = guaranteed + leftover   # diverse mix, guaranteed first
                    pool = pool[:10]               # take only 10 for 2 days × 5
                    random.shuffle(pool)           # final shuffle so days are unpredictable

                    day1_pois = pool[:5]
                    day2_pois = pool[5:]

                    # Build 2 themed days (both fully mixed)
                    days = []

                    if day1_pois:
                        days.append({
                            "day": 1,
                            "theme": "🗺️ Day 1 Highlights",
                            "pois": [{
                                "name": p["name"],
                                "type": p.get("type", "attraction"),
                                "lat":  p.get("lat"),
                                "lon":  p.get("lon"),
                            } for p in day1_pois]
                        })
                    if day2_pois:
                        days.append({
                            "day": 2,
                            "theme": "✨ Day 2 Highlights",
                            "pois": [{
                                "name": p["name"],
                                "type": p.get("type", "attraction"),
                                "lat":  p.get("lat"),
                                "lon":  p.get("lon"),
                            } for p in day2_pois]
                        })


                    if days:
                        logger.info(f"Reference itinerary ready for '{city}': {sum(len(d['pois']) for d in days)} POIs across {len(days)} days")
                        return {
                            "city": city,
                            "status": "ready",
                            "total_cached": len(cached_pois),
                            "days": days
                        }

        except Exception as cache_err:
            logger.warning(f"Cache check failed for '{city}': {cache_err}")

        # ── Cache miss — kick off background fetch ──────────────────────────
        logger.info(f"No cache for '{city}' — queuing OSM fetch for reference itinerary")
        background_tasks.add_task(_fetch_and_cache_osm_pois, city)

        return {
            "city": city,
            "status": "fetching",
            "retry_after": 20,
            "days": []
        }

    except Exception as e:
        logger.error(f"Error in reference_itinerary for {city}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Run with: uvicorn app.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
