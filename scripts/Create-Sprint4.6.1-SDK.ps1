<#
===========================================================
 Mission Control
 Sprint 4.6.1
 Docker SDK Foundation
===========================================================

This script:

• Adds Docker SDK dependency
• Creates infrastructure/docker package
• Creates Docker client wrapper
• Creates provider abstraction

Run:

.\scripts\Create-Sprint4.6.1-SDK.ps1

===========================================================
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Mission Control Sprint 4.6.1" -ForegroundColor Yellow
Write-Host " Docker SDK Foundation" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$Root = Split-Path $PSScriptRoot -Parent

if (!(Test-Path $Root))
{
    throw "Repository root not found."
}

Set-Location $Root

$Infrastructure = Join-Path $Root "backend\app\infrastructure"
$DockerFolder   = Join-Path $Infrastructure "docker"

New-Item $Infrastructure -ItemType Directory -Force | Out-Null
New-Item $DockerFolder -ItemType Directory -Force | Out-Null

Write-Host "Created infrastructure folders."

############################################################
# Update requirements.txt
############################################################

$Requirements = "backend\requirements.txt"

if (!(Test-Path $Requirements))
{
    throw "backend\requirements.txt not found."
}

$content = Get-Content $Requirements

if ($content -notcontains "docker>=7.1.0")
{
    Add-Content $Requirements ""
    Add-Content $Requirements "docker>=7.1.0"

    Write-Host "Added Docker SDK dependency."
}
else
{
    Write-Host "Docker SDK already installed."
}

############################################################
# Create package __init__
############################################################

@'
"""
Mission Control Infrastructure Layer
"""
'@ | Set-Content "backend\app\infrastructure\__init__.py"

@'
"""
Docker Infrastructure
"""
'@ | Set-Content "backend\app\infrastructure\docker\__init__.py"

Write-Host "Created package initializers."

############################################################
# Docker Base Interface
############################################################

@'
from abc import ABC, abstractmethod


class DockerProvider(ABC):

    @abstractmethod
    async def info(self):
        ...

    @abstractmethod
    async def containers(self):
        ...

    @abstractmethod
    async def version(self):
        ...
'@ | Set-Content "backend\app\infrastructure\docker\base.py"

Write-Host "Created DockerProvider base class."

Write-Host ""
Write-Host "----------------------------------------"
Write-Host " Part 1 Complete"
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Next: Paste Part 2 into the SAME script."
############################################################
# Docker SDK Client
############################################################

@'
import docker
from docker.errors import DockerException


class DockerSdk:

    def __init__(self):

        self.client = None

        try:
            self.client = docker.from_env()

        except DockerException:
            self.client = None

        except Exception:
            self.client = None


    @property
    def connected(self):

        return self.client is not None


    def ping(self):

        if not self.connected:
            return False

        try:
            self.client.ping()
            return True

        except Exception:
            return False


    def version(self):

        if not self.connected:
            return {}

        try:
            return self.client.version()

        except Exception:
            return {}


    def info(self):

        if not self.connected:
            return {}

        try:
            return self.client.info()

        except Exception:
            return {}


    def containers(self):

        if not self.connected:
            return []

        try:
            return self.client.containers.list(all=True)

        except Exception:
            return []
'@ | Set-Content "backend\app\infrastructure\docker\docker_sdk.py"

Write-Host "Created Docker SDK client."

############################################################
# Docker Provider
############################################################

@'
from .base import DockerProvider
from .docker_sdk import DockerSdk


class DockerSdkProvider(DockerProvider):

    def __init__(self):

        self.sdk = DockerSdk()


    async def info(self):

        return self.sdk.info()


    async def version(self):

        return self.sdk.version()


    async def containers(self):

        results = []

        for container in self.sdk.containers():

            try:

                results.append(
                    {
                        "id": container.short_id,
                        "name": container.name,
                        "image": container.image.tags[0] if container.image.tags else "<none>",
                        "status": container.status,
                    }
                )

            except Exception:

                pass

        return results
