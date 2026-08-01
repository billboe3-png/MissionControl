<#
.SYNOPSIS
Uninstalls Mission Control Agent from CORHQROBERTB.
#>

$ErrorActionPreference = 'SilentlyContinue'

# 1. Remove scheduled task
schtasks /Delete /TN "MissionControlAgent" /F 2>$null

# 2. Kill any running agent processes
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force

# 3. Remove install dirs
$dirs = @(
    'C:\MissionControlAgent',
    'C:\Program Files\Python312\Lib\site-packages\agent',
    'C:\Program Files\Python312\Scripts\mc-agent*',
    'C:\Users\robert\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages\agent'
)
foreach ($d in $dirs) {
    if (Test-Path $d) {
        Write-Host "Removing $d"
        Remove-Item $d -Recurse -Force
    }
}

# 4. Remove leftover configs
$configs = @(
    'C:\MissionControlAgent\config.yaml',
    'C:\ProgramData\MissionControlAgent\config.yaml'
)
foreach ($c in $configs) {
    if (Test-Path $c) { Remove-Item $c -Force }
}

Write-Host "Uninstall complete. Reboot or reinstall from UI."
