/**
 * TravelPro - Destinations Discovery Module
 * Fetches places from OpenStreetMap based on city name and interests
 */

let selectedInterests = [];
let allDestinations = [];
let currentCity = '';

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeDestinations();
});

/**
 * Initialize destinations page
 */
function initializeDestinations() {
    // Check authentication - redirect if not logged in
    const authToken = getAuthToken();
    const userData = getCurrentUser();

    if (!authToken || !userData) {
        console.log('User not authenticated, redirecting to home page');
        window.location.href = 'index.html';
        return;
    }

    // Load user data into sidebar
    loadUserDataInSidebar();

    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Setup interest filters
    setupInterestFilters();

    // Setup city search
    setupCitySearch();
}

/**
 * Setup city search functionality
 */
function setupCitySearch() {
    const searchBtn = document.getElementById('searchBtn');
    const cityInput = document.getElementById('cityInput');

    // Search on button click
    if (searchBtn) {
        searchBtn.addEventListener('click', function () {
            const city = cityInput.value.trim();
            if (city) {
                searchPlacesInCity(city);
            } else {
                alert('Please enter a city name');
            }
        });
    }

    // Search on Enter key
    if (cityInput) {
        cityInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                const city = cityInput.value.trim();
                if (city) {
                    searchPlacesInCity(city);
                }
            }
        });
    }
}

/**
 * Search for places in a city using OSM via ML Engine
 */
