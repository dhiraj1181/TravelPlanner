@echo off
echo ====================================
echo Starting TravelPro Backend
echo ====================================

cd backend-java

echo.
echo Building and starting Spring Boot application...
mvn spring-boot:run

pause
