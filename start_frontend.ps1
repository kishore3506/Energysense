# Windows PowerShell Script to Launch EnergySense React Vite Frontend
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting EnergySense React Vite Dashboard (Dev Server) " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path "$ScriptDir\frontend"

Write-Host "Frontend directory: $(Get-Location)" -ForegroundColor DarkGray
Write-Host "Local URL: http://localhost:5173" -ForegroundColor Yellow

npm run dev
