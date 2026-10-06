<#
.SYNOPSIS
    Uninstall Mission Control Edge Agent on Windows (invoked by the MSI).

.DESCRIPTION
    Stops and removes the edge-agent scheduled task (MissionControlEdgeAgent),
    terminates the agent's python process, and removes the runtime install
    directory C:\MissionControlAgent. Shared artifacts (the Python install)
    are intentionally left in place.

.PARAMETER InstallDir
    Agent runtime directory. Default: C:\MissionControlAgent
#>
param(
    [string]$InstallDir = "C:\MissionControlAgent"
)

$ErrorActionPreference = "Continue"

$TaskName = "MissionControlEdgeAgent"

Write-Host "Mission Control Edge Agent Uninstaller"
Write-Host "======================================"
Write-Host ""

# 1. Stop and remove the scheduled task
Write-Host "[1/3] Removing scheduled task '$TaskName'..."
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    try {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Out-Null
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
        Write-Host "  Scheduled task removed."
    } catch {
        Write-Host "  Could not remove scheduled task: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Scheduled task not present."
}

# 2. Stop agent processes (only the ones running the Mission Control agent)
Write-Host "[2/3] Stopping agent processes..."
$procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue
foreach ($p in $procs) {
    $cmd = $p.CommandLine
    if ($cmd -match "edge_main|mission-control-agent|MissionControlAgent") {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  Stopped PID $($p.ProcessId)"
    }
}

# 3. Remove the runtime directory
Write-Host "[3/3] Removing runtime directory $InstallDir..."
if (Test-Path $InstallDir) {
    try {
        Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction Stop
        Write-Host "  Removed $InstallDir"
    } catch {
        Write-Host "  Could not fully remove $InstallDir : $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Directory not present."
}

Write-Host ""
Write-Host "Uninstall complete." -ForegroundColor Green
exit 0