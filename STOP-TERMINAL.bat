@echo off
color 0C
title Stop Portfolio Terminal

echo ========================================
echo   STOPPING PORTFOLIO TERMINAL
echo ========================================
echo.

echo Killing Backend API (port 8000)...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *Portfolio API*" >nul 2>&1
npx kill-port 8000 >nul 2>&1

echo Killing Frontend (port 3000)...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *Portfolio Terminal*" >nul 2>&1
npx kill-port 3000 >nul 2>&1

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   ALL PROCESSES STOPPED
echo ========================================
echo.
pause
