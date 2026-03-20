/**
 * TravelPro - Trip Planner Module
 * Handles multi-step trip creation wizard logic
 */

// Current step tracking
let currentStep = 1;
const totalSteps = 3;

// Trip form data
let tripData = {};

// Initialize trip planner when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeTripPlanner();
});

/**
 * Initialize trip creation wizard
 */
function initializeTripPlanner() {
    // Load user data into sidebar (if not already loaded)
    loadUserDataInSidebar();

    // Setup step navigation
    setupStepNavigation();

    // Setup interest checkboxes
    setupInterestSelection();

    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Load any saved form data
    loadSavedFormData();
}

/**
 * Setup step navigation (Previous/Next buttons)
 */
function setupStepNavigation() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const form = document.getElementById('tripForm');

    // Next button click
    nextBtn.addEventListener('click', function () {
        if (validateCurrentStep()) {
            saveCurrentStepData();

            if (currentStep < totalSteps) {
                goToStep(currentStep + 1);
            } else {
                // Final step - submit form
                submitTripForm();
            }
        }
    });

    // Previous button click
    prevBtn.addEventListener('click', function () {
        if (currentStep > 1) {
            saveCurrentStepData();
            goToStep(currentStep - 1);
        }
    });
}

/**
 * Navigate to a specific step
 * @param {number} stepNumber - Step to navigate to
 */
function goToStep(stepNumber) {
    // Hide all steps
    const steps = document.querySelectorAll('.step-content');
    steps.forEach(step => step.classList.remove('active'));

    // Show target step
    const targetStep = document.querySelector(`.step-content[data-step="${stepNumber}"]`);
    if (targetStep) {
        targetStep.classList.add('active');
    }

    // Update progress indicator
    updateProgressIndicator(stepNumber);

    // Update navigation buttons
    updateNavigationButtons(stepNumber);

    // Update current step
    currentStep = stepNumber;
}

/**
 * Update progress indicator visual state
 * @param {number} stepNumber - Current step number
 */
function updateProgressIndicator(stepNumber) {
    const progressSteps = document.querySelectorAll('.progress-step');

    progressSteps.forEach((step, index) => {
        const stepNum = index + 1;

        if (stepNum < stepNumber) {
            // Completed step
            step.classList.add('completed');
            step.classList.remove('active');
        } else if (stepNum === stepNumber) {
            // Active step
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            // Future step
            step.classList.remove('active', 'completed');
        }
    });
}

/**
 * Update navigation button states
 * @param {number} stepNumber - Current step number
 */
function updateNavigationButtons(stepNumber) {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    // Show/hide Previous button
    if (stepNumber === 1) {
        prevBtn.style.visibility = 'hidden';
    } else {
        prevBtn.style.visibility = 'visible';
    }

    // Update Next button text
    if (stepNumber === totalSteps) {
        nextBtn.innerHTML = `
            Generate Itinerary
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 13L9 17L19 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
    } else {
        nextBtn.innerHTML = `
            Next
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
    }
}

/**
 * Validate current step inputs
 * @returns {boolean} - Whether current step is valid
 */