async function searchPlacesInCity(city) {
    currentCity = city;
    const container = document.getElementById('destinationsContainer');
    container.innerHTML = `<div class="loading-spinner"><p>🔍 Finding best places in ${city}...</p></div>`;

    try {
        console.log(`Searching for places in ${city}`);

        // Call ML Engine to get POIs from OSM
        // Send empty interests to get diverse selection
        const response = await fetch('http://localhost:8000/get_pois', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                destination: city,
                interests: selectedInterests.length > 0 ? selectedInterests : []
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error:', errorText);
            throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();
        console.log('Received POIs:', data);

        if (data.pois && data.pois.length > 0) {
            // Normalize POI data
            allDestinations = data.pois.map(poi => ({
                name: poi.name,
                type: poi.type,
                cost: poi.cost || 0,
                duration: poi.duration || 2,
                distance: Math.random() * 30 + 5, // Mock distance
                interests: poi.interests || [poi.type],
                icon: getIconForType(poi.type),
                lat: poi.lat,
                lon: poi.lon
            }));

            filterAndDisplayDestinations();
        } else {
            showEmptyState(`No places found in ${city}. Try a different city name.`);
        }

    } catch (error) {
        console.error('Error fetching places:', error);
        showErrorState(`Unable to fetch places for ${city}. Make sure the ML engine is running.`);
    }
}

/**
 * Calculate approximate distance (mock for now, could use geocoding)
 */
function calculateApproxDistance(poi) {
    // Return random distance for now
    // In production, this would calculate from city center coordinates
    return Math.random() * 30 + 5; // 5-35 km
}

/**
 * Show empty state message
 */
function showEmptyState(message) {
    const container = document.getElementById('destinationsContainer');
    container.innerHTML = `
        <div class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2ZM12 11.5C10.62 11.5 9.5 10.38 9.5 9C9.5 7.62 10.62 6.5 12 6.5C13.38 6.5 14.5 7.62 14.5 9C14.5 10.38 13.38 11.5 12 11.5Z" fill="currentColor"/>
            </svg>
            <h3>No places found</h3>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Show error state message
 */
function showErrorState(message) {
    const container = document.getElementById('destinationsContainer');
    container.innerHTML = `
        <div class="empty-state" style="color: var(--color-error);">
            <h3>⚠️ Error</h3>
            <p>${message}</p>
        </div>
    `;
}

/**
 * Setup interest filter chips
 */
function setupInterestFilters() {
    const filterChips = document.querySelectorAll('.filter-chip');

    filterChips.forEach(chip => {
        chip.addEventListener('click', function () {
            const interest = this.dataset.interest;

            // Toggle active state
            this.classList.toggle('active');

            // Update selected interests
            if (this.classList.contains('active')) {
                selectedInterests.push(interest);
            } else {
                selectedInterests = selectedInterests.filter(i => i !== interest);
            }

            // If we have a current city, re-search with new filters
            if (currentCity) {
                searchPlacesInCity(currentCity);
            }
        });
    });
}

/**
 * Filter and display destinations based on selected interests
 */
function filterAndDisplayDestinations() {
    let filtered = allDestinations;

    // Filter by selected interests (if any are selected)
    if (selectedInterests.length > 0) {
        filtered = allDestinations.filter(dest =>
            dest.interests.some(interest => selectedInterests.includes(interest))
        );
    }

    // Sort by distance
    filtered.sort((a, b) => a.distance - b.distance);

    displayDestinations(filtered);
}

/**
 * Display destinations in grid
 */
function displayDestinations(destinations) {
    const container = document.getElementById('destinationsContainer');

    if (destinations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2ZM12 11.5C10.62 11.5 9.5 10.38 9.5 9C9.5 7.62 10.62 6.5 12 6.5C13.38 6.5 14.5 7.62 14.5 9C14.5 10.38 13.38 11.5 12 11.5Z" fill="currentColor"/>
                </svg>
                <h3>No destinations found</h3>
                <p>Try selecting different interests or check back later</p>
            </div>
        `;
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'destinations-grid';

    destinations.forEach(dest => {
        const card = createDestinationCard(dest);
        grid.appendChild(card);
    });

    container.innerHTML = '';
    container.appendChild(grid);

    console.log(`Displayed ${destinations.length} destinations`);
}

/**
 * Create destination card element
 */
function createDestinationCard(destination) {
    const card = document.createElement('div');
    card.className = 'destination-card';

    card.innerHTML = `
        <div class="destination-image">
            ${destination.icon}
        </div>
        <div class="destination-content">
            <h3 class="destination-title">${destination.name}</h3>
            <span class="destination-type">${getTypeLabel(destination.type)}</span>
            <div class="destination-meta">
                <div class="destination-meta-item">
                    ⏱️ ${destination.duration || 2} hours
                </div>
                ${destination.cost > 0 ? `
                <div class="destination-meta-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2"/>
                        <path d="M17 5H9.5C7.01472 5 5 7.01472 5 9.5C5 11.9853 7.01472 14 9.5 14H14.5C16.9853 14 19 16.0147 19 18.5C19 20.9853 16.9853 23 14.5 23H6" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    ₹${destination.cost}
                </div>
                ` : '<div class="destination-meta-item">🆓 Free</div>'}
            </div>
        </div>
    `;

    return card;
}

/**
 * Get icon emoji for destination type
 */
function getIconForType(type) {
    const icons = {
        'museum': '🏛️',
        'food': '🍜',
        'culture': '🎭',
        'nature': '🌳',
        'shopping': '🛍️',
        'adventure': '🏔️',
        'history': '📜',
        'nightlife': '🌃'
    };
    return icons[type] || '📍';
}

/**
 * Get readable label for type
 */
function getTypeLabel(type) {
    const labels = {
        'museum': 'Museum',
        'food': 'Food & Dining',
        'culture': 'Cultural',
        'nature': 'Nature',
        'shopping': 'Shopping',
        'adventure': 'Adventure',
        'history': 'Historical',
        'nightlife': 'Nightlife'
    };
    return labels[type] || type;
}

/**
 * Load user data into sidebar
 */
function loadUserDataInSidebar() {
    const userData = getCurrentUser();
    if (userData) {
        const userNameEl = document.getElementById('userName');
        const userEmailEl = document.getElementById('userEmail');
        const userAvatarEl = document.getElementById('userAvatar');

        if (userNameEl) userNameEl.textContent = userData.name;
        if (userEmailEl) userEmailEl.textContent = userData.email;
        if (userAvatarEl) userAvatarEl.textContent = userData.name.charAt(0).toUpperCase();
    }
}
