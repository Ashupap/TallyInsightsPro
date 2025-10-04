@echo off
echo ========================================
echo Tally Prime Analytics Dashboard
echo Windows Deployment Script
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18 or higher from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/5] Installing Python dependencies...
pip install -q fastapi uvicorn pandas requests scikit-learn openpyxl plotly python-multipart
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo [2/5] Installing Node.js dependencies...
cd client
call npm install --silent
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)
cd ..

echo [3/5] Building frontend...
cd client
call npm run build --silent
if %errorlevel% neq 0 (
    echo ERROR: Failed to build frontend
    cd ..
    pause
    exit /b 1
)
cd ..

echo [4/5] Dependencies installed successfully!
echo.
echo ========================================
echo Starting Tally Prime Analytics Dashboard
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:5000
echo.
echo Press Ctrl+C to stop the servers
echo ========================================
echo.

REM Start backend server in a new window
start "Tally Analytics - Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend server in a new window
start "Tally Analytics - Frontend" cmd /k "cd client && npx vite --port 5000 --host 0.0.0.0"

echo.
echo [5/5] Servers started successfully!
echo.
echo Opening browser...
timeout /t 5 /nobreak >nul
start http://localhost:5000

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Access the dashboard at: http://localhost:5000
echo.
echo Default credentials:
echo   Admin    - Username: admin    Password: admin123
echo   Manager  - Username: manager  Password: manager123
echo   Viewer   - Username: viewer   Password: viewer123
echo.
echo Tally Server URL: http://localhost:9000
echo Make sure Tally Prime is running with web API enabled!
echo.
pause
