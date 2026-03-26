/**
 * TravelPro - Main Application JavaScript
 * Handles landing page interactions and modal controls
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeLandingPage();
});

/**
 * Initialize landing page functionality
 */
function initializeLandingPage() {
    const authModal = document.getElementById('authModal');
    // Support both old (getStartedBtn) and new (planTripBtn) homepage button IDs
    const triggerBtn = document.getElementById('planTripBtn') || document.getElementById('getStartedBtn');
    const startPlanningBtn = document.getElementById('startPlanningBtn');
    const closeModalBtn = document.getElementById('closeAuthModal');

    if (!authModal) return; // Not on a page with auth modal

    // Open modal on CTA click
    if (triggerBtn) {
        triggerBtn.addEventListener('click', function () {
            openAuthModal();
        });
    }
    if (startPlanningBtn) {
        startPlanningBtn.addEventListener('click', openAuthModal);
    }

    // Close modal
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeAuthModalFn);
    }
    authModal.addEventListener('click', function (e) {
        if (e.target === authModal) closeAuthModalFn();
    });

    setupAuthTabs();
    setupAuthForms();
}

/**
 * Open authentication modal
 */
function openAuthModal() {
    const authModal = document.getElementById('authModal');
    authModal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open
}

/**
 * Close authentication modal
 */
function closeAuthModalFn() {
    const authModal = document.getElementById('authModal');
    authModal.classList.remove('active');
    document.body.style.overflow = ''; // Restore scrolling
}

/**
 * Setup authentication tab switching
 */
function setupAuthTabs() {
    const tabs = document.querySelectorAll('.auth-tab');
    const tabContents = document.querySelectorAll('.auth-tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            const targetTab = this.getAttribute('data-tab');

            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));

            // Add active class to clicked tab
            this.classList.add('active');

            // Show corresponding content
            const targetContent = document.getElementById(targetTab + 'Tab');
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

/**
 * Setup authentication form submissions
 */
function setupAuthForms() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // Login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const errorEl = document.getElementById('loginError');
            if (errorEl) errorEl.textContent = '';

            const formData = new FormData(loginForm);
            const credentials = {
                email: formData.get('email'),
                password: formData.get('password')
            };

            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Logging in...';
            submitBtn.disabled = true;

            try {
                await login(credentials);
                // Redirect: if user typed a destination on homepage, go to create-trip
                const dest = sessionStorage.getItem('prefilledDestination');
                window.location.href = dest ? 'create-trip.html' : 'dashboard.html';
            } catch (error) {
                if (errorEl) errorEl.textContent = 'Invalid email or password. Please try again.';
                else alert('Login failed. Please check your credentials.');
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Register form submission
    if (registerForm) {
        registerForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const errorEl = document.getElementById('registerError');
            if (errorEl) errorEl.textContent = '';

            const formData = new FormData(registerForm);
            const password = formData.get('password');
            const confirmPassword = formData.get('confirmPassword');

            if (password !== confirmPassword) {
                if (errorEl) errorEl.textContent = 'Passwords do not match!';
                else alert('Passwords do not match!');
                return;
            }

            const userData = {
                name: formData.get('name'),
                email: formData.get('email'),
                password: password
            };

            const submitBtn = registerForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Creating account...';
            submitBtn.disabled = true;

            try {
                await register(userData);
                // Redirect: if user typed a destination on homepage, go to create-trip
                const dest = sessionStorage.getItem('prefilledDestination');
                window.location.href = dest ? 'create-trip.html' : 'dashboard.html';
            } catch (error) {
                if (errorEl) errorEl.textContent = 'Registration failed. Please try again.';
                else alert('Registration failed. Please try again.');
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
}

/**
 * Load hero image with placeholder
 */
function loadHeroImage() {
    const heroImage = document.getElementById('heroImage');
    if (heroImage) {
        // If actual image doesn't exist, create a gradient placeholder
        heroImage.onerror = function () {
            this.style.display = 'none';
            const placeholder = document.createElement('div');
            placeholder.style.cssText = `
                width: 100%;
                height: 500px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: var(--radius-2xl);
                box-shadow: var(--shadow-2xl);
            `;
            this.parentNode.appendChild(placeholder);
        };
    }
}

/**
 * Show toast notification (utility function)
 * @param {string} message - Message to display
 * @param {string} type - Type of notification (success, error, info)
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background-color: ${type === 'success' ? 'var(--color-success)' : type === 'error' ? 'var(--color-error)' : 'var(--color-info)'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        animation: slideInUp 0.3s ease-out;
    `;

    document.body.appendChild(toast);

    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

/**
 * Format date to readable string
 * @param {string} dateString - Date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Calculate number of days between two dates
 * @param {string} startDate - Start date string
 * @param {string} endDate - End date string
 * @returns {number} Number of days
 */
function calculateDays(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays + 1; // Include both start and end days
}
