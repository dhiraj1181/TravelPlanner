# TravelPro - AI-Powered Travel Planning System

Smart travel itinerary planner that generates optimized day-by-day schedules using ML algorithms.

## Architecture

- **Frontend**: HTML/CSS/JavaScript
- **Backend**: Spring Boot (Java) + MySQL
- **ML Engine**: FastAPI (Python) with K-means clustering and TSP routing

## Quick Start

### Prerequisites
- Java 21+
- Maven
- Python 3.13+
- MySQL 8.0+

### 1. Start MySQL
Create database `travelpro_db` with user `root` and your password.

### 2. Configure Backend
Update `backend-java/src/main/resources/application.properties`:
```properties
spring.datasource.password=YOUR_MYSQL_PASSWORD
```

### 3. Start Services

**ML Engine:**
```bash
cd engine-ml
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Backend:**
```bash
cd backend-java
mvn spring-boot:run
```

**Frontend:**
Open `frontend/index.html` in your browser.

## Endpoints

- Frontend: `file://frontend/index.html`
- Backend API: `http://localhost:8080/api`
- ML Engine: `http://localhost:8000`

## Features

- User authentication (register/login)
- Trip planning with budget tracking
- ML-powered itinerary generation
- Day-by-day optimized schedules
- Responsive UI

## Tech Stack

**Frontend**: Vanilla JS, CSS3, HTML5  
**Backend**: Spring Boot 4.0, Hibernate 7.2, MySQL 8.0  
**ML Engine**: FastAPI, scikit-learn, NumPy

---

See component-specific READMEs in `backend-java/`, `engine-ml/`, and `frontend/` for details.
