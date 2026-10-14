# Windows PowerShell Script to Launch EnergySense FastAPI Backend
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting EnergySense FastAPI Backend (Uvicorn Server)   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path "$ScriptDir\backend"

Write-Host "Backend directory: $(Get-Location)" -ForegroundColor DarkGray
Write-Host "Serving at: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Interactive Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow

python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
