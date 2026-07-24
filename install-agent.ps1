<#
.SYNOPSIS
    Install Mission Control Agent on Windows
.DESCRIPTION
    Copies the agent to Program Files, creates a config file,
    and registers it as a Windows service that starts automatically.
.PARAMETER ServerUrl
    Mission Control server URL (e.g. http://192.168.1.100:8000)
.PARAMETER AgentName
    Display name for this agent (defaults to computer name)
.PARAMETER NoSslVerify
    Disable SSL certificate verification
.PARAMETER HeartbeatInterval
    Seconds between heartbeats (default: 30)
.PARAMETER Uninstall
    Remove the agent service and files
.EXAMPLE
    .\install-agent.ps1 -ServerUrl http://192.168.1.100:8000 -AgentName "EGGBERT-PC"
.EXAMPLE
    .\install-agent.ps1 -Uninstall
#>

param(
    [string]$ServerUrl = "",
    [string]$AgentName = "",
    [switch]$NoSslVerify,
    [int]$HeartbeatInterval = 30,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$ServiceName = "MissionControlAgent"
$InstallDir = "$env:ProgramFiles\MissionControlAgent"
$AgentScript = "$InstallDir\agent\__main__.py"
$ConfigDir = "$env:USERPROFILE\.config\mission-control-agent"
$ConfigFile = "$ConfigDir\config.yaml"
$LogDir = "$env:ProgramData\MissionControlAgent\logs"
$ExeName = "mc-agent.exe"

# ── Helpers ──────────────────────────────────────────────

function Write-Status($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "[-] $msg" -ForegroundColor Red }

function Find-Python {
    foreach ($cmd in @("python", "python3", "py")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match "Python 3\.(\d+)") {
                $minor = [int]$Matches[1]
                if ($minor -ge 11) {
                    return $cmd
                }
            }
        } catch {}
    }
    return $null
}

function Install-Python {
    Write-Status "Python 3.11+ not found. Installing..."

    # Try winget first (Windows 10/11 built-in)
    $winget = Get-Command "winget" -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Status "Installing Python via winget..."
        winget install --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent 2>&1 | Out-Null
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $py = Find-Python
        if ($py) { return $py }
    }

    # Try chocolatey
    $choco = Get-Command "choco" -ErrorAction SilentlyContinue
    if ($choco) {
        Write-Status "Installing Python via Chocolatey..."
        choco install python --version=3.12 -y 2>&1 | Out-Null
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $py = Find-Python
        if ($py) { return $py }
    }

    # Download and install directly
    Write-Status "Downloading Python 3.12..."
    $pyUrl = "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"
    $pyInstaller = "$env:TEMP\python-installer.exe"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $pyUrl -OutFile $pyInstaller -UseBasicParsing
    } catch {
        Write-Fail "Failed to download Python: $_"
        return $null
    }

    Write-Status "Installing Python 3.12 (this may take a minute)..."
    Start-Process -FilePath $pyInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait -NoNewWindow
    Remove-Item $pyInstaller -Force -ErrorAction SilentlyContinue

    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    $py = Find-Python
    if ($py) {
        Write-Ok "Python installed: $py"
        return $py
    }

    Write-Fail "Python installation failed. Install manually from https://www.python.org/downloads/"
    return $null
}

# ── Uninstall ────────────────────────────────────────────

if ($Uninstall) {
    Write-Status "Uninstalling Mission Control Agent..."

    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($svc) {
        Write-Status "Stopping service..."
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        sc.exe delete $ServiceName | Out-Null
        Write-Ok "Service removed"
    }

    if (Test-Path $InstallDir) {
        Remove-Item -Recurse -Force $InstallDir
        Write-Ok "Removed $InstallDir"
    }

    Write-Ok "Uninstall complete."
    exit 0
}

# ── Preflight checks ─────────────────────────────────────

Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  Mission Control Agent Installer" -ForegroundColor White
Write-Host "========================================" -ForegroundColor White
Write-Host ""

$python = Find-Python
if (-not $python) {
    $python = Install-Python
    if (-not $python) {
        exit 1
    }
}
Write-Ok "Python found: $python"

if (-not $ServerUrl) {
    $ServerUrl = Read-Host "Server URL (e.g. http://192.168.1.100:8000)"
}
if (-not $ServerUrl) {
    Write-Fail "Server URL is required."
    exit 1
}

if (-not $AgentName) {
    $AgentName = $env:COMPUTERNAME
}
Write-Ok "Agent name: $AgentName"
Write-Ok "Server:    $ServerUrl"

# ── Stop existing service ────────────────────────────────

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Status "Stopping existing service..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# ── Copy agent files ─────────────────────────────────────

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentSource = Join-Path $ScriptDir ".agents"

if (-not (Test-Path $AgentSource)) {
    Write-Fail "Agent source not found at $AgentSource"
    Write-Fail "Run this script from the MissionControl project root."
    exit 1
}

