$projectRoot = Split-Path -Parent $PSScriptRoot
$routerPath = Join-Path $projectRoot "backend\app\routers"

if (-not (Test-Path $routerPath)) {
    New-Item -ItemType Directory -Path $routerPath | Out-Null
}

$routes = @(
    @{
        Name    = "version"
        Content = @'
from fastapi import APIRouter

from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/version", tags=["version"])


@router.get("")
async def version() -> dict[str, str]:
    return {
        "name": settings.project_name,
        "version": "0.1.0",
    }
'@
    },
    @{
        Name    = "status"
        Content = @'
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def status():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
'@
    },
    @{
        Name    = "doctor"
        Content = @'
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("")
async def doctor():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
'@
    },
    @{
        Name    = "docker"
        Content = @'
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/docker", tags=["docker"])


@router.get("")
async def docker():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
'@
    },
    @{
        Name    = "git"
        Content = @'
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/git", tags=["git"])


@router.get("")
async def git():
    raise HTTPException(
        status_code=501,
        detail="Not implemented",
    )
'@
    }
)

foreach ($route in $routes) {
    $file = Join-Path $routerPath "$($route.Name).py"

    if (Test-Path $file) {
        Write-Host "Skipping existing file: $($route.Name).py"
    }
    else {
        Set-Content -Path $file -Value $route.Content -Encoding UTF8
        Write-Host "Created $($route.Name).py"
    }
}

Write-Host ""
Write-Host "Sprint 4.1 route files created successfully."
Write-Host "Next step: update backend/app/main.py to register the new routers."