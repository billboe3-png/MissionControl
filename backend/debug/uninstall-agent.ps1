<#
.SYNOPSIS
Uninstalls Mission Control Agent from Windows.

.DESCRIPTION
Stops and removes the agent scheduled task, kills running processes,
and removes the installation directory.

.PARAMETER InstallDir
Agent installation directory. Default: C:\MissionControlAgent
#>
param(
    [Parameter(Mandatory=$false)][string]$InstallDir = "C:\MissionControlAgent"
)

$ErrorActionPreference = 'SilentlyContinue'
Write-Host ""
Write-Host "Mission Control Agent Uninstaller"
Write-Host "================================="
Write-Host ""

# 1. Delete scheduled task
Write-Host "[1/3] Removing scheduled task..."
schtasks /Delete /TN "MissionControlAgent" /F 2>$null | Out-Null
Write-Host "  Done."

# 2. Kill processes
Write-Host "[2/3] Stopping agent processes..."
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force | Out-Null
Write-Host "  Done."

# 3. Remove files
Write-Host "[3/3] Removing installation directory..."
if (Test-Path $InstallDir) {
    Remove-Item $InstallDir -Recurse -Force
    Write-Host "  Removed: $InstallDir"
} else {
    Write-Host "  Directory not found: $InstallDir"
}

Write-Host ""
Write-Host "Uninstall complete." -ForegroundColor Green
