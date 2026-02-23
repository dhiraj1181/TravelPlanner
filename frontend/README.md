# Frontend - TravelPro UI

Responsive web interface for trip planning.

## Run

Open `index.html` in your browser.

## Pages

- `index.html` - Landing page with auth
- `dashboard.html` - User dashboard
- `create-trip.html` - Multi-step trip planning form
- `itinerary.html` - Day-by-day itinerary view

## Configuration

Update `js/config.js` to change API endpoints:
```javascript
const API_CONFIG = {
    BACKEND_URL: 'http://localhost:8080/api',
    ML_ENGINE_URL: 'http://localhost:8000'
};

const MOCK_MODE = false; // true for demo without backend
```

## Structure

```
frontend/
├── index.html              # Landing page
├── dashboard.html          # User dashboard
├── create-trip.html        # Trip planner
├── itinerary.html          # Itinerary display
├── css/
│   ├── styles.css         # Global styles
│   └── components.css     # Component styles
└── js/
    ├── config.js          # API configuration
    ├── auth.js            # Authentication
    └── app.js             # Main logic
```

## Tech

- Vanilla JavaScript
- CSS3 with animations
- Google Fonts (Inter, Playfair Display)
