@echo off
echo Starting Tally Prime Analytics Dashboard (Development Mode)
echo.

REM Start backend server
start "Backend Server" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a bit for backend to start
timeout /t 2 /nobreak >nul

REM Start frontend server
start "Frontend Server" cmd /k "cd client && npx vite --port 5000 --host 0.0.0.0"

echo.
echo Servers starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5000
echo.
timeout /t 5 /nobreak >nul
start http://localhost:5000
