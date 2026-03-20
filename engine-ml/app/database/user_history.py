"""
User POI History — tracks which POIs each user has seen
so the ranking algorithm can penalize repeat recommendations.
"""
import logging
from typing import Set, List
from app.database.poi_cache import POICacheManager

logger = logging.getLogger(__name__)


def get_seen_poi_ids(user_id: int, city: str) -> Set[str]:
    """
    Fetch OSM IDs of POIs this user has already seen for this city.
    Returns empty set if user has no history or DB is unavailable.
    """
    if not user_id:
        return set()
    try:
        cache = POICacheManager()
        if not cache.connection or not cache.connection.is_connected():
            return set()
        cursor = cache.connection.cursor()
        cursor.execute(
            "SELECT osm_id FROM user_poi_history WHERE user_id = %s AND city = %s",
            (user_id, city.lower())
        )
        rows = cursor.fetchall()
        cursor.close()
        seen = {row[0] for row in rows}
        logger.info(f"User {user_id} has seen {len(seen)} POIs in {city}")
        return seen
    except Exception as e:
        logger.warning(f"Could not fetch user POI history: {e}")
        return set()


def save_seen_pois(user_id: int, city: str, osm_ids: List[str]) -> None:
    """
    Save the list of POI osm_ids shown to this user for this city.
    Uses INSERT IGNORE so duplicates are silently skipped.
    """
    if not user_id or not osm_ids:
        return
    try:
        cache = POICacheManager()
        if not cache.connection or not cache.connection.is_connected():
            return
        cursor = cache.connection.cursor()
        query = """
            INSERT IGNORE INTO user_poi_history (user_id, city, osm_id)
            VALUES (%s, %s, %s)
        """
        values = [(user_id, city.lower(), osm_id) for osm_id in osm_ids]
        cursor.executemany(query, values)
        cache.connection.commit()
        cursor.close()
        logger.info(f"Saved {len(osm_ids)} POIs to history for user {user_id} in {city}")
    except Exception as e:
        logger.warning(f"Could not save user POI history: {e}")
