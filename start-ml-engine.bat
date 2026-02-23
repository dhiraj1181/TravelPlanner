@echo off
echo ====================================
echo Starting TravelPro ML Engine
echo ====================================

cd engine-ml

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI server on port 8000...
uvicorn app.main:app --reload --port 8000

pause
