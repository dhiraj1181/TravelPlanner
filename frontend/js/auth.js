/**
 * TravelPro - Authentication Module
 * Handles user login, registration, and session management
 */

/**
 * Handle user login
 * @param {Object} credentials - {email, password}
 * @returns {Promise<Object>} User data and token
 */
async function login(credentials) {
    try {
        if (MOCK_MODE) {
            // Mock login for development
            return mockLogin(credentials);
        }

        // Real API call
        const response = await fetch(`${API_CONFIG.BACKEND_URL}${API_CONFIG.ENDPOINTS.LOGIN}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();

        // Store authentication data
        localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.AUTH_TOKEN, data.token);
        localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));

        return data;
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}

/**
 * Mock login function for development
 */
function mockLogin(credentials) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const mockUser = {
                id: 1,
                name: credentials.email.split('@')[0],
                email: credentials.email
            };

            const mockToken = 'mock-jwt-token-' + Date.now();

            // Store in localStorage
            localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.AUTH_TOKEN, mockToken);
            localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.USER_DATA, JSON.stringify(mockUser));

            resolve({
                token: mockToken,
                user: mockUser
            });
        }, 500); // Simulate network delay
    });
}

/**
 * Handle user registration
 * @param {Object} userData - {name, email, password}
 * @returns {Promise<Object>} User data and token
 */
async function register(userData) {
    try {
        if (MOCK_MODE) {
            // Mock registration for development
            return mockRegister(userData);
        }

        // Real API call
        const response = await fetch(`${API_CONFIG.BACKEND_URL}${API_CONFIG.ENDPOINTS.REGISTER}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            throw new Error('Registration failed');
        }

        const data = await response.json();

        // Store authentication data
        localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.AUTH_TOKEN, data.token);
        localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));

        return data;
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
}

/**
 * Mock registration function for development
 */
function mockRegister(userData) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const mockUser = {
                id: Date.now(),
                name: userData.name,
                email: userData.email
            };

            const mockToken = 'mock-jwt-token-' + Date.now();

            // Store in localStorage
            localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.AUTH_TOKEN, mockToken);
            localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.USER_DATA, JSON.stringify(mockUser));

            resolve({
                token: mockToken,
                user: mockUser
            });
        }, 500);
    });
}

/**
 * Handle user logout
 */
function logout() {
    // Clear all stored data
    localStorage.removeItem(APP_CONSTANTS.STORAGE_KEYS.AUTH_TOKEN);
    localStorage.removeItem(APP_CONSTANTS.STORAGE_KEYS.USER_DATA);
    localStorage.removeItem(APP_CONSTANTS.STORAGE_KEYS.USER_TRIPS);

    // Redirect to home page
    window.location.href = 'index.html';
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
function isAuthenticated() {
    const token = localStorage.getItem(APP_CONSTANTS.STORAGE_KEYS.AUTH_TOKEN);
    return !!token;
}

/**
 * Get current user data
 * @returns {Object|null}
 */
function getCurrentUser() {
    const userData = localStorage.getItem(APP_CONSTANTS.STORAGE_KEYS.USER_DATA);
    return userData ? JSON.parse(userData) : null;
}

/**
 * Get authentication token
 * @returns {string|null}
 */
function getAuthToken() {
    return localStorage.getItem(APP_CONSTANTS.STORAGE_KEYS.AUTH_TOKEN);
}

// Export functions for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        login,
        register,
        logout,
        isAuthenticated,
        getCurrentUser,
        getAuthToken
    };
}
