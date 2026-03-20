/**
 * wishlist.js — Shared Wishlist Module
 * Stores wishlisted POIs in localStorage, scoped per user ID.
 * Used by: destinations.js (add/remove buttons) and wishlist.html (display)
 */

// ── Storage helpers ─────────────────────────────────────────────────────────
function _getUserId() {
    const u = JSON.parse(localStorage.getItem(APP_CONSTANTS.STORAGE_KEYS.USER_DATA) || '{}');
    return u.id ? String(u.id) : 'guest';
}

function _storageKey() {
    return `${APP_CONSTANTS.STORAGE_KEYS.WISHLIST}_${_getUserId()}`;
}

/**
 * Return the full wishlist array for the current user.
 * Each item: { id, name, type, city, cost, duration, wikipedia, wikidata, addedAt }
 */
function getWishlist() {
    try {
        return JSON.parse(localStorage.getItem(_storageKey()) || '[]');
    } catch (_) { return []; }
}

/**
 * Save wishlist array back to storage.
 */
function _saveWishlist(list) {
    localStorage.setItem(_storageKey(), JSON.stringify(list));
}

/**
 * Check if a POI is already wishlisted (by unique composite id).
 */
function isWishlisted(poi) {
    const id = _poiId(poi);
    return getWishlist().some(w => w.id === id);
}

/**
 * Add a POI to the wishlist. Returns true if added, false if already present.
 */
function addToWishlist(poi) {
    const list = getWishlist();
    const id = _poiId(poi);
    if (list.some(w => w.id === id)) return false;
    list.push({
        id,
        name: poi.name,
        type: poi.type || 'default',
        city: poi.city || '',
        cost: poi.cost || 0,
        duration: poi.duration || 2,
        wikipedia: poi.wikipedia || '',
        wikidata: poi.wikidata || '',
        addedAt: new Date().toISOString()
    });
    _saveWishlist(list);
    return true;
}

/**
 * Remove a POI from the wishlist. Returns true if removed.
 */
function removeFromWishlist(poi) {
    const id = _poiId(poi);
    const list = getWishlist().filter(w => w.id !== id);
    _saveWishlist(list);
    return true;
}

/**
 * Toggle wishlist status. Returns 'added' or 'removed'.
 */
function toggleWishlist(poi) {
    if (isWishlisted(poi)) {
        removeFromWishlist(poi);
        return 'removed';
    } else {
        addToWishlist(poi);
        return 'added';
    }
}

/**
 * Build a stable unique ID for a POI.
 * Uses name + type + city to avoid collisions between same-named places.
 */
function _poiId(poi) {
    return `${(poi.name || '').trim().toLowerCase()}|${poi.type || ''}|${(poi.city || '').toLowerCase()}`;
}

// ── Heart button builder (reused in destinations.js) ────────────────────────

/**
 * Create a heart wishlist button for a POI card.
 * Precondition: config.js and auth.js must already be loaded.
 */
function createWishlistButton(poi) {
    const wishlisted = isWishlisted(poi);
    const btn = document.createElement('button');
    btn.className = 'wishlist-btn' + (wishlisted ? ' wishlisted' : '');
    btn.title = wishlisted ? 'Remove from Wishlist' : 'Add to Wishlist';
    btn.setAttribute('aria-label', btn.title);
    btn.innerHTML = _heartSvg(wishlisted);

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const action = toggleWishlist(poi);
        const isNowWishlisted = action === 'added';
        btn.classList.toggle('wishlisted', isNowWishlisted);
        btn.title = isNowWishlisted ? 'Remove from Wishlist' : 'Add to Wishlist';
        btn.innerHTML = _heartSvg(isNowWishlisted);
        _showWishlistFeedback(btn, action);
    });

    return btn;
}

function _heartSvg(filled) {
    const fillColor = filled ? '#ef4444' : 'none';
    const strokeColor = filled ? '#ef4444' : 'currentColor';
    return `<svg width="18" height="18" viewBox="0 0 24 24" fill="${fillColor}"
        xmlns="http://www.w3.org/2000/svg">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
        stroke="${strokeColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
}

// Mini floating toast anchored near the button
function _showWishlistFeedback(btn, action) {
    const tip = document.createElement('div');
    tip.className = 'wishlist-tip';
    tip.textContent = action === 'added' ? '❤️ Wishlisted!' : '💔 Removed';
    btn.parentElement.appendChild(tip);
    setTimeout(() => tip.classList.add('visible'), 10);
    setTimeout(() => {
        tip.classList.remove('visible');
        setTimeout(() => tip.remove(), 300);
    }, 1600);
}
