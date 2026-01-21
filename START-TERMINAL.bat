@echo off
color 0A
title Portfolio Terminal Launcher

echo ========================================
echo   PORTFOLIO TERMINAL LAUNCHER
echo ========================================
echo.

REM Kill any existing processes
echo [1/4] Cleaning up old processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 /nobreak >nul

echo [2/4] Starting Backend API...
cd /d "%~dp0options"
if not exist "api.py" (
    echo ERROR: api.py not found in options folder!
    pause
    exit /b 1
)
start "Portfolio API - Port 8000" cmd /k "python api.py"
timeout /t 5 /nobreak >nul

echo [3/4] Starting Frontend...
cd /d "%~dp0terminal-app"
if not exist "package.json" (
    echo ERROR: package.json not found in terminal-app folder!
    echo Please run: npm install
    pause
    exit /b 1
)
start "Portfolio Terminal - Port 3000" cmd /k "npm run dev"
timeout /t 8 /nobreak >nul

echo [4/4] Opening browser...
start http://localhost:3000

echo.
echo ========================================
echo   PORTFOLIO TERMINAL IS STARTING
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Wait 10-15 seconds for everything to load...
echo.
echo You should see 2 new windows:
echo   - Portfolio API (Python)
echo   - Portfolio Terminal (Next.js)
echo.
echo Keep those windows open!
echo.
pause
