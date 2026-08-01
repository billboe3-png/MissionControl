<#
.SYNOPSIS
Mission Control Agent Installer for Windows.

.DESCRIPTION
Downloads the agent bundle from the Mission Control server, configures it,
and installs a scheduled task to run it as SYSTEM.

.PARAMETER AgentId
The agent ID from the Mission Control UI.

.PARAMETER ApiKey
The full agent API key from the Mission Control UI.

.PARAMETER ServerUrl
Mission Control server URL. Default: https://missioncontrol.optichosting.co.za

.PARAMETER InstallDir
Agent installation directory. Default: C:\MissionControlAgent

.PARAMETER PythonExe
Python executable to use. Default: py -3

.EXAMPLE
.\install-agent.ps1 -AgentId 1 -ApiKey "mc_agent_..."

.EXAMPLE
.\install-agent.ps1 -AgentId 1 -ApiKey "mc_agent_..." -ServerUrl "https://your-server.com"
#>
param(
    [Parameter(Mandatory=$true)][string]$AgentId,
    [Parameter(Mandatory=$true)][string]$ApiKey,
    [Parameter(Mandatory=$false)][string]$ServerUrl = "https://missioncontrol.optichosting.co.za",
    [Parameter(Mandatory=$false)][string]$InstallDir = "C:\MissionControlAgent",
    [Parameter(Mandatory=$false)][string]$PythonExe = "py -3"
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

Write-Host ""
Write-Host "Mission Control Agent Installer"
Write-Host "================================"
Write-Host ""

# 1. Validate parameters
Write-Host "[1/6] Validating parameters..."
if (-not $AgentId -match '^\d+$') {
    Write-Host "ERROR: AgentId must be a number." -ForegroundColor Red
    exit 1
}
if (-not $ApiKey.StartsWith('mc_agent_')) {
    Write-Host "WARNING: ApiKey does not start with 'mc_agent_'. Is this correct?" -ForegroundColor Yellow
}
Write-Host "  Agent ID:   $AgentId"
Write-Host "  Server:     $ServerUrl"
Write-Host "  Install:    $InstallDir"
Write-Host "  Python:     $PythonExe"
Write-Host ""

# 2. Create directories
Write-Host "[2/6] Creating directories..."
$dirs = @($InstallDir, (Join-Path $InstallDir "logs"), (Join-Path $InstallDir "agent"))
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
    Write-Host "  Created: $d"
}

# 3. Download bundle
Write-Host "[3/6] Downloading agent bundle..."
$zipPath = Join-Path $InstallDir "agent-bundle.zip"
try {
    $headers = @{
        "Content-Type" = "application/json"
        "X-Agent-API-Key" = $ApiKey
    }
    $body = @{ agent_id = [int]$AgentId } | ConvertTo-Json
    Invoke-RestMethod -Uri "$ServerUrl/api/v1/agents/$AgentId/bundles/download" -Method Post -Headers $headers -Body $body -OutFile $zipPath -ErrorAction Stop
    $size = (Get-Item $zipPath).Length
    if ($size -lt 1000) {
        throw "Downloaded file is too small ($size bytes). Check network/auth."
    }
    Write-Host "  Downloaded: $size bytes"
} catch {
    Write-Host "  ERROR: $_" -ForegroundColor Red
    exit 1
}

# 4. Extract and fix structure
Write-Host "[4/6] Extracting bundle..."
Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
$zipItem = Join-Path $InstallDir "agent"
if (-not (Test-Path $zipItem)) {
    Write-Host "  Fixing bundle structure..."
    $pyFiles = Get-ChildItem $InstallDir -Filter *.py
    $dirs = Get-ChildItem $InstallDir -Directory | Where-Object { $_.Name -ne "agent" -and $_.Name -ne "logs" }
    foreach ($f in $pyFiles) {
        Move-Item $f.FullName (Join-Path $InstallDir "agent") -Force
    }
    foreach ($d in $dirs) {
        Move-Item $d.FullName (Join-Path $InstallDir "agent") -Force
    }
}
Remove-Item $zipPath -Force
Write-Host "  Extracted to: $InstallDir"

# 5. Write config
Write-Host "[5/6] Writing configuration..."
$configPath = Join-Path $InstallDir "config.yaml"
$yaml = @"
server_url: $ServerUrl
agent_id: $AgentId
api_key: $ApiKey
heartbeat_interval: 30
log_file: $InstallDir\logs\agent.log
"@
[System.IO.File]::WriteAllText($configPath, $yaml, [System.Text.UTF8Encoding]::new($false))
Write-Host "  Config: $configPath"

# 6. Create run script
Write-Host "[6/6] Creating run script and scheduled task..."
$runBat = "@echo off`r`ncd /d $InstallDir`r`n$PythonExe -m agent --config `"$InstallDir\config.yaml`" --log-file `"$InstallDir\logs\agent.log`""
$batPath = Join-Path $InstallDir "run-agent.bat"
Set-Content -Path $batPath -Value $runBat
Write-Host "  Run script: $batPath"

# Register scheduled task
schtasks /Delete /TN "MissionControlAgent" /F 2>$null | Out-Null
$tr = "cmd /c `"$batPath`""
schtasks /Create /TN "MissionControlAgent" /TR $tr /SC ONSTART /RU SYSTEM /F | Out-Null
Start-Sleep -Seconds 2
schtasks /Run /TN "MissionControlAgent" | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Verification:"
Write-Host "  Task status:  schtasks /Query /TN `"MissionControlAgent`" /FO LIST /V"
Write-Host "  Agent log:    Get-Content $InstallDir\logs\agent.log -Tail 20"
Write-Host "  Uninstall:    .\uninstall-agent.ps1"
Write-Host ""
