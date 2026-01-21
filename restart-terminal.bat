@echo off
echo Killing existing processes...

REM Kill existing API
taskkill /F /IM python.exe /FI "WINDOWTITLE eq api.py*" 2>nul

REM Kill existing Next.js
npx kill-port 3000 2>nul

echo.
echo Starting Backend API...
start "Portfolio API" cmd /k "cd options && python api.py"

timeout /t 3 /nobreak >nul

echo Starting Next.js Frontend...
start "Portfolio Terminal" cmd /k "cd terminal-app && npm run dev"

echo.
echo Terminal starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window...
pause >nul
