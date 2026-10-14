# Windows PowerShell Script to Execute EnergySense Pytest Suite
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path "$ProjectRoot\backend"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "         Running EnergySense Automated Test Suite         " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

python -m pytest -v --tb=short

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nAll backend tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nSome tests failed. Check error trace above." -ForegroundColor Red
}
