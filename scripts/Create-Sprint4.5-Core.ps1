#requires -Version 7

Clear-Host

Write-Host ""
Write-Host "========================================="
Write-Host " Mission Control Sprint 4.5"
Write-Host " Platform Abstraction - Core"
Write-Host "========================================="
Write-Host ""

$platformFolder = "backend/app/platform"

if (!(Test-Path $platformFolder)) {
    New-Item -ItemType Directory $platformFolder | Out-Null
}

# ----------------------------------------------------------
# __init__.py
# ----------------------------------------------------------

@'
from .provider import get_platform
'@ | Set-Content "$platformFolder/__init__.py"

# ----------------------------------------------------------
# base.py
# ----------------------------------------------------------

@'
from abc import ABC, abstractmethod


class PlatformProvider(ABC):

    @abstractmethod
    async def docker_status(self):
        pass

    @abstractmethod
    async def doctor(self):
        pass

    @abstractmethod
    async def status(self):
        pass
'@ | Set-Content "$platformFolder/base.py"

# ----------------------------------------------------------
# windows.py
# ----------------------------------------------------------

@'
from app.platform.base import PlatformProvider

from app.services.status_service import get_status
from app.services.doctor_service import get_doctor
from app.services.docker_service import get_docker_status


class WindowsPlatform(PlatformProvider):

    async def status(self):
        return await get_status()

    async def doctor(self):
        return await get_doctor()

    async def docker_status(self):
        return await get_docker_status()
'@ | Set-Content "$platformFolder/windows.py"

# ----------------------------------------------------------
# linux.py
# ----------------------------------------------------------

@'
from app.platform.base import PlatformProvider

from app.services.status_service import get_status
from app.services.doctor_service import get_doctor
from app.services.docker_service import get_docker_status


class LinuxPlatform(PlatformProvider):

    async def status(self):
        return await get_status()

    async def doctor(self):
        return await get_doctor()

    async def docker_status(self):
        return await get_docker_status()
'@ | Set-Content "$platformFolder/linux.py"

# ----------------------------------------------------------
# provider.py
# ----------------------------------------------------------

@'
import platform

from app.platform.windows import WindowsPlatform
from app.platform.linux import LinuxPlatform


_provider = None


def get_platform():

    global _provider

    if _provider is not None:
        return _provider

    system = platform.system().lower()

    if system == "windows":
        _provider = WindowsPlatform()

    else:
        _provider = LinuxPlatform()

    return _provider
'@ | Set-Content "$platformFolder/provider.py"

Write-Host "Created:"
Write-Host "  backend/app/platform/"
Write-Host "      base.py"
Write-Host "      provider.py"
Write-Host "      windows.py"
Write-Host "      linux.py"
Write-Host "      __init__.py"
Write-Host ""
Write-Host "Sprint 4.5.1 complete."
Write-Host ""
Write-Host "Next:"
Write-Host "    .\scripts\Create-Sprint4.5-Integration.ps1"
Write-Host ""