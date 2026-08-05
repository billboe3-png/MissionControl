#requires -RunAsAdministrator
<#
.SYNOPSIS
    Mission Control Edge Agent - One-Click Windows Installer
.DESCRIPTION
    Downloads agent bundle, configures, and installs as SYSTEM scheduled task.
.PARAMETER ServerUrl
    Mission Control server URL (default: https://missioncontrol.optichosting.co.za)
.PARAMETER AgentId
    Agent ID (default: 1)
.PARAMETER ApiKey
    Agent API key
.PARAMETER PythonPath
    Full path to Python executable
.PARAMETER WorkDir
    Agent working directory
.EXAMPLE
    .\install-agent.ps1 -AgentId 2 -ApiKey "your-key"
#>
param(
    [string]$ServerUrl = "https://missioncontrol.optichosting.co.za",
    [string]$AgentId = "1",
    [string]$ApiKey = "mc_agent_cd1a4b965593a04b05a4a919e0878222b8db924514a403a4f4129db59f2bb796",
    [string]$PythonPath = "C:\Users\robert\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe",
    [string]$WorkDir = "C:\MissionControlAgent"
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== Mission Control Edge Agent Installer ===" -ForegroundColor Cyan
Write-Host "Server: $ServerUrl" -ForegroundColor Gray
Write-Host "Agent ID: $AgentId`n" -ForegroundColor Gray

# 1. Create work directory
Write-Host "[1/6] Creating work directory..." -ForegroundColor Yellow
New-Item -Path $WorkDir -ItemType Directory -Force | Out-Null

# 2. Download bundle
Write-Host "[2/6] Downloading agent bundle..." -ForegroundColor Yellow
$ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$bundleUrl = "$ServerUrl/api/v1/agents/$AgentId/bundles/download?t=$ts"
$bundleZip = Join-Path $WorkDir "agent-bundle-live.zip"

if (-not (Test-Path $bundleZip)) {
    curl.exe -k -L -X POST -o $bundleZip $bundleUrl 2>&1 | Out-Null
} else {
    Write-Host "  Using existing bundle" -ForegroundColor Gray
}

if (-not (Test-Path $bundleZip)) {
    throw "Bundle download failed from $bundleUrl"
}
$bundleSize = (Get-Item $bundleZip).Length
Write-Host "  Downloaded: $bundleSize bytes" -ForegroundColor Green

# 3. Extract bundle
Write-Host "[3/6] Extracting bundle..." -ForegroundColor Yellow
Remove-Item "$WorkDir\agent" -Recurse -Force -ErrorAction SilentlyContinue
$extractScript = @"
import zipfile, sys
z = zipfile.ZipFile(sys.argv[1])
z.extractall(sys.argv[2])
print('Extracted', len(z.namelist()), 'files')
"@
$extractScript | Out-File -FilePath "$WorkDir\_extract.py" -Encoding ascii
& $PythonPath "$WorkDir\_extract.py" $bundleZip $WorkDir
Remove-Item "$WorkDir\_extract.py" -ErrorAction SilentlyContinue

# 4. Write config.yaml
Write-Host "[4/6] Writing config.yaml..." -ForegroundColor Yellow
$config = @"
server_url: $ServerUrl
verify_ssl: false
agent_id: $AgentId
api_key: $ApiKey
data_dir: "$WorkDir\data"
config_dir: "$WorkDir"
"@
[System.IO.File]::WriteAllText("$WorkDir\config.yaml", $config)
New-Item -Path "$WorkDir\data" -ItemType Directory -Force | Out-Null
Write-Host "  Config written" -ForegroundColor Green

# 5. Create scheduled task
Write-Host "[5/6] Creating scheduled task..." -ForegroundColor Yellow
schtasks /Delete /TN "MissionControlEdgeAgent" /F 2>&1 | Out-Null
$action = New-ScheduledTaskAction -Execute $PythonPath -Argument '-m agent.edge_main' -WorkingDirectory $WorkDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Seconds 0)
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName 'MissionControlEdgeAgent' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "  Task created" -ForegroundColor Green

# 6. Run and verify
Write-Host "[6/6] Starting agent..." -ForegroundColor Yellow
schtasks /Run /TN "MissionControlEdgeAgent"
Start-Sleep -Seconds 20

Write-Host "`n=== Installation Complete ===" -ForegroundColor Cyan
Write-Host "Agent installed as scheduled task: MissionControlEdgeAgent" -ForegroundColor Green
Write-Host "To restart later:" -ForegroundColor Gray
Write-Host '  schtasks /End /TN "MissionControlEdgeAgent"' -ForegroundColor Gray
Write-Host '  schtasks /Run /TN "MissionControlEdgeAgent"' -ForegroundColor Gray
