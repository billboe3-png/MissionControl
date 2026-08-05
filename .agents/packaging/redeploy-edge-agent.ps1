<#
.SYNOPSIS
One-click redeploy for CORHQROBERTB: uninstalls old agent, downloads latest edge bundle, installs new Windows service.
#>

$ErrorActionPreference = 'Stop'

$ServerUrl = 'https://missioncontrol.optichosting.co.za'
$AgentId = 1
$InstallDir = 'C:\MissionControlAgent'
$BundleZip = "$env:TEMP\mc-edge-bundle.zip"

function Write-Ok($msg) { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "[-] $msg" -ForegroundColor Red }
function Write-Status($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }

# 1. Stop old scheduled task if present
Write-Status "Stopping old scheduled task..."
$task = Get-ScheduledTask -TaskName 'MissionControlAgent' -ErrorAction SilentlyContinue
if ($task) {
    Stop-ScheduledTask -TaskName 'MissionControlAgent' -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName 'MissionControlAgent' -Confirm:$false -ErrorAction SilentlyContinue
    Write-Ok "Old scheduled task removed"
}

# 2. Uninstall old service if present
Write-Status "Removing old service..."
$oldService = Get-Service -Name 'MissionControlEdgeAgent' -ErrorAction SilentlyContinue
if ($oldService) {
    Stop-Service -Name 'MissionControlEdgeAgent' -Force -ErrorAction SilentlyContinue
    sc.exe delete MissionControlEdgeAgent | Out-Null
    Write-Ok "Old service removed"
}
$oldDirs = @('C:\MissionControlAgent', "$env:ProgramData\MissionControlAgent", $InstallDir)
foreach ($d in $oldDirs) {
    if (Test-Path $d) {
        Remove-Item $d -Recurse -Force -ErrorAction SilentlyContinue
        Write-Ok "Removed $d"
    }
}

# 2. Download fresh bundle
Write-Status "Downloading edge agent bundle from $ServerUrl ..."
$configPath = Join-Path $InstallDir 'config.yaml'
if (-not (Test-Path $configPath)) { $configPath = "$env:ProgramData\MC Edge Agent\config.yaml" }
if (-not (Test-Path $configPath)) { $configPath = "$env:ProgramData\MissionControlAgent\config.yaml" }
if (-not (Test-Path $configPath)) {
    Write-Fail "Could not find agent config.yaml; aborting."
    exit 1
}
$apiKey = (Get-Content $configPath | Select-String 'api_key' | ForEach-Object { $_ -replace '.*api_key:\s*', '' }.Trim())
if (-not $apiKey) {
    Write-Fail "Could not read API key from config; aborting."
    exit 1
}
curl.exe -k -L -o $BundleZip `
    -H "Authorization: Bearer $apiKey" `
    "$ServerUrl/api/v1/agents/$AgentId/bundles/download" 2>&1 | Out-Null
if (-not (Test-Path $BundleZip)) {
    Write-Fail "Bundle download failed"
    exit 1
}
Write-Ok "Bundle downloaded: $((Get-Item $BundleZip).Length) bytes"

# 3. Extract bundle
Write-Status "Extracting bundle..."
$extractDir = "$env:TEMP\mc-edge-bundle"
if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
Expand-Archive -Path $BundleZip -DestinationPath $extractDir -Force
$agentSrc = Join-Path $extractDir 'agent'
if (-not (Test-Path (Join-Path $agentSrc '__main__.py'))) {
    Write-Fail "Bundle structure unexpected"
    exit 1
}
Write-Ok "Bundle extracted"

# 4. Copy into install dir
Write-Status "Installing to $InstallDir ..."
if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null }
Copy-Item "$agentSrc\*" -Destination $InstallDir -Recurse -Force
Write-Ok "Files installed"

# 5. Install dependencies
Write-Status "Installing Python dependencies..."
$py = 'C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }
& $py -m pip install --quiet httpx psutil pydantic pydantic-settings pyyaml packaging paramiko pywinrm pysnmp pywin32 2>$null
Write-Ok "Dependencies ready"

# 6. Write run-agent.bat
$bat = @"
@echo off
cd /d "C:\Program Files\MC Edge Agent"
"C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe" -m agent
"@
Set-Content -Path "$InstallDir\run-agent.bat" -Value $bat -Encoding ASCII
Write-Ok "run-agent.bat written"

# 7. Register Windows service via NSSM
Write-Status "Registering Windows service..."
$nssmDir = "$InstallDir\tools"
New-Item -ItemType Directory -Path $nssmDir -Force | Out-Null
$nssmZip = "$env:TEMP\nssm.zip"
if (-not (Test-Path "$nssmDir\nssm.exe")) {
    curl.exe -k -L -o $nssmZip "https://nssm.cc/release/nssm-win64.zip" 2>&1 | Out-Null
    Expand-Archive -Path $nssmZip -DestinationPath $nssmDir -Force
    $nssmExe = Get-ChildItem $nssmDir -Recurse -Filter 'nssm.exe' | Select-Object -First 1
    if ($nssmExe) { $env:Path += ";$nssmDir" } else { Write-Fail "nssm.exe missing"; exit 1 }
}
nssm stop MissionControlEdgeAgent 2>&1 | Out-Null
nssm remove MissionControlEdgeAgent confirm 2>&1 | Out-Null
nssm install MissionControlEdgeAgent $py "-m agent --log-file `"$InstallDir\logs\agent.log`""
nssm set MissionControlEdgeAgent DisplayName "Mission Control Edge Agent"
nssm set MissionControlEdgeAgent Description "Outbound-only edge collector for Mission Control"
nssm set MissionControlEdgeAgent Start SERVICE_AUTO_START
nssm set MissionControlEdgeAgent AppDirectory $InstallDir
nssm set MissionControlEdgeAgent AppStdout "$InstallDir\logs\service-stdout.log"
nssm set MissionControlEdgeAgent AppStderr "$InstallDir\logs\service-stderr.log"
nssm set MissionControlEdgeAgent AppRotateFiles 1
nssm set MissionControlEdgeAgent AppRotateBytes 10485760
nssm set MissionControlEdgeAgent AppExit 0 "Ignore"
nssm set MissionControlEdgeAgent AppRestartDelay 5000
Write-Ok "Service registered"

# 8. Start service
Write-Status "Starting service..."
Start-Service -Name 'MissionControlEdgeAgent' -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
$svc = Get-Service -Name 'MissionControlEdgeAgent' -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq 'Running') {
    Write-Ok "Service running"
} else {
    Write-Fail "Service not running; check $InstallDir\logs"
}

# 9. Verify edge calls
Write-Status "Waiting 10s for first heartbeat..."
Start-Sleep -Seconds 10
Write-Host "Check backend logs for /api/v1/edge/1/config and /api/v1/edge/1/heartbeat"
Write-Ok "Redeploy complete"