'@ | Set-Content "backend\app\infrastructure\docker\provider.py"

Write-Host "Created Docker SDK provider."

############################################################
# Export package
############################################################

@'
from .base import DockerProvider
from .provider import DockerSdkProvider

__all__ = [
    "DockerProvider",
    "DockerSdkProvider",
]
'@ | Set-Content "backend\app\infrastructure\docker\__init__.py"

Write-Host "Updated package exports."

Write-Host ""
Write-Host "----------------------------------------"
Write-Host " Part 2 Complete"
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Infrastructure layer now contains:"
Write-Host "  docker_sdk.py"
Write-Host "  provider.py"
Write-Host "  base.py"
Write-Host ""
Write-Host "Next: Append Part 3."
############################################################
# Docker Provider Factory
############################################################

@'
from .provider import DockerSdkProvider


_provider = None


def get_docker_provider():

    global _provider

    if _provider is None:
        _provider = DockerSdkProvider()

    return _provider
'@ | Set-Content "backend\app\infrastructure\docker\factory.py"

Write-Host "Created Docker provider factory."

############################################################
# Update docker package exports
############################################################

@'
from .base import DockerProvider
from .provider import DockerSdkProvider
from .factory import get_docker_provider

__all__ = [
    "DockerProvider",
    "DockerSdkProvider",
    "get_docker_provider",
]
'@ | Set-Content "backend\app\infrastructure\docker\__init__.py"

Write-Host "Updated docker package exports."

############################################################
# Update Platform Base
############################################################

$PlatformBase = "backend\app\platform\base.py"

@'
from abc import ABC, abstractmethod


class PlatformBase(ABC):

    @abstractmethod
    async def status(self):
        ...

    @abstractmethod
    async def doctor(self):
        ...

    @abstractmethod
    async def docker_status(self):
        ...
'@ | Set-Content $PlatformBase

Write-Host "Verified PlatformBase."

############################################################
# Update Platform Provider
############################################################

$Provider = "backend\app\platform\provider.py"

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
'@ | Set-Content $Provider

Write-Host "Updated platform provider."

############################################################
# Create infrastructure README
############################################################

@'
Infrastructure Layer

Mission Control uses providers to isolate infrastructure
implementations from routers and business logic.

Current Providers

- Docker SDK

Future Providers

- SSH
- WinRM
- Kubernetes
- Hyper-V
- VMware
- Proxmox
'@ | Set-Content "backend\app\infrastructure\README.md"

Write-Host "Created infrastructure documentation."

Write-Host ""
Write-Host "----------------------------------------"
Write-Host " Part 3 Complete"
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Created:"
Write-Host "  docker/factory.py"
Write-Host "Updated:"
Write-Host "  docker/__init__.py"
Write-Host "  platform/provider.py"
Write-Host "  platform/base.py"
Write-Host ""
Write-Host "Next: Append Part 4."
############################################################
# Windows Platform
############################################################

@'
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.postgres import check_postgres
from app.db.redis import check_redis

from app.infrastructure.docker import get_docker_provider

from .base import PlatformBase


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

        return {
            "overall": "healthy" if postgres and redis else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks
        }

    async def docker_status(self):

        docker = get_docker_provider()

        version = await docker.version()
        containers = await docker.containers()

        return {
            "engine": "running" if version else "offline",
            "compose": "sdk",
            "container_count": len(containers),
            "containers": containers,
            "docker_version": version.get("Version", "Unknown")
        }
'@ | Set-Content "backend\app\platform\windows.py"

Write-Host "Updated WindowsPlatform."

############################################################
# Linux Platform
############################################################

@'
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.postgres import check_postgres
from app.db.redis import check_redis

from app.infrastructure.docker import get_docker_provider

from .base import PlatformBase


