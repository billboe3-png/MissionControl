$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host " Mission Control - Sprint 4.2"
Write-Host " Status API"
Write-Host "========================================="
Write-Host ""

# ------------------------------------------------------------
# Create folders
# ------------------------------------------------------------

$directories = @(
    "backend/app/services"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "Created $dir"
    }
}

# ------------------------------------------------------------
# status_service.py
# ------------------------------------------------------------

@'
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.postgres import check_postgres
from app.db.redis import check_redis


async def get_status() -> dict:
    settings = get_settings()

    postgres = await check_postgres()
    redis = await check_redis()

    return {
        "project": settings.project_name,
        "environment": settings.environment,
        "version": "0.1.0",
        "backend": "online",
        "database": "connected" if postgres else "disconnected",
        "redis": "connected" if redis else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
'@ | Set-Content backend/app/services/status_service.py

Write-Host "Created status_service.py"

# ------------------------------------------------------------
# __init__.py
# ------------------------------------------------------------

@'
from .status_service import get_status
'@ | Set-Content backend/app/services/__init__.py

Write-Host "Updated services/__init__.py"

# ------------------------------------------------------------
# status.py
# ------------------------------------------------------------

@'
from fastapi import APIRouter

from app.services import get_status

router = APIRouter(tags=["status"])


@router.get("/status")
async def status():
    return await get_status()
'@ | Set-Content backend/app/routers/status.py

Write-Host "Updated routers/status.py"

Write-Host ""
Write-Host "Sprint 4.2 files created."
Write-Host ""

Write-Host "Rebuild Docker:"
Write-Host "docker compose up -d --build"

Write-Host ""
Write-Host "Test:"
Write-Host "curl http://localhost/api/v1/status"