# =========================================
# Mission Control
# Sprint 4.4 Fix
# =========================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Mission Control Sprint 4.4 Fix" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$servicesInit = Join-Path $PSScriptRoot "..\backend\app\services\__init__.py"
$servicesInit = (Resolve-Path $servicesInit).Path

$content = Get-Content $servicesInit

$newContent = @()

foreach ($line in $content) {

    # Remove the invalid import
    if ($line.Trim() -eq "from .docker_service import get_docker") {
        Write-Host "Removing invalid import..." -ForegroundColor Yellow
        continue
    }

    $newContent += $line
}

# Ensure the correct import exists
if (-not ($newContent -contains "from .docker_service import get_docker_status")) {

    Write-Host "Adding get_docker_status import..." -ForegroundColor Green

    $newContent += "from .docker_service import get_docker_status"
}

$newContent |
    Set-Content $servicesInit -Encoding UTF8

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Sprint 4.4 import fixed." -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next:" -ForegroundColor Yellow
Write-Host ""
Write-Host "docker compose up -d --build"
Write-Host ""
Write-Host "curl http://localhost/api/v1/docker"
Write-Host ""