function validateCurrentStep() {
    console.log(`Validating step ${currentStep}`);
    const currentStepElement = document.querySelector(`.step-content[data-step="${currentStep}"]`);

    // Get all required inputs in current step
    const requiredInputs = currentStepElement.querySelectorAll('input[required], select[required]');

    let isValid = true;

    requiredInputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('error');
            isValid = false;
            console.log(`Validation failed: ${input.id || input.name} is empty`);
        } else {
            input.classList.remove('error');
        }
    });

    // Step-specific validation
    if (currentStep === 2) {
        // Validate dates
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);

            if (end < start) {
                alert('End date must be after start date');
                document.getElementById('endDate').classList.add('error');
                isValid = false;
                console.log('Validation failed: End date before start date');
            }
        }

        // Validate budget
        const budgetValue = document.getElementById('budget').value;
        console.log('Budget value:', budgetValue, 'Type:', typeof budgetValue);

        if (budgetValue) {
            const budget = parseInt(budgetValue);
            console.log('Parsed budget:', budget, 'MIN_BUDGET:', APP_CONSTANTS.MIN_BUDGET);

            if (budget < APP_CONSTANTS.MIN_BUDGET) {
                alert(`Budget must be at least ₹${APP_CONSTANTS.MIN_BUDGET}`);
                document.getElementById('budget').classList.add('error');
                isValid = false;
                console.log(`Validation failed: Budget ${budget} is less than minimum ${APP_CONSTANTS.MIN_BUDGET}`);
            }
        }
    }

    if (currentStep === 3) {
        // Validate at least one interest selected
        const selectedInterests = document.querySelectorAll('input[name="interests"]:checked');
        const errorMsg = document.getElementById('interestError');

        if (selectedInterests.length === 0) {
            errorMsg.classList.remove('hidden');
            isValid = false;
            console.log('Validation failed: No interests selected');
        } else {
            errorMsg.classList.add('hidden');
        }
    }

    console.log(`Step ${currentStep} validation result: ${isValid}`);
    return isValid;
}

/**
 * Calculate number of days between two dates
 * @param {string} startDate - Start date in YYYY-MM-DD format
 * @param {string} endDate - End date in YYYY-MM-DD format
 * @returns {number} Number of days
 */
function calculateDays(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays + 1; // Include both start and end day
}

/**
 * Save current step data to tripData object
 */
function saveCurrentStepData() {
    if (currentStep === 1) {
        tripData.destination = document.getElementById('destination').value;
        tripData.title = document.getElementById('tripTitle').value;
    } else if (currentStep === 2) {
        tripData.startDate = document.getElementById('startDate').value;
        tripData.endDate = document.getElementById('endDate').value;
        tripData.budget = parseInt(document.getElementById('budget').value);

        // Calculate days
        const days = calculateDays(tripData.startDate, tripData.endDate);
        tripData.days = days;
    } else if (currentStep === 3) {
        const selectedInterests = [];
        document.querySelectorAll('input[name="interests"]:checked').forEach(checkbox => {
            selectedInterests.push(checkbox.value);
        });
        tripData.interests = selectedInterests;
    }

    // Save to localStorage
    localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.TEMP_TRIP_DATA, JSON.stringify(tripData));
}

/**
 * Load saved form data from localStorage
 */
