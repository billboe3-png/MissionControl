<#
==============================================================================
Mission Control
Sprint 0.1.1 - Dashboard Foundation
Part 1 - Build Framework
==============================================================================

This script provides the helper functions used by the remaining sprint parts.

Nothing in this script modifies the project yet.

==============================================================================

Usage

Run from the project root.

Example

PS C:\Projects\MissionControl> .\scripts\Sprint-0.1.1.ps1

==============================================================================
#>

#Requires -Version 7.0

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Global Configuration
# ---------------------------------------------------------------------------

$Script:ProjectRoot = (Get-Location).Path

$Script:BackendRoot = Join-Path $ProjectRoot "backend"
$Script:FrontendRoot = Join-Path $ProjectRoot "frontend"

$Script:BackupRoot = Join-Path $ProjectRoot ".mc-backups"

$Script:CreatedFiles = [System.Collections.Generic.List[string]]::new()
$Script:ModifiedFiles = [System.Collections.Generic.List[string]]::new()
$Script:CreatedFolders = [System.Collections.Generic.List[string]]::new()

# ---------------------------------------------------------------------------
# Console Helpers
# ---------------------------------------------------------------------------

function Write-Banner {

    param(
        [string]$Title
    )

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host " Mission Control" -ForegroundColor Green
    Write-Host " $Title" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {

    param(
        [string]$Message
    )

    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Write-Success {

    param(
        [string]$Message
    )

    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-WarningMessage {

    param(
        [string]$Message
    )

    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Failure {

    param(
        [string]$Message
    )

    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

function Test-Project {

    Write-Step "Validating Mission Control project..."

    $required = @(
        "backend",
        "frontend",
        "docker-compose.yml"
    )

    foreach ($item in $required) {

        $path = Join-Path $ProjectRoot $item

        if (-not (Test-Path $path)) {

            throw "Mission Control project not found.`nMissing: $item"
        }
    }

    Write-Success "Mission Control project detected."
}

# ---------------------------------------------------------------------------
# Backup Helpers
# ---------------------------------------------------------------------------

function Initialize-BackupFolder {

    if (-not (Test-Path $BackupRoot)) {

        New-Item `
            -ItemType Directory `
            -Path $BackupRoot `
            -Force | Out-Null
    }

}

function Backup-File {

    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    Initialize-BackupFolder

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

    $name = Split-Path $Path -Leaf

    $destination = Join-Path `
        $BackupRoot `
        "$timestamp-$name"

    Copy-Item `
        $Path `
        $destination `
        -Force

    Write-Step "Backup created: $name"
}

# ---------------------------------------------------------------------------
# Folder Helpers
# ---------------------------------------------------------------------------

function New-McDirectory {

    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    if (Test-Path $Path) {
        return
    }

    New-Item `
        -ItemType Directory `
        -Force `
        -Path $Path | Out-Null

    $CreatedFolders.Add($Path)

    Write-Success "Created directory: $Path"
}

# ---------------------------------------------------------------------------
# File Helpers
# ---------------------------------------------------------------------------

function New-McFile {

    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [string]$Content
    )

    if (Test-Path $Path) {

        Write-Step "Exists: $Path"

        return
    }

    $folder = Split-Path $Path

    if (-not (Test-Path $folder)) {

        New-McDirectory $folder
    }

    Set-Content `
        -Path $Path `
        -Value $Content `
        -Encoding UTF8

    $CreatedFiles.Add($Path)

    Write-Success "Created file: $Path"
}

function Update-McFile {

    param(
        [Parameter(Mandatory)]
        [string]$Path,

        [Parameter(Mandatory)]
        [scriptblock]$Editor
    )

    if (-not (Test-Path $Path)) {

        throw "Cannot update missing file:`n$Path"
    }

    Backup-File $Path

    $content = Get-Content `
        $Path `
        -Raw

    $updated = & $Editor $content

    if ($updated -eq $content) {

        Write-Step "No changes: $Path"

        return
    }

    Set-Content `
        -Path $Path `
        -Value $updated `
        -Encoding UTF8

    $ModifiedFiles.Add($Path)

    Write-Success "Updated: $Path"
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

function Show-Summary {

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host " Sprint Summary" -ForegroundColor Yellow
    Write-Host "==================================================" -ForegroundColor Cyan

    Write-Host ""
    Write-Host "Created Directories"

    $CreatedFolders |
    Sort-Object |
    ForEach-Object {

        Write-Host "  + $_"
    }

    Write-Host ""
    Write-Host "Created Files"

    $CreatedFiles |
    Sort-Object |
    ForEach-Object {

        Write-Host "  + $_"
    }

    Write-Host ""
    Write-Host "Modified Files"

    $ModifiedFiles |
    Sort-Object |
    ForEach-Object {

        Write-Host "  * $_"
    }

    Write-Host ""
}

# ---------------------------------------------------------------------------
# Script Start
# ---------------------------------------------------------------------------

Write-Banner "Sprint 0.1.1 - Dashboard Foundation"

Test-Project

Write-Success "Framework loaded."

Write-Host ""
Write-Host "Ready for Part 2..." -ForegroundColor Green
Write-Host ""
# ---------------------------------------------------------------------------
# Part 2 - Dashboard Backend
# ---------------------------------------------------------------------------

Write-Banner "Part 2 - Dashboard Backend"

# ---------------------------------------------------------------------------
# Create folders
# ---------------------------------------------------------------------------

$routerFolder = Join-Path $BackendRoot "app\routers"
$serviceFolder = Join-Path $BackendRoot "app\services"

# ---------------------------------------------------------------------------
# dashboard_service.py
# ---------------------------------------------------------------------------

Write-Step "Creating Dashboard Service..."

$dashboardService = Join-Path `
    $serviceFolder `
    "dashboard_service.py"

New-McFile `
    -Path $dashboardService `
    -Content @'
"""
Mission Control Dashboard Service

Sprint 0.1.1
"""

from datetime import datetime, timezone


class DashboardService:

    async def get_dashboard(self):

        return {

            "application": "Mission Control",

            "version": "0.1.0",

            "generated": datetime.now(timezone.utc).isoformat(),

            "health": {

                "backend": "healthy",

                "database": "healthy",

                "redis": "healthy"

            },

            "projects": [],

            "tasks": [],

            "notes": [],

            "resume": None

        }


dashboard_service = DashboardService()
'@

# ---------------------------------------------------------------------------
# dashboard.py Router
# ---------------------------------------------------------------------------

Write-Step "Creating Dashboard Router..."

$dashboardRouter = Join-Path `
    $routerFolder `
    "dashboard.py"

New-McFile `
    -Path $dashboardRouter `
    -Content @'
"""
Mission Control Dashboard Router

Sprint 0.1.1
"""

from fastapi import APIRouter

from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get(
    "/dashboard",
    tags=["Dashboard"]
)
async def dashboard():

    return await dashboard_service.get_dashboard()
'@

# ---------------------------------------------------------------------------
# services/__init__.py
# ---------------------------------------------------------------------------

Write-Step "Updating services package..."

$servicesInit = Join-Path `
    $serviceFolder `
    "__init__.py"

if (Test-Path $servicesInit) {

    Update-McFile `
        -Path $servicesInit `
        -Editor {

        param($content)

        $line = "from .dashboard_service import dashboard_service"

        if ($content.Contains($line)) {
            return $content
        }

        return $content.TrimEnd() + "`r`n`r`n" + $line + "`r`n"

    }

}

Write-Success "Dashboard backend created."

Write-Host ""
Write-Host "Part 2 Complete." -ForegroundColor Green
Write-Host ""
# ---------------------------------------------------------------------------
# Part 3 - Register Dashboard Router
# ---------------------------------------------------------------------------

Write-Banner "Part 3 - Register Dashboard Router"

$mainPy = Join-Path `
    $BackendRoot `
    "app\main.py"

if (-not (Test-Path $mainPy)) {
    throw "Unable to locate backend/app/main.py"
}

Write-Step "Updating main.py..."

Update-McFile `
    -Path $mainPy `
    -Editor {

    param($content)

    # -----------------------------------------------------------------------
    # Import
    # -----------------------------------------------------------------------

    $importLine = "from app.routers.dashboard import router as dashboard_router"

    if ($content -notmatch [regex]::Escape($importLine)) {

        $imports = $content -split "`r?`n"

        $lastImport = -1

        for ($i = 0; $i -lt $imports.Count; $i++) {

            if ($imports[$i] -match "^from " -or
                $imports[$i] -match "^import ") {

                $lastImport = $i
            }
        }

        if ($lastImport -ge 0) {

            $list = [System.Collections.Generic.List[string]]::new()

            $list.AddRange($imports)

            $list.Insert($lastImport + 1, $importLine)

            $content = $list -join "`r`n"
        }
    }

    # -----------------------------------------------------------------------
    # Router Registration
    # -----------------------------------------------------------------------

    $registration = 'app.include_router(dashboard_router, prefix="/api/v1")'

    if ($content -notmatch [regex]::Escape($registration)) {

        $pattern = 'app\.include_router\([^)]+\)'

        $matches = [regex]::Matches($content, $pattern)

        if ($matches.Count -gt 0) {

            $last = $matches[$matches.Count - 1].Value

            $replacement = $last + "`r`n" + $registration

            $content = $content.Replace($last, $replacement)

        }
        else {

            $content += "`r`n`r`n" + $registration + "`r`n"

        }

    }

    return $content

}

Write-Success "Dashboard router registered."

Write-Host ""
