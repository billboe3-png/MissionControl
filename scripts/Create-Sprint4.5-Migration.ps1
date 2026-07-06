#requires -Version 7

Clear-Host

Write-Host ""
Write-Host "========================================="
Write-Host " Mission Control Sprint 4.5"
Write-Host " Platform Abstraction - Migration"
Write-Host "========================================="
Write-Host ""

$Platform = "backend/app/platform"
$Services = "backend/app/services"

############################################################
# WINDOWS PROVIDER
############################################################

@'
from datetime import datetime, timezone
import subprocess

from app.core.config import get_settings
from app.db.postgres import check_postgres
from app.db.redis import check_redis

from .base import PlatformBase


def run(command):

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )

        return result.returncode == 0, result.stdout.strip()

    except Exception:
        return False, ""


class WindowsPlatform(PlatformBase):

    async def status(self):

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

    async def doctor(self):

        postgres = await check_postgres()
        redis = await check_redis()

        checks = [
            {
                "name":"Backend",
                "status":"OK",
                "message":"API running"
            },
            {
                "name":"PostgreSQL",
                "status":"OK" if postgres else "ERROR",
                "message":"Connected" if postgres else "Unavailable"
            },
            {
                "name":"Redis",
                "status":"OK" if redis else "ERROR",
                "message":"Connected" if redis else "Unavailable"
            }
        ]

        return {
            "overall":"healthy" if postgres and redis else "degraded",
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "checks":checks
        }

    async def docker_status(self):

        engine,_ = run(["docker","info"])

        compose,_ = run(["docker","compose","version"])

        return {
            "engine":"running" if engine else "offline",
            "compose":"available" if compose else "missing"
        }
'@ | Set-Content "$Platform/windows.py"

Write-Host "Updated windows.py"

############################################################
# LINUX PROVIDER
############################################################

Copy-Item `
    "$Platform/windows.py" `
    "$Platform/linux.py" `
    -Force

(Get-Content "$Platform/linux.py") `
    -replace "WindowsPlatform","LinuxPlatform" |
Set-Content "$Platform/linux.py"

Write-Host "Updated linux.py"

############################################################
# COMPATIBILITY WRAPPERS
############################################################

@'
from app.platform import get_platform

async def get_status():
    return await get_platform().status()
'@ | Set-Content "$Services/status_service.py"

@'
from app.platform import get_platform

async def get_doctor():
    return await get_platform().doctor()
'@ | Set-Content "$Services/doctor_service.py"

@'
from app.platform import get_platform

async def get_docker_status():
    return await get_platform().docker_status()
'@ | Set-Content "$Services/docker_service.py"

Write-Host "Created compatibility wrappers"

############################################################
# SERVICES INIT
############################################################

@'
from .status_service import get_status
from .doctor_service import get_doctor
from .docker_service import get_docker_status
'@ | Set-Content "$Services/__init__.py"

Write-Host "Updated services/__init__.py"

Write-Host ""
Write-Host "========================================="
Write-Host " Sprint 4.5 COMPLETE"
Write-Host "========================================="
Write-Host ""
Write-Host "Next:"
Write-Host ""
Write-Host "docker compose up -d --build"
Write-Host ""
Write-Host "Verify:"
Write-Host ""
Write-Host "curl http://localhost/api/v1/status"
Write-Host "curl http://localhost/api/v1/doctor"
Write-Host "curl http://localhost/api/v1/docker"
Write-Host ""
Write-Host "Expected:"
Write-Host "  ✔ Same API responses"
Write-Host "  ✔ Routers no longer know about Windows/Linux"
Write-Host "  ✔ Platform-specific logic isolated under app/platform"
Write-Host "  ✔ Ready for remote agents (SSH, WinRM, Kubernetes, etc.)"