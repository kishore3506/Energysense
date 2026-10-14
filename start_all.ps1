# Windows PowerShell Script to Launch Both EnergySense Backend and Frontend Concurrently
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         Launching EnergySense Full-Stack Platform        " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor DarkGray

# 1. Start Backend in separate window
Write-Host "Launching Backend API (http://127.0.0.1:8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$ProjectRoot\start_backend.ps1"

# Brief pause to allow backend port binding
Start-Sleep -Seconds 2

# 2. Start Frontend in separate window
Write-Host "Launching Frontend Dashboard (http://localhost:5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$ProjectRoot\start_frontend.ps1"

Write-Host "`nEnergySense is running!" -ForegroundColor Green
Write-Host "  Frontend Dashboard : http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API Docs   : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
