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

# 1. Delete scheduled task FIRST
Write-Host "[1/4] Removing scheduled task..."
schtasks /Delete /TN "MissionControlAgent" /F 2>$null | Out-Null
Start-Sleep -Seconds 2
Write-Host "  Done."

# 2. Kill ALL python processes
Write-Host "[2/4] Stopping agent processes..."
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Stop-Process -Force | Out-Null
Start-Sleep -Seconds 2
Write-Host "  Done."

# 3. Remove files (retry with force)
Write-Host "[3/4] Removing installation directory..."
if (Test-Path $InstallDir) {
    # Force remove read-only/system files
    $items = Get-ChildItem -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($item in $items) {
        try {
            $item.Attributes = 'Normal'
            Remove-Item $item.FullName -Recurse -Force -ErrorAction SilentlyContinue
        } catch {}
    }
    # Final attempt with cmd.exe
    cmd /c "rd /s /q `"$InstallDir`"" 2>$null | Out-Null
    
    if (-not (Test-Path $InstallDir)) {
        Write-Host "  Removed: $InstallDir"
    } else {
        Write-Host "  WARNING: Some files could not be removed. They may be in use."
        Write-Host "  Remaining:"
        Get-ChildItem $InstallDir -Recurse -Force -ErrorAction SilentlyContinue | Select-Object FullName | ForEach-Object { Write-Host "    $($_.FullName)" }
    }
} else {
    Write-Host "  Directory already removed."
}

# 4. Cleanup
Write-Host "[4/4] Cleanup..."
Write-Host ""
Write-Host "Uninstall complete. Reboot if files remain locked." -ForegroundColor Green