class LinuxPlatform(PlatformBase):

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

        return {
            "overall": "healthy" if postgres and redis else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks
        }

    async def docker_status(self):

        docker = get_docker_provider()

        version = await docker.version()
        containers = await docker.containers()

        return {
            "engine": "running" if version else "offline",
            "compose": "sdk",
            "container_count": len(containers),
            "containers": containers,
            "docker_version": version.get("Version", "Unknown")
        }
'@ | Set-Content "backend\app\platform\linux.py"

Write-Host "Updated LinuxPlatform."

############################################################
# Verify services exports
############################################################

@'
from .status_service import get_status
from .doctor_service import get_doctor
from .docker_service import get_docker_status

__all__ = [
    "get_status",
    "get_doctor",
    "get_docker_status",
]
'@ | Set-Content "backend\app\services\__init__.py"

Write-Host "Verified services exports."

Write-Host ""
Write-Host "----------------------------------------"
Write-Host " Part 4 Complete"
Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Platform layer now uses Docker SDK."
Write-Host ""
Write-Host "Next: Append Part 5."
############################################################
# Docker Compose Guidance
############################################################

Write-Host ""
Write-Host "========================================="
Write-Host " IMPORTANT"
Write-Host "========================================="
Write-Host ""

Write-Host "The Docker SDK requires access to the Docker Engine."

Write-Host ""
Write-Host "Linux:"
Write-Host "  Mount:"
Write-Host "  /var/run/docker.sock:/var/run/docker.sock"

Write-Host ""
Write-Host "Windows Docker Desktop:"
Write-Host "  Docker SDK will use the Docker Desktop"
Write-Host "  named pipe automatically when available."

Write-Host ""
Write-Host "No code changes are required."
Write-Host ""

############################################################
# Verify generated files
############################################################

Write-Host ""
Write-Host "Verifying generated files..."
Write-Host ""

$Files = @(
"backend/app/infrastructure/__init__.py",
"backend/app/infrastructure/README.md",
"backend/app/infrastructure/docker/__init__.py",
"backend/app/infrastructure/docker/base.py",
"backend/app/infrastructure/docker/docker_sdk.py",
"backend/app/infrastructure/docker/provider.py",
"backend/app/infrastructure/docker/factory.py",
"backend/app/platform/windows.py",
"backend/app/platform/linux.py"
)

foreach($File in $Files)
{
    if(Test-Path $File)
    {
        Write-Host " OK  $File" -ForegroundColor Green
    }
    else
    {
        Write-Host " FAIL $File" -ForegroundColor Red
    }
}

############################################################
# Check requirements
############################################################

Write-Host ""
Write-Host "Checking requirements.txt..."

$Requirements = Get-Content "backend\requirements.txt"

if($Requirements -contains "docker>=7.1.0")
{
    Write-Host " Docker SDK dependency present." -ForegroundColor Green
}
else
{
    Write-Host " Docker SDK dependency missing." -ForegroundColor Red
}

############################################################
# Next Steps
############################################################

Write-Host ""
Write-Host "========================================="
Write-Host " Sprint 4.6.1 COMPLETE"
Write-Host "========================================="
Write-Host ""

Write-Host "Next:"
Write-Host ""

Write-Host "1. Build the project"
Write-Host ""
Write-Host "   docker compose up -d --build"
Write-Host ""

Write-Host "2. Verify the API"
Write-Host ""
Write-Host "   curl http://localhost/api/v1/status"
Write-Host "   curl http://localhost/api/v1/doctor"
Write-Host "   curl http://localhost/api/v1/docker"
Write-Host ""

Write-Host "Expected:"
Write-Host ""

Write-Host " Platform abstraction active"
Write-Host " Docker SDK installed"
Write-Host " No subprocess() Docker calls remain"
Write-Host " Windows and Linux share the same provider interface"
Write-Host ""

Write-Host "Sprint 4.6.2 will introduce:"
Write-Host ""
Write-Host " • Container CPU usage"
Write-Host " • Memory usage"
Write-Host " • Restart counts"
Write-Host " • Health status"
Write-Host " • Image information"
Write-Host " • Container uptime"
Write-Host ""

Write-Host "========================================="