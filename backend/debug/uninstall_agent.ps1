<#
.SYNOPSIS
Uninstalls Mission Control Edge Agent from Windows.
#>

$ErrorActionPreference = 'SilentlyContinue'

$ServiceName = "MissionControlEdgeAgent"
$InstallDir = "C:\Program Files\MC Edge Agent"
$ConfigDir = "$env:ProgramData\MC Edge Agent"

# 1. Stop and remove service
Write-Host "[*] Stopping and removing service..."
$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($svc) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Write-Host "[+] Service removed"
}

# 2. Remove install dirs
Write-Host "[*] Removing installation files..."
$dirs = @(
    $InstallDir,
    "C:\MissionControlAgent",
    "$env:ProgramData\MissionControlAgent"
)
foreach ($d in $dirs) {
    if (Test-Path $d) {
        Remove-Item $d -Recurse -Force
        Write-Host "[+] Removed $d"
    }
}

# 3. Remove leftover configs
$configs = @(
    "$InstallDir\config.yaml",
    "$ConfigDir\config.yaml",
    "$env:USERPROFILE\.config\mission-control-agent\config.yaml",
    "$env:USERPROFILE\.config\mission-control-edge-agent\config.yaml"
)
foreach ($c in $configs) {
    if (Test-Path $c) { 
        Remove-Item $c -Force
        Write-Host "[+] Removed $c"
    }
}

# 4. Remove scheduled task if exists
$task = Get-ScheduledTask -TaskName "MissionControlAgent" -ErrorAction SilentlyContinue
if ($task) {
    Unregister-ScheduledTask -TaskName "MissionControlAgent" -Confirm:$false
    Write-Host "[+] Removed scheduled task"
}

Write-Host "`n[+] Uninstall complete."
