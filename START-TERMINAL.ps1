# Portfolio Terminal Launcher (PowerShell)
# Run with: powershell -ExecutionPolicy Bypass -File START-TERMINAL.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host "  PORTFOLIO TERMINAL LAUNCHER" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Kill existing processes
Write-Host "[1/4] Cleaning up old processes..." -ForegroundColor Yellow
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*api.py*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -like "*terminal-app*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Start Backend API
Write-Host "[2/4] Starting Backend API..." -ForegroundColor Yellow
$backendPath = Join-Path $scriptPath "options"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; Write-Host 'Portfolio API - Port 8000' -ForegroundColor Cyan; python api.py"
Start-Sleep -Seconds 5

# Start Frontend
Write-Host "[3/4] Starting Frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path $scriptPath "terminal-app"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; Write-Host 'Portfolio Terminal - Port 3000' -ForegroundColor Cyan; npm run dev"
Start-Sleep -Seconds 8

# Open browser
Write-Host "[4/4] Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  PORTFOLIO TERMINAL IS RUNNING" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to close this launcher..." -ForegroundColor Yellow
Write-Host "(Leave the other two windows open!)" -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
