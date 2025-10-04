# Tally Prime Analytics Dashboard - Windows Deployment Script
# PowerShell Version

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tally Prime Analytics Dashboard" -ForegroundColor Cyan
Write-Host "Windows Deployment Script (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for Python
Write-Host "[Check] Verifying Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.8 or higher from https://www.python.org/downloads/" -ForegroundColor Red
    pause
    exit 1
}

# Check for Node.js
Write-Host "[Check] Verifying Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Found: Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Node.js 18 or higher from https://nodejs.org/" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""

# Install Python dependencies
Write-Host "[1/5] Installing Python dependencies..." -ForegroundColor Yellow
pip install -q fastapi uvicorn pandas requests scikit-learn openpyxl plotly python-multipart
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to install Python dependencies" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "✓ Python dependencies installed" -ForegroundColor Green

# Install Node.js dependencies
Write-Host "[2/5] Installing Node.js dependencies..." -ForegroundColor Yellow
Set-Location client
npm install --silent
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to install Node.js dependencies" -ForegroundColor Red
    Set-Location ..
    pause
    exit 1
}
Set-Location ..
Write-Host "✓ Node.js dependencies installed" -ForegroundColor Green

# Build frontend
Write-Host "[3/5] Building frontend..." -ForegroundColor Yellow
Set-Location client
npm run build --silent
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to build frontend" -ForegroundColor Red
    Set-Location ..
    pause
    exit 1
}
Set-Location ..
Write-Host "✓ Frontend built successfully" -ForegroundColor Green

Write-Host "[4/5] Starting servers..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Tally Prime Analytics Dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "Frontend UI: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the servers" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start backend server in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000" -WindowStyle Normal

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend server in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location client; npx vite --port 5000 --host 0.0.0.0" -WindowStyle Normal

Write-Host "[5/5] Servers started successfully`!" -ForegroundColor Green
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Start-Process "http://localhost:5000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete`!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the dashboard at: http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Default credentials:" -ForegroundColor Yellow
Write-Host "  Admin    - Username: admin    Password: admin123" -ForegroundColor White
Write-Host "  Manager  - Username: manager  Password: manager123" -ForegroundColor White
Write-Host "  Viewer   - Username: viewer   Password: viewer123" -ForegroundColor White
Write-Host ""
Write-Host "Tally Server URL: http://localhost:9000" -ForegroundColor White
Write-Host "Make sure Tally Prime is running with web API enabled`!" -ForegroundColor Yellow
Write-Host ""
pause
