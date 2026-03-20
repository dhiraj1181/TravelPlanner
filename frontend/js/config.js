/**
 * TravelPro - Configuration File
 * Contains API endpoints and application constants
 */

// API Configuration
const API_CONFIG = {
    // Backend Spring Boot API URL
    BACKEND_URL: 'http://localhost:8080/api',

    // ML Engine FastAPI URL
    ML_ENGINE_URL: 'http://localhost:8000',

    // API Endpoints
    ENDPOINTS: {
        // Authentication
        LOGIN: '/auth/login',
        REGISTER: '/auth/register',
        LOGOUT: '/auth/logout',

        // Trip Management
        CREATE_TRIP: '/trips/plan',
        GET_TRIPS: '/trips',
        GET_TRIP_BY_ID: '/trips/:id',
        UPDATE_TRIP: '/trips/:id',
        DELETE_TRIP: '/trips/:id',

        // ML Engine
        GENERATE_ITINERARY: '/generate_itinerary'
    }
};

// Application Constants
const APP_CONSTANTS = {
    // Local Storage Keys
    STORAGE_KEYS: {
        AUTH_TOKEN: 'authToken',
        USER_DATA: 'userData',
        USER_TRIPS: 'userTrips',
        TEMP_TRIP_DATA: 'tempTripData',
        WISHLIST: 'userWishlist'
    },

    // Form Validation
    MIN_BUDGET: 100,
    MAX_BUDGET: 100000,
    MIN_TRIP_DAYS: 1,
    MAX_TRIP_DAYS: 30,

    // Date Formats
    DATE_FORMAT: 'YYYY-MM-DD',

    // Interests Options
    INTERESTS: [
        { value: 'museum', label: 'Museums', icon: '🏛️' },
        { value: 'food', label: 'Food & Dining', icon: '🍜' },
        { value: 'adventure', label: 'Adventure', icon: '🏔️' },
        { value: 'culture', label: 'Culture', icon: '🎭' },
        { value: 'nature', label: 'Nature', icon: '🌳' },
        { value: 'shopping', label: 'Shopping', icon: '🛍️' },
        { value: 'nightlife', label: 'Nightlife', icon: '🌃' },
        { value: 'history', label: 'History', icon: '📜' }
    ]
};

// Mock Mode (for development without backend)
const MOCK_MODE = false; // Set to false when backend is ready

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG, APP_CONSTANTS, MOCK_MODE };
}
