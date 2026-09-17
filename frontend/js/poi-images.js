/**
 * poi-images.js — Real POI Image Loader (v7)
 *
 * Flow per card:
 *  1. Show shimmer skeleton immediately (non-blocking)
 *  2. Call backend  GET /api/poi-image?name=...&city=...
 *     - Backend queries DuckDuckGo and returns the best image URL
 *  3a. URL received → fade real photo in over the shimmer
 *  3b. No URL / error → render Letter Avatar (gradient + first letter)
 *
 * Public API (matches what destinations.js and index.html call):
 *   applyPoiImage(poi, imgWrapEl)   async, no return value
 */

/* ─────────────────────────────────────────────────────────────────────────────
   Constants
───────────────────────────────────────────────────────────────────────────── */

// Gradient pairs for the letter-avatar fallback, keyed by POI type
const _TYPE_GRADIENTS = {
    museum:    ['#667eea', '#764ba2'],
    culture:   ['#f093fb', '#f5576c'],
    nature:    ['#11998e', '#38ef7d'],
    food:      ['#f7971e', '#ffd200'],
    adventure: ['#4facfe', '#00f2fe'],
    shopping:  ['#43e97b', '#38f9d7'],
    history:   ['#c8a951', '#8B6914'],
    nightlife: ['#2c3e75', '#6b48c8'],
    default:   ['#667eea', '#764ba2'],
};

// In-memory result cache so the same POI never hits the backend twice
// key: "name|city"  value: { url: string|null }
const _imgCache = new Map();

/* ─────────────────────────────────────────────────────────────────────────────
   Private helpers
───────────────────────────────────────────────────────────────────────────── */

/** Resolve the ML-engine base URL from the global config or fall back. */
function _mlBase() {
    try { return API_CONFIG.ML_ENGINE_URL; } catch (_) {}
    return 'http://127.0.0.1:8000';
}

/**
 * Fetch DuckDuckGo image URL from the backend.
 * Returns { url: string|null }.
 */
async function _fetchPoiImageUrl(poi) {
    const cacheKey = `${poi.name}|${poi.city || ''}`;
    if (_imgCache.has(cacheKey)) return _imgCache.get(cacheKey);

    let result = { url: null };
    try {
        const qs = new URLSearchParams({ name: poi.name });
        if (poi.city) qs.set('city', poi.city);

        const res = await fetch(`${_mlBase()}/api/poi-image?${qs}`, {
            signal: AbortSignal.timeout(10000)   // 10 s client-side cut-off
        });
        if (res.ok) {
            const data = await res.json();
            result = { url: data.url || null };
        }
    } catch (_) {
        // network error or timeout → letter avatar
    }
    _imgCache.set(cacheKey, result);
    return result;
}

/** Render a Letter Avatar inside imgWrapEl (removes shimmer first). */
function _renderLetterAvatar(imgWrapEl, poi) {
    const shimmer = imgWrapEl.querySelector('.poi-shimmer');
    if (shimmer?.parentNode) shimmer.remove();

    const [c1, c2] = _TYPE_GRADIENTS[poi.type] || _TYPE_GRADIENTS.default;

    // First printable character — works for Hindi/Devanagari & Latin alike
    const letter = [...(poi.name || '?').trim()][0]?.toUpperCase() || '?';

    imgWrapEl.innerHTML = `
        <div style="
            width: 100%; height: 100%;
            background: linear-gradient(135deg, ${c1} 0%, ${c2} 100%);
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            user-select: none; pointer-events: none;
        ">
            <span style="
                font-size: clamp(2rem, 10cqw, 4rem);
                font-weight: 800;
                color: rgba(255,255,255,0.95);
                line-height: 1;
                text-shadow: 0 3px 12px rgba(0,0,0,.35);
                letter-spacing: -.02em;
            ">${letter}</span>
            <span style="
                font-size: .65rem;
                color: rgba(255,255,255,0.65);
                margin-top: .35rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: .12em;
            ">${poi.type || 'place'}</span>
        </div>`;
}

/** Fade a real photo in over the shimmer skeleton. */
function _renderPhoto(imgWrapEl, poi, url) {
    const shimmer = imgWrapEl.querySelector('.poi-shimmer');
    let imgEl = imgWrapEl.querySelector('.poi-photo');

    // Create <img> if the wrapper doesn't already have one
    if (!imgEl) {
        imgEl = document.createElement('img');
        imgEl.className = 'poi-photo';
        imgEl.alt = poi.name;
        imgEl.style.cssText =
            'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;display:block;';
        imgWrapEl.appendChild(imgEl);
    }

    const probe = new Image();
    probe.onload = () => {
        if (shimmer?.parentNode) shimmer.remove();
        imgEl.src = url;
        requestAnimationFrame(() => {
            imgEl.style.transition = 'opacity 0.45s ease';
            imgEl.style.opacity = '1';
        });
    };
    probe.onerror = () => _renderLetterAvatar(imgWrapEl, poi);
    probe.src = url;
}

/* ─────────────────────────────────────────────────────────────────────────────
   Public API
───────────────────────────────────────────────────────────────────────────── */

/**
 * Apply an image (or letter-avatar) to a .poi-img-wrap DOM element.
 * Called by destinations.js and index.html (_loadTeaserImages).
 *
 * @param {object} poi     - Must have: name, type. Optional: city.
 * @param {Element} imgWrapEl - The .poi-img-wrap container element.
 */
async function applyPoiImage(poi, imgWrapEl) {
    if (!imgWrapEl) return;

    const { url } = await _fetchPoiImageUrl(poi);

    if (url) {
        _renderPhoto(imgWrapEl, poi, url);
    } else {
        _renderLetterAvatar(imgWrapEl, poi);
    }
}
