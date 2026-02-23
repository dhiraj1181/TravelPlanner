# Backend - Spring Boot API

## Run

```bash
mvn spring-boot:run
```

Server starts on `http://localhost:8080`

## Configuration

Update `src/main/resources/application.properties`:
```properties
spring.datasource.password=YOUR_PASSWORD
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (returns mock JWT)
- `POST /api/auth/logout` - Logout

### Trips
- `POST /api/trips/plan` - Create trip with ML itinerary
- `GET /api/trips` - Get user's trips
- `GET /api/trips/{id}` - Get trip by ID

## Database Schema

**users** (id, email, password, name)  
**trips** (id, user_id, destination, title, dates, budget, is_feasible)  
**itinerary_items** (id, trip_id, day_number, place_name, lat, lon, cost, duration)

## Tech

- Spring Boot 4.0.2
- Hibernate 7.2.1
- MySQL 8.0
- Lombok for clean code
