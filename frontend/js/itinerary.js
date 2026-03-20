/**
 * TravelPro - Itinerary Display Module
 * Handles loading and rendering of generated itineraries
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeItineraryPage();
});

/**
 * Initialize itinerary page
 */
async function initializeItineraryPage() {
    // Get trip ID from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const tripId = urlParams.get('id');

    if (!tripId) {
        alert('No trip ID provided');
        window.location.href = 'dashboard.html';
        return;
    }

    try {
        // Load trip data
        const trip = await loadTripById(tripId);

        // Render itinerary
        renderItinerary(trip);

        // Hide loading, show content
        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('itineraryContent').classList.remove('hidden');

    } catch (error) {
        console.error('Error loading itinerary:', error);
        alert('Failed to load itinerary');
        window.location.href = 'dashboard.html';
    }
}

/**
 * Load trip by ID
 * @param {string} tripId - Trip ID
 * @returns {Promise<Object>} Trip data with itinerary
 */
async function loadTripById(tripId) {
    if (MOCK_MODE) {
        return mockLoadTrip(tripId);
    }

    // Real API call
    const token = getAuthToken();
    const endpoint = API_CONFIG.ENDPOINTS.GET_TRIP_BY_ID.replace(':id', tripId);
    const response = await fetch(`${API_CONFIG.BACKEND_URL}${endpoint}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        throw new Error('Failed to load trip');
    }

    return await response.json();
}

/**
 * Mock trip loading for development
 */
function mockLoadTrip(tripId) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const trips = JSON.parse(localStorage.getItem(APP_CONSTANTS.STORAGE_KEYS.USER_TRIPS) || '[]');
            const trip = trips.find(t => t.id == tripId);

            if (trip) {
                resolve(trip);
            } else {
                throw new Error('Trip not found');
            }
        }, 500);
    });
}

/**
 * Render complete itinerary
 * @param {Object} trip - Trip data with itinerary
 */
function renderItinerary(trip) {
    // Render header
    document.getElementById('tripTitle').textContent = trip.title || `Your Trip to ${trip.destination}`;

    // Render dates
    const startDate = formatDate(trip.startDate);
    const endDate = formatDate(trip.endDate);
    document.getElementById('tripDates').textContent = `${startDate} - ${endDate} (${trip.days} days)`;

    // Render budget status
    const budgetStatus = document.getElementById('budgetStatus');
    const budgetStatusText = document.getElementById('budgetStatusText');
    const estimatedCost = trip.itinerary.estimatedCost || 0;

    document.getElementById('totalBudget').textContent = trip.budget;
    document.getElementById('estimatedCost').textContent = estimatedCost;

    if (trip.itinerary.greenSignal) {
        budgetStatus.classList.add('success');
        budgetStatus.classList.remove('warning');
        budgetStatusText.textContent = 'Within Budget ✓';
    } else {
        budgetStatus.classList.add('warning');
        budgetStatus.classList.remove('success');
        budgetStatusText.textContent = 'Over Budget';
    }

    // Render day-by-day itinerary
    renderDayByDay(trip.itinerary.dayByDay, trip.destination);
}

/**
 * Render day-by-day itinerary sections
 * @param {Array} days - Array of day objects with POIs
 */
function renderDayByDay(days, destination) {
    const container = document.getElementById('itineraryDays');
    container.innerHTML = '';

    days.forEach((dayData, index) => {
        const daySection = createDaySection(dayData, index + 1, destination);
        container.appendChild(daySection);
    });
}

/**
 * Create a day section element
 * @param {Object} dayData - Day data with POIs
 * @param {number} dayNumber - Day number
 * @returns {HTMLElement} Day section element
 */
function createDaySection(dayData, dayNumber, destination) {
    const section = document.createElement('div');
    section.className = 'day-section';

    // Day header
    const header = document.createElement('div');
    header.className = 'day-header';
    header.innerHTML = `
        <div class="day-number">${dayNumber}</div>
        <div>
            <h3 style="margin: 0;">Day ${dayNumber}</h3>
            <p style="margin: 0; color: var(--color-gray-600); font-size: var(--font-size-sm);">
                ${formatDate(dayData.date)}
            </p>
        </div>
    `;
    section.appendChild(header);

    // POIs for this day
    const poisContainer = document.createElement('div');
    dayData.pois.forEach((poi, index) => {
        const poiCard = createPOICard(poi, index + 1, destination);
        poisContainer.appendChild(poiCard);
    });
    section.appendChild(poisContainer);

    return section;
}

/**
 * Create a POI (Point of Interest) card element
 * @param {Object} poi - POI data
 * @param {number} order - Order in the day
 * @returns {HTMLElement} POI card element
 */
function createPOICard(poi, order, destination) {
    const card = document.createElement('div');
    card.className = 'poi-card';

    card.innerHTML = `
        <div class="poi-order">${order}</div>
        <div class="poi-details">
            <div class="poi-name">${poi.name}</div>
            <div class="poi-meta">
                ${poi.type ? `
                    <span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 4px;">
                            <path d="M20 10C20 16 12 22 12 22C12 22 4 16 4 10C4 7.87827 4.84285 5.84344 6.34315 4.34315C7.84344 2.84285 9.87827 2 12 2C14.1217 2 16.1566 2.84285 17.6569 4.34315C19.1571 5.84344 20 7.87827 20 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M12 13C13.6569 13 15 11.6569 15 10C15 8.34315 13.6569 7 12 7C10.3431 7 9 8.34315 9 10C9 11.6569 10.3431 13 12 13Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        ${capitalizeFirst(poi.type)}
                    </span>
                ` : ''}
                ${poi.duration ? `
                    <span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 4px;">
                            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                            <path d="M12 6V12L16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                        ${poi.duration} hrs
                    </span>
                ` : ''}
                ${poi.cost ? `
                    <span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; margin-right: 4px;">
                            <line x1="12" y1="1" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            <path d="M17 5H9.5C7.01472 5 5 7.01472 5 9.5C5 11.9853 7.01472 14 9.5 14H14.5C16.9853 14 19 16.0147 19 18.5C19 20.9853 16.9853 23 14.5 23H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        ₹${poi.cost}
                    </span>
                ` : ''}
            </div>
        </div>
    `;

    // Add wishlist heart button — inlined POI data for the wishlist module
    const wishPoi = {
        name: poi.name,
        type: poi.type || 'culture',
        city: destination || '',
        cost: poi.cost || 0,
        duration: poi.duration || 2
    };
    card.appendChild(createWishlistButton(wishPoi));

    return card;
}

/**
 * Capitalize first letter of string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Format date to readable string (from app.js)
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}
