/**
 * poi-images.js — 3-Tier POI Image Waterfall (v3)
 *
 * Tier 1: Wikipedia "pageimages" API  — exact article photo for the named place
 * Tier 2: Wikipedia category API      — random curated image from India-specific
 *                                       categories (Museums_in_India, Forts_in_India …)
 *                                       Culturally accurate, free, no key, CORS-safe.
 * Tier 3: Inline SVG placeholder      — works offline, card never looks broken
 */

// ── Tier 2: Wikipedia categories per POI type ───────────────────────────────
// These are well-populated Wikimedia Commons / Wikipedia article categories.
// The API randomly picks one article image each time → type-accurate photos.
const WIKI_CATEGORIES = {
    museum:    ['Museums_in_India', 'Archaeological_museums_in_India'],
    culture:   ['Temples_in_India', 'Hindu_temples_in_India', 'Mosques_in_India'],
    nature:    ['National_parks_of_India', 'Waterfalls_in_India', 'Wildlife_sanctuaries_in_India'],
    food:      ['Indian_cuisine', 'Street_food_in_India', 'Cuisine_of_India'],
    adventure: ['Mountains_of_India', 'Hill_stations_in_India', 'Trekking_in_India'],
    shopping:  ['Bazaars_in_India', 'Markets_in_India'],
    history:   ['Forts_in_India', 'Palaces_in_India', 'Heritage_sites_in_India'],
    nightlife: ['Night_markets_in_India', 'Festivals_in_India'],
    default:   ['Tourist_attractions_in_India', 'India_tourism']
};

// ── Tier 3 SVG placeholders per POI type ────────────────────────────────────
const POI_SVG_PLACEHOLDERS = {
    museum: {
        gradient: ['#667eea', '#764ba2'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/></svg>`
    },
    culture: {
        gradient: ['#f093fb', '#f5576c'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>`
    },
    nature: {
        gradient: ['#11998e', '#38ef7d'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 8C8 10 5.9 16.17 3.82 19c0 0 3-1 4.18-1 0 0 1 5 7 5 5.5 0 9-4.5 9-9.5A7.5 7.5 0 0 0 17 8z"/></svg>`
    },
    food: {
        gradient: ['#f7971e', '#ffd200'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>`
    },
    adventure: {
        gradient: ['#2196f3', '#21cbf3'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 2 22 22 22"/><line x1="12" y1="8" x2="12" y2="16"/></svg>`
    },
    shopping: {
        gradient: ['#ec4899', '#f43f5e'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`
    },
    history: {
        gradient: ['#c8a951', '#8B6914'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`
    },
    nightlife: {
        gradient: ['#2c3e75', '#4a1e8a'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`
    },
    default: {
        gradient: ['#2d5f3f', '#4a8f6f'],
        svg: `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.95)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>`
    }
};

// In-memory cache: cacheKey → { url, source }
const _imageCache = new Map();

// Category image pool cache: categoryName → [imageUrl, ...]
const _categoryPool = new Map();

// ── Helper: fetch with manual timeout ────────────────────────────────────────
function _fetchWithTimeout(url, options = {}, ms = 7000) {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('timeout')), ms);
        fetch(url, options)
            .then(r => { clearTimeout(timer); resolve(r); })
            .catch(e => { clearTimeout(timer); reject(e); });
    });
}

// Simple string hash for deterministic but varied image selection
function _hash(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
    return Math.abs(h);
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Resolve best image for a POI.
 * Returns { url, source: 'wikimedia'|'category'|'svg' }
 */
async function resolvePoiImage(poi) {
    const key = poi.name + '|' + (poi.type || '');
    if (_imageCache.has(key)) return _imageCache.get(key);

    // Tier 1 — Wikipedia page image for the named place
    const t1 = await _tier1Wikipedia(poi);
    if (t1) { _imageCache.set(key, t1); return t1; }

    // Tier 2 — Wikipedia category image (India-specific, type-accurate)
    const t2 = await _tier2WikiCategory(poi);
    if (t2) { _imageCache.set(key, t2); return t2; }

    // Tier 3 — SVG placeholder (resolved synchronously in applyPoiImage)
    const svg = { url: null, source: 'svg' };
    _imageCache.set(key, svg);
    return svg;
}

/**
 * Apply resolved image to a .poi-img-wrap element in the DOM.
 */
async function applyPoiImage(poi, imgWrapEl) {
    if (!imgWrapEl) return;
    const result = await resolvePoiImage(poi);
    const shimmer = imgWrapEl.querySelector('.poi-shimmer');
    const imgEl   = imgWrapEl.querySelector('.poi-photo');

    if (result.source === 'svg' || !result.url) {
        _showSvgFallback(imgWrapEl, poi.type, shimmer);
        return;
    }

    const temp = new Image();
    temp.onload = () => {
        if (shimmer && shimmer.parentNode) shimmer.remove();
        if (imgEl) {
            imgEl.src = result.url;
            imgEl.style.display = 'block';
            imgEl.style.opacity = '0';
            requestAnimationFrame(() => {
                imgEl.style.transition = 'opacity 0.45s ease';
                imgEl.style.opacity = '1';
            });
        }
    };
    temp.onerror = () => _showSvgFallback(imgWrapEl, poi.type, shimmer);
    temp.src = result.url;
}

// ── Tier 1: Wikipedia article photo for the exact place name ─────────────────
async function _tier1Wikipedia(poi) {
    // Try the OSM wikipedia tag first (most accurate)
    if (poi.wikipedia) {
        const title = poi.wikipedia.includes(':')
            ? poi.wikipedia.split(':').slice(1).join(':')
            : poi.wikipedia;
        const url = await _fetchWikipediaThumb(title);
        if (url) return { url, source: 'wikimedia' };
    }

    // Try the POI name directly — works great for famous landmarks
    const url = await _fetchWikipediaThumb(poi.name);
    if (url) return { url, source: 'wikimedia' };

    // Try "POI name City" for better disambiguation
    if (poi.city) {
        const url2 = await _fetchWikipediaThumb(`${poi.name} ${poi.city}`);
        if (url2) return { url: url2, source: 'wikimedia' };
    }
    return null;
}

async function _fetchWikipediaThumb(title) {
    try {
        const t = encodeURIComponent(title.trim());
        const apiUrl =
            `https://en.wikipedia.org/w/api.php` +
            `?action=query&titles=${t}&prop=pageimages&format=json` +
            `&pithumbsize=640&pilimit=1&origin=*`;
        const res = await _fetchWithTimeout(apiUrl, {}, 6000);
        if (!res.ok) return null;
        const data = await res.json();
        for (const page of Object.values(data?.query?.pages || {})) {
            if (page.pageid !== -1 && page.thumbnail?.source) {
                return page.thumbnail.source;
            }
        }
    } catch (_) {}
    return null;
}

// ── Tier 2: Wikipedia category API — India-specific, type-accurate ────────────
async function _tier2WikiCategory(poi) {
    const type = poi.type || 'default';
    const cats = WIKI_CATEGORIES[type] || WIKI_CATEGORIES.default;

    // Use a deterministic-but-varied index so the same POI always gets
    // the same category but different POIs rotate through.
    const catIndex = _hash(poi.name) % cats.length;
    const category = cats[catIndex];

    // Fetch a pool of article thumbnails from this Wikipedia category
    const pool = await _getCategoryImagePool(category);
    if (!pool || pool.length === 0) return null;

    // Pick deterministically based on POI name to keep images stable
    const img = pool[_hash(poi.name + category) % pool.length];
    return img ? { url: img, source: 'category' } : null;
}

/**
 * Fetch up to 30 article thumbnail URLs from a Wikipedia category.
 * Results are cached per category for the session so subsequent lookups are instant.
 */
async function _getCategoryImagePool(category) {
    if (_categoryPool.has(category)) return _categoryPool.get(category);

    try {
        // Use Wikipedia's generator API: get pages in the category + their images in one call
        const url =
            `https://en.wikipedia.org/w/api.php` +
            `?action=query&generator=categorymembers&gcmtitle=Category:${encodeURIComponent(category)}` +
            `&gcmtype=page&gcmlimit=30&prop=pageimages&pithumbsize=640&pilimit=30` +
            `&format=json&origin=*`;

        const res = await _fetchWithTimeout(url, {}, 8000);
        if (!res.ok) { _categoryPool.set(category, []); return []; }

        const data = await res.json();
        const pages = Object.values(data?.query?.pages || {});
        const urls = pages
            .map(p => p.thumbnail?.source)
            .filter(Boolean);

        _categoryPool.set(category, urls);
        return urls;
    } catch (_) {
        _categoryPool.set(category, []);
        return [];
    }
}

// ── Tier 3: SVG placeholder ───────────────────────────────────────────────────
function _showSvgFallback(wrapEl, type, shimmer) {
    if (shimmer && shimmer.parentNode) shimmer.remove();
    const ph = POI_SVG_PLACEHOLDERS[type] || POI_SVG_PLACEHOLDERS.default;
    const [c1, c2] = ph.gradient;
    wrapEl.innerHTML = `
        <div style="width:100%;height:100%;
            background:linear-gradient(135deg,${c1} 0%,${c2} 100%);
            display:flex;align-items:center;justify-content:center;">
            ${ph.svg}
        </div>`;
}