function loadSavedFormData() {
    const savedData = localStorage.getItem(APP_CONSTANTS.STORAGE_KEYS.TEMP_TRIP_DATA);
    if (savedData) {
        tripData = JSON.parse(savedData);

        // Populate form fields
        if (tripData.destination) document.getElementById('destination').value = tripData.destination;
        if (tripData.title) document.getElementById('tripTitle').value = tripData.title;
        if (tripData.startDate) document.getElementById('startDate').value = tripData.startDate;
        if (tripData.endDate) document.getElementById('endDate').value = tripData.endDate;
        if (tripData.budget) document.getElementById('budget').value = tripData.budget;

        if (tripData.interests && tripData.interests.length > 0) {
            tripData.interests.forEach(interest => {
                const checkbox = document.querySelector(`input[name="interests"][value="${interest}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                    checkbox.parentElement.classList.add('checked');
                }
            });
        }
    }
}

/**
 * Setup interest checkbox selection with visual feedback
 */
function setupInterestSelection() {
    const interestOptions = document.querySelectorAll('.interest-option');

    interestOptions.forEach(option => {
        const checkbox = option.querySelector('input[type="checkbox"]');

        option.addEventListener('click', function (e) {
            // Toggle checkbox if clicking on label
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }

            // Update visual state
            if (checkbox.checked) {
                option.classList.add('checked');
            } else {
                option.classList.remove('checked');
            }
        });
    });
}

/**
 * Submit trip creation form
 */
async function submitTripForm() {
    try {
        // Show loading state
        const nextBtn = document.getElementById('nextBtn');
        nextBtn.disabled = true;
        nextBtn.textContent = 'Generating itinerary...';

        // Save trip to backend - backend will call ML engine
        const savedTrip = await saveTripToBackend({
            destination: tripData.destination,
            title: tripData.title,
            startDate: tripData.startDate,
            endDate: tripData.endDate,
            budget: tripData.budget,
            interests: tripData.interests
        });

        // Clear temp data
        localStorage.removeItem(APP_CONSTANTS.STORAGE_KEYS.TEMP_TRIP_DATA);

        // Redirect to itinerary view
        window.location.href = `itinerary.html?id=${savedTrip.id}`;

    } catch (error) {
        console.error('Error creating trip:', error);
        alert('Failed to generate itinerary. Please try again.');

        // Restore button
        const nextBtn = document.getElementById('nextBtn');
        nextBtn.disabled = false;
        updateNavigationButtons(currentStep);
    }
}

/**
 * Call ML engine to generate itinerary
 * @param {Object} tripData - Trip parameters
 * @returns {Promise<Object>} Generated itinerary
 */
async function generateItinerary(tripData) {
    if (MOCK_MODE) {
        return mockGenerateItinerary(tripData);
    }

    // Real API call to ML engine
    const response = await fetch(`${API_CONFIG.ML_ENGINE_URL}${API_CONFIG.ENDPOINTS.GENERATE_ITINERARY}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(tripData)
    });

    if (!response.ok) {
        throw new Error('Failed to generate itinerary');
    }

    return await response.json();
}

/**
 * Mock itinerary generation for development
 */
function mockGenerateItinerary(tripData) {
    return new Promise((resolve) => {
        setTimeout(() => {
            // Generate mock itinerary
            const itinerary = {
                destination: tripData.destination,
                days: tripData.days,
                totalBudget: tripData.budget,
                estimatedCost: Math.floor(tripData.budget * 0.9), // 90% of budget
                greenSignal: true,
                dayByDay: []
            };

            // Generate day-by-day itinerary
            for (let day = 1; day <= tripData.days; day++) {
                const pois = [];
                const numPois = Math.floor(Math.random() * 3) + 3; // 3-5 POIs per day

                for (let i = 0; i < numPois; i++) {
                    pois.push({
                        name: `Attraction ${i + 1} - Day ${day}`,
                        type: tripData.interests[Math.floor(Math.random() * tripData.interests.length)],
                        cost: Math.floor(Math.random() * 50) + 10,
                        duration: Math.floor(Math.random() * 3) + 1,
                        lat: 48.8566 + (Math.random() - 0.5) * 0.1,
                        lon: 2.3522 + (Math.random() - 0.5) * 0.1
                    });
                }

                itinerary.dayByDay.push({
                    day: day,
                    date: new Date(new Date(tripData.startDate).getTime() + (day - 1) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                    pois: pois
                });
            }

            resolve(itinerary);
        }, 2000); // Simulate processing time
    });
}

/**
 * Save trip to backend
 * @param {Object} tripData - Complete trip data with itinerary
 * @returns {Promise<Object>} Saved trip with ID
 */
async function saveTripToBackend(tripData) {
    if (MOCK_MODE) {
        return mockSaveTrip(tripData);
    }

    // Real API call to backend
    const token = getAuthToken();
    const user = getCurrentUser();
    const response = await fetch(`${API_CONFIG.BACKEND_URL}${API_CONFIG.ENDPOINTS.CREATE_TRIP}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-User-Id': user ? String(user.id) : ''
        },
        body: JSON.stringify(tripData)
    });

    if (!response.ok) {
        throw new Error('Failed to save trip');
    }

    return await response.json();
}

/**
 * Mock save trip for development
 */
function mockSaveTrip(tripData) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const trip = {
                id: Date.now(),
                ...tripData,
                createdAt: new Date().toISOString()
            };

            // Save to localStorage
            const trips = JSON.parse(localStorage.getItem(APP_CONSTANTS.STORAGE_KEYS.USER_TRIPS) || '[]');
            trips.push(trip);
            localStorage.setItem(APP_CONSTANTS.STORAGE_KEYS.USER_TRIPS, JSON.stringify(trips));

            resolve(trip);
        }, 500);
    });
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
