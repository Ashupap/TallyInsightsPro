@echo off
echo Stopping Tally Prime Analytics Dashboard servers...

REM Kill Python processes (backend)
taskkill /F /IM python.exe /T >nul 2>&1

REM Kill Node processes (frontend)
taskkill /F /IM node.exe /T >nul 2>&1

echo Servers stopped.
pause
