#requires -Version 7

Clear-Host

Write-Host ""
Write-Host "========================================="
Write-Host " Mission Control Sprint 4.5"
Write-Host " Platform Abstraction - Integration"
Write-Host "========================================="
Write-Host ""

$routerFolder = "backend/app/routers"

#----------------------------------------------------------
# STATUS ROUTER
#----------------------------------------------------------

@'
from fastapi import APIRouter

from app.platform import get_platform

router = APIRouter(prefix="/status", tags=["status"])


@router.get("")
async def status():

    platform = get_platform()

    return await platform.status()
'@ | Set-Content "$routerFolder/status.py"

Write-Host "Updated status.py"

#----------------------------------------------------------
# DOCTOR ROUTER
#----------------------------------------------------------

@'
from fastapi import APIRouter

from app.platform import get_platform

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("")
async def doctor():

    platform = get_platform()

    return await platform.doctor()
'@ | Set-Content "$routerFolder/doctor.py"

Write-Host "Updated doctor.py"

#----------------------------------------------------------
# DOCKER ROUTER
#----------------------------------------------------------

@'
from fastapi import APIRouter

from app.platform import get_platform

router = APIRouter(prefix="/docker", tags=["docker"])


@router.get("")
async def docker():

    platform = get_platform()

    return await platform.docker_status()
'@ | Set-Content "$routerFolder/docker.py"

Write-Host "Updated docker.py"

Write-Host ""
Write-Host "========================================="
Write-Host "Sprint 4.5.2 complete"
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
Write-Host "The output should be IDENTICAL to Sprint 4.4."
Write-Host ""
Write-Host "If successful, continue with:"
Write-Host ""
Write-Host ".\scripts\Create-Sprint4.5-Migration.ps1"