Write-Status "Installing agent to $InstallDir..."
if (Test-Path $InstallDir) {
    # Stop any running agent processes first
    Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -and $_.Path.StartsWith($InstallDir)
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    try {
        Remove-Item -Recurse -Force $InstallDir
    } catch {
        Write-Status "Cleaning up locked files..."
        cmd.exe /c "rmdir /s /q `"$InstallDir`"" 2>&1 | Out-Null
        if (Test-Path $InstallDir) {
            Write-Fail "Could not remove $InstallDir — run this script as Administrator"
            exit 1
        }
    }
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null

# Copy agent package
Copy-Item -Recurse -Force "$AgentSource\agent" "$InstallDir\agent"
Copy-Item -Force "$AgentSource\pyproject.toml" "$InstallDir\"
Copy-Item -Force "$AgentSource\requirements.txt" "$InstallDir\"

Write-Ok "Agent files copied"

# ── Install Python dependencies ──────────────────────────

Write-Status "Installing Python dependencies..."
& $python -m pip install --quiet httpx psutil pydantic pydantic-settings pyyaml packaging 2>&1 | Out-Null
Write-Ok "Dependencies installed"

# ── Install as a package ─────────────────────────────────

Write-Status "Installing agent package..."
Push-Location $InstallDir
& $python -m pip install --quiet --no-deps -e . 2>&1 | Out-Null
Pop-Location
Write-Ok "Agent package installed"

# ── Create wrapper script ────────────────────────────────

$WrapperPath = "$InstallDir\mc-agent.ps1"
$WrapperContent = @"
`$env:MC_SERVER_URL = '$ServerUrl'
`$env:MC_AGENT_NAME = '$AgentName'
`$env:MC_HEARTBEAT_INTERVAL = '$HeartbeatInterval'
`$env:MC_LOG_LEVEL = 'INFO'
`$env:MC_LOG_FILE = '$LogDir\agent.log'
$(if ($NoSslVerify) { "`$env:MC_VERIFY_SSL = 'false'" })

& $python "$AgentScript" --log-file "$LogDir\agent.log"
"@
Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding UTF8
Write-Ok "Wrapper script created"

# ── Create config file ───────────────────────────────────

Write-Status "Creating config file..."
New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null

$SslVerify = if ($NoSslVerify) { "false" } else { "true" }
$configYaml = @"
# Mission Control Agent Configuration
# Installed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

server_url: "$ServerUrl"
agent_name: "$AgentName"
heartbeat_interval: $HeartbeatInterval
inventory_interval: 300
verify_ssl: $SslVerify
log_level: "INFO"
log_file: "$LogDir\agent.log"
command_timeout: 60
"@
Set-Content -Path $ConfigFile -Value $configYaml -Encoding UTF8
Write-Ok "Config written to $ConfigFile"

# ── Create log directory ─────────────────────────────────

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# ── Register as Windows service ──────────────────────────

Write-Status "Registering Windows service..."

# Find python.exe full path
$pythonExe = (Get-Command $python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    $pythonExe = $python
}

# Create a batch launcher for the service
$BatchPath = "$InstallDir\start-agent.bat"
$BatchContent = @"
@echo off
cd /d "$InstallDir"
"$pythonExe" "$AgentScript"
"@
Set-Content -Path $BatchPath -Value $BatchContent -Encoding ASCII

# Use NSSM if available, otherwise use sc.exe + srvany approach
$nssm = Get-Command "nssm" -ErrorAction SilentlyContinue

if ($nssm) {
    Write-Status "Using NSSM to register service..."
    nssm stop $ServiceName 2>&1 | Out-Null
    nssm remove $ServiceName confirm 2>&1 | Out-Null
    nssm install $ServiceName $BatchPath
    nssm set $ServiceName DisplayName "Mission Control Agent"
    nssm set $ServiceName Description "Outbound-only agent for Mission Control"
    nssm set $ServiceName Start SERVICE_AUTO_START
    nssm set $ServiceName AppDirectory $InstallDir
    nssm set $ServiceName AppStdout "$LogDir\service-stdout.log"
    nssm set $ServiceName AppStderr "$LogDir\service-stderr.log"
    nssm set $ServiceName AppRotateFiles 1
    nssm set $ServiceName AppRotateBytes 10485760
    Write-Ok "Service registered via NSSM"
} else {
    # Fallback: create a scheduled task that runs at startup
    Write-Status "NSSM not found. Registering as scheduled task..."

    $taskName = $ServiceName
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    $action = New-ScheduledTaskAction `
        -Execute "cmd.exe" `
        -Argument "/c `"$BatchPath`"" `
        -WorkingDirectory $InstallDir

    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)

    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Mission Control Agent - outbound heartbeat and command execution" `
        | Out-Null

    Write-Ok "Scheduled task registered (runs at startup as SYSTEM)"
}

# ── Start the agent ──────────────────────────────────────

Write-Status "Starting agent..."
if ($nssm) {
    nssm start $ServiceName 2>&1 | Out-Null
} else {
    Start-ScheduledTask -TaskName $ServiceName -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Agent name:     $AgentName"
Write-Host "  Server:         $ServerUrl"
Write-Host "  Config:         $ConfigFile"
Write-Host "  Logs:           $LogDir\agent.log"
Write-Host "  Install dir:    $InstallDir"
Write-Host ""
Write-Host "  The agent will register with the server on first"
Write-Host "  heartbeat and appear in the Agents page."
Write-Host ""
Write-Host "  To uninstall: .\install-agent.ps1 -Uninstall"
Write-Host ""
