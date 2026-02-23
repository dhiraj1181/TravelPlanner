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
    // Get modal and trigger elements
    const authModal = document.getElementById('authModal');
    const getStartedBtn = document.getElementById('getStartedBtn');
    const startPlanningBtn = document.getElementById('startPlanningBtn');
    const closeAuthModal = document.getElementById('closeAuthModal');

    // Check if elements exist (landing page)
    if (authModal && getStartedBtn) {
        // Open modal when "Get Started" button is clicked
        getStartedBtn.addEventListener('click', function () {
            openAuthModal();
        });

        // Open modal when "Start Planning" button is clicked
        if (startPlanningBtn) {
            startPlanningBtn.addEventListener('click', function () {
                openAuthModal();
            });
        }

        // Close modal when X button is clicked
        closeAuthModal.addEventListener('click', function () {
            closeAuthModalFn();
        });

        // Close modal when clicking outside
        authModal.addEventListener('click', function (e) {
            if (e.target === authModal) {
                closeAuthModalFn();
            }
        });

        // Setup auth tabs
        setupAuthTabs();

        // Setup auth forms
        setupAuthForms();

        // Load hero image
        loadHeroImage();
    }
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

            const formData = new FormData(loginForm);
            const credentials = {
                email: formData.get('email'),
                password: formData.get('password')
            };

            try {
                // Show loading state
                const submitBtn = loginForm.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Logging in...';
                submitBtn.disabled = true;

                // Call login function from auth.js
                const result = await login(credentials);

                // Success - redirect to dashboard
                window.location.href = 'dashboard.html';

            } catch (error) {
                // Show error message
                alert('Login failed. Please check your credentials and try again.');

                // Restore button state
                const submitBtn = loginForm.querySelector('button[type="submit"]');
                submitBtn.textContent = 'Login';
                submitBtn.disabled = false;
            }
        });
    }

    // Register form submission
    if (registerForm) {
        registerForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const formData = new FormData(registerForm);
            const password = formData.get('password');
            const confirmPassword = formData.get('confirmPassword');

            // Validate password match
            if (password !== confirmPassword) {
                alert('Passwords do not match!');
                return;
            }

            const userData = {
                name: formData.get('name'),
                email: formData.get('email'),
                password: password
            };

            try {
                // Show loading state
                const submitBtn = registerForm.querySelector('button[type="submit"]');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Registering...';
                submitBtn.disabled = true;

                // Call register function from auth.js
                const result = await register(userData);

                // Success - redirect to dashboard
                window.location.href = 'dashboard.html';

            } catch (error) {
                // Show error message
                alert('Registration failed. Please try again.');

                // Restore button state
                const submitBtn = registerForm.querySelector('button[type="submit"]');
                submitBtn.textContent = 'Register';
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
