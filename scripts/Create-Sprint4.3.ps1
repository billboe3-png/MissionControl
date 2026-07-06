$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host " Mission Control Sprint 4.3"
Write-Host " Doctor API"
Write-Host "========================================="
Write-Host ""

#----------------------------------------------------------
# Ensure services folder exists
#----------------------------------------------------------

New-Item `
    -ItemType Directory `
    -Force `
    -Path "backend/app/services" | Out-Null

#----------------------------------------------------------
# doctor_service.py
#----------------------------------------------------------

@'
from datetime import datetime, timezone

from app.db.postgres import check_postgres
from app.db.redis import check_redis


async def get_doctor() -> dict:

    postgres = await check_postgres()
    redis = await check_redis()

    checks = [
        {
            "name": "Backend",
            "status": "OK",
            "message": "API running"
        },
        {
            "name": "PostgreSQL",
            "status": "OK" if postgres else "ERROR",
            "message": "Connected" if postgres else "Unavailable"
        },
        {
            "name": "Redis",
            "status": "OK" if redis else "ERROR",
            "message": "Connected" if redis else "Unavailable"
        }
    ]

    overall = "healthy"

    if not postgres or not redis:
        overall = "degraded"

    return {
        "overall": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks
    }
'@ | Set-Content backend/app/services/doctor_service.py

Write-Host "Created doctor_service.py"

#----------------------------------------------------------
# services/__init__.py
#----------------------------------------------------------

$init = @'
from .status_service import get_status
from .doctor_service import get_doctor
'@

Set-Content backend/app/services/__init__.py $init

Write-Host "Updated services/__init__.py"

#----------------------------------------------------------
# routers/doctor.py
#----------------------------------------------------------

@'
from fastapi import APIRouter

from app.services import get_doctor

router = APIRouter(tags=["doctor"])


@router.get("/doctor")
async def doctor():
    return await get_doctor()
'@ | Set-Content backend/app/routers/doctor.py

Write-Host "Updated routers/doctor.py"

#----------------------------------------------------------
# main.py
#----------------------------------------------------------

$main = "backend/app/main.py"

$content = Get-Content $main -Raw

if ($content -notmatch "from app\.routers import doctor") {

    $content = $content.Replace(
        "from app.routers import health",
        @"
from app.routers import health
from app.routers import doctor
"@
    )
}

if ($content -notmatch "include_router\(doctor\.router") {

    $content = $content.Replace(
        '    app.include_router(health.router, prefix="/api/v1")',
        @'
app.include_router(health.router, prefix="/api/v1")
app.include_router(doctor.router, prefix="/api/v1")
'@
    )
}

Set-Content $main $content

Write-Host "Updated main.py"

Write-Host ""
Write-Host "========================================="
Write-Host "Sprint 4.3 complete"
Write-Host "========================================="
Write-Host ""
Write-Host "Next:"
Write-Host ""
Write-Host "docker compose up -d --build"
Write-Host ""
Write-Host "curl http://localhost/api/v1/doctor"