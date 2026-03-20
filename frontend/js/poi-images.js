/**
 * poi-images.js — 3-Tier POI Image Waterfall
 *
 * Tier 1: Wikipedia REST API  — exact photo for famous places (free, no key, CORS-safe)
 * Tier 2: Lorem Flickr        — category vibe photo  (free, no key, reliable replacement for defunct source.unsplash.com)
 * Tier 3: Inline SVG          — offline-safe gradient + icon, card never looks broken
 */

// ── Tier 3 SVG placeholders per POI type ─────────────────────────────────
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

// Tier 2: loremflickr.com keywords per POI type
// Format: https://loremflickr.com/{w}/{h}/{keyword1},{keyword2}
const FLICKR_KEYWORDS = {
    museum:    ['museum', 'heritage', 'architecture'],
    culture:   ['temple', 'monument', 'india'],
    nature:    ['nature', 'park', 'landscape'],
    food:      ['food', 'restaurant', 'cuisine'],
    adventure: ['mountain', 'trekking', 'viewpoint'],
    shopping:  ['market', 'bazaar', 'shopping'],
    history:   ['fort', 'ruins', 'historical'],
    nightlife: ['city', 'lights', 'night'],
    default:   ['travel', 'india', 'destination']
};

// In-memory URL cache
const _imageCache = new Map();

// ── Helper: fetch with manual timeout (broad browser support) ─────────────
function _fetchWithTimeout(url, options = {}, ms = 6000) {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('timeout')), ms);
        fetch(url, options)
            .then(r => { clearTimeout(timer); resolve(r); })
            .catch(e => { clearTimeout(timer); reject(e); });
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Resolve best image for a POI.
 * Returns { url, source: 'wikimedia'|'flickr'|'svg' }
 * 'svg' means inject via innerHTML, not <img src>.
 */
async function resolvePoiImage(poi) {
    const key = poi.name + '|' + (poi.type || '');
    if (_imageCache.has(key)) return _imageCache.get(key);

    // Tier 1 — Wikipedia
    const wikiResult = await _tier1Wikipedia(poi);
    if (wikiResult) {
        _imageCache.set(key, wikiResult);
        return wikiResult;
    }

    // Tier 2 — Lorem Flickr
    const flickrResult = _tier2LoremFlickr(poi);
    _imageCache.set(key, flickrResult);
    return flickrResult;
    // Tier 3 (SVG) is applied in applyPoiImage on img.onerror
}

/**
 * Apply an image to a .poi-img-wrap element that is already in the DOM.
 * Removes the shimmer and either shows the photo or injects an SVG placeholder.
 */
async function applyPoiImage(poi, imgWrapEl) {
    if (!imgWrapEl) return;

    const result = await resolvePoiImage(poi);
    const shimmer = imgWrapEl.querySelector('.poi-shimmer');
    const imgEl = imgWrapEl.querySelector('.poi-photo');

    if (result.source === 'svg') {
        _showSvgFallback(imgWrapEl, poi.type, shimmer);
        return;
    }

    const tempImg = new Image();

    tempImg.onload = () => {
        if (shimmer && shimmer.parentNode) shimmer.remove();
        if (imgEl) {
            imgEl.src = result.url;
            imgEl.style.display = 'block';
            imgEl.style.opacity = '0';
            // Fade in
            requestAnimationFrame(() => {
                imgEl.style.transition = 'opacity 0.45s ease';
                imgEl.style.opacity = '1';
            });
        }
    };

    tempImg.onerror = () => {
        // Tier 2 failed → Tier 3 SVG
        _showSvgFallback(imgWrapEl, poi.type, shimmer);
    };

    tempImg.src = result.url;
}

// ── Tier 1: Wikipedia page image ─────────────────────────────────────────
async function _tier1Wikipedia(poi) {
    // Path A: OSM wikipedia tag (e.g. "en:Amber Fort")
    if (poi.wikipedia) {
        const title = poi.wikipedia.includes(':')
            ? poi.wikipedia.split(':').slice(1).join(':')
            : poi.wikipedia;
        const url = await _fetchWikipediaThumb(title);
        if (url) return { url, source: 'wikimedia' };
    }

    // Path B: Try POI name directly — works well for famous landmarks
    const url = await _fetchWikipediaThumb(poi.name);
    if (url) return { url, source: 'wikimedia' };

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
        const pages = Object.values(data?.query?.pages || {});
        for (const page of pages) {
            // "-1" page id means the article doesn't exist
            if (page.pageid !== -1 && page.thumbnail?.source) {
                return page.thumbnail.source;
            }
        }
    } catch (_) { /* timeout or network — fall through */ }
    return null;
}

// ── Tier 2: Lorem Flickr (free, no key, category keywords) ───────────────
function _tier2LoremFlickr(poi) {
    const keywords = FLICKR_KEYWORDS[poi.type] || FLICKR_KEYWORDS.default;
    // loremflickr picks a real Flickr photo tagged with these words
    // Lock=hash so the same POI always gets the same photo
    const lock = _simpleHash(poi.name);
    const kw = keywords.join(',');
    const url = `https://loremflickr.com/600/400/${encodeURIComponent(kw)}/all?lock=${lock}`;
    return { url, source: 'flickr' };
}

// ── Tier 3 helper ─────────────────────────────────────────────────────────
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

// Simple deterministic hash for loremflickr lock parameter
function _simpleHash(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) {
        h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
    }
    return Math.abs(h);
}
