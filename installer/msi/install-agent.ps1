#requires -RunAsAdministrator
<#
.SYNOPSIS
    Mission Control Edge Agent - Windows installer (self-registering).

.DESCRIPTION
    Creates a dedicated virtualenv, installs agent dependencies, downloads the
    agent bundle from the Mission Control server, registers this machine using a
    one-time registration token, and installs the agent as a SYSTEM scheduled
    task that starts at boot.

    No pre-existing Python virtualenv and no long-lived API key are required.
    The one-time token is exchanged for the agent API key, which is stored in
    config.yaml on the target machine only.

.PARAMETER ServerUrl
    Mission Control server URL.

.PARAMETER RegistrationToken
    One-time registration token generated on the server.

.PARAMETER AgentName
    Display name for this agent. Defaults to the computer hostname.

.PARAMETER WorkDir
    Installation directory. Defaults to C:\MissionControlAgent.

.PARAMETER SkipSslVerify
    Skip TLS verification when contacting the server.

.PARAMETER NoPythonInstall
    Do not attempt to install Python. By default the script installs Python 3.12
    automatically when no suitable interpreter is found, using winget if present
    and otherwise downloading the official installer from python.org.

.PARAMETER NonInteractive
    Never prompt. Used when this script is driven by an MSI custom action.

.PARAMETER PreferDownload
    Ignore the agent bundle shipped next to this script and fetch the newest one
    from the server instead. Useful after the server-side agent is updated.

.PARAMETER BundlePath
    Use this specific agent bundle zip instead of auto-discovering one.

.PARAMETER RegistrationToken
    Optional. A brand-new machine self-registers without one. Supply a token
    only when re-installing over a hostname that is already registered.

.EXAMPLE
    .\install-agent.ps1

.EXAMPLE
    .\install-agent.ps1 -RegistrationToken "0jh...xyz"

.NOTES
    Requires internet access to the Mission Control server.
    Self-registration means any machine reaching the server can enrol itself.
#>
[CmdletBinding()]
param(
    [string]$ServerUrl = "https://missioncontrol.optichosting.co.za",
    [string]$RegistrationToken = "",
    [string]$AgentName = "",
    [string]$WorkDir = "C:\MissionControlAgent",
    [switch]$SkipSslVerify,
    [switch]$NoPythonInstall,
    [switch]$NonInteractive,
    [switch]$PreferDownload,
    [string]$BundlePath = ""
)

$ErrorActionPreference = "Stop"
$TaskName = "MissionControlEdgeAgent"

function Write-Step { param([string]$m) Write-Host "[$m]" -ForegroundColor Yellow }
function Write-Ok   { param([string]$m) Write-Host "      $m" -ForegroundColor Green }

# ---------------------------------------------------------------------------
# 0. Administrator check
# ---------------------------------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    throw "Must run as Administrator. Right-click PowerShell and choose 'Run as administrator'."
}

Write-Host ""
Write-Host "=== Mission Control Edge Agent Installer ===" -ForegroundColor Cyan
Write-Host "  Server : $ServerUrl" -ForegroundColor Gray
Write-Host "  Target : $WorkDir" -ForegroundColor Gray
Write-Host ""

# Always keep a transcript. An MSI custom action has no visible console, so this
# log is the only way to diagnose a failed install afterwards.
if (-not (Test-Path $WorkDir)) { New-Item -Path $WorkDir -ItemType Directory -Force | Out-Null }
try {
    Start-Transcript -Path (Join-Path $WorkDir "install.log") -Append | Out-Null
    Write-Host "[$(Get-Date -Format s)] starting (interactive=$([bool]$NonInteractive -eq $false))"
} catch {
    Write-Host "Could not start transcript: $($_.Exception.Message)"
}

# ---------------------------------------------------------------------------
# 1. Locate a suitable Python (3.10+)
# ---------------------------------------------------------------------------
Write-Step "1/7 Locating Python 3.10+"

function Find-Python {
    $candidates = New-Object System.Collections.ArrayList

    $pyExe = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyExe) {
        foreach ($ver in @("-3.12", "-3.11", "-3.10")) {
            try {
                $resolved = & $pyExe.Source $ver -c "import sys;print(sys.executable)" 2>$null
                if ($resolved -and (Test-Path $resolved)) {
                    [void]$candidates.Add($resolved.Trim())
                }
            } catch { }
        }
    }

    foreach ($name in @("python.exe", "python3.exe")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { [void]$candidates.Add($cmd.Source) }
    }

    $patterns = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
        "C:\Python3*\python.exe",
        "$env:ProgramFiles\Python3*\python.exe"
    )
    foreach ($pattern in $patterns) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue
        if ($found) {
            foreach ($item in @($found)) { [void]$candidates.Add($item.FullName) }
        }
    }

    foreach ($c in ($candidates | Select-Object -Unique)) {
        try {
            $ver = & $c -c "import sys;print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and $ver) {
                $parts = $ver.Trim().Split('.')
                if ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 10) {
                    return @{ Path = $c; Version = $ver.Trim() }
                }
            }
        } catch { }
    }
    return $null
}

function Refresh-Path {
    # An installer writes PATH to the registry; this process inherited the old value.
    $env:PATH = [Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                 [Environment]::GetEnvironmentVariable("PATH", "User")
}

function Install-Python {
    # Windows Server and LTSC images ship without winget, so fall back to
    # downloading the official installer from python.org and running it silently.
    Refresh-Path
    $found = Find-Python
    if ($found) { return $found }

    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "  Trying winget..." -ForegroundColor Yellow
        & $winget.Source install --id Python.Python.3.12 -e `
            --accept-package-agreements --accept-source-agreements --silent
        Write-Host "  winget exited with code $LASTEXITCODE" -ForegroundColor DarkGray
        Refresh-Path
        $found = Find-Python
        if ($found) { return $found }
        Write-Host "  winget did not produce a usable interpreter." -ForegroundColor Yellow
    } else {
        Write-Host "  winget is not installed here - using direct download." -ForegroundColor Yellow
    }

    $arch = "amd64"
    if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { $arch = "arm64" }
    $version = "3.12.10"
    $url = "https://www.python.org/ftp/python/$version/python-$version-$arch.exe"
    $exe = Join-Path $env:TEMP "python-$version-$arch.exe"

    Write-Host "  Downloading $url (about 27 MB)" -ForegroundColor Yellow
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing -TimeoutSec 900
    } catch {
        throw "Failed to download the Python installer: $($_.Exception.Message)"
    }

    if (-not (Test-Path $exe)) { throw "Python installer download produced no file." }
    $size = (Get-Item $exe).Length
    if ($size -lt 5MB) { throw "Python installer is only $size bytes - download looks corrupt." }

    Write-Host "  Running the Python installer silently..." -ForegroundColor Yellow
    $proc = Start-Process -FilePath $exe -ArgumentList @(
        "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_pip=1",
        "Include_test=0", "Include_launcher=0", "AssociateFiles=0", "Shortcuts=0"
    ) -Wait -PassThru

    # 0 = success, 3010 = success but a reboot is required.
    if ($proc.ExitCode -ne 0 -and $proc.ExitCode -ne 3010) {
        throw "Python installer failed with exit code $($proc.ExitCode)."
    }
    Remove-Item $exe -Force -ErrorAction SilentlyContinue

    Refresh-Path
    return (Find-Python)
}

$python = Find-Python

if (-not $python) {
    Write-Host ""
    Write-Host "Python 3.10 or newer was not found on this machine." -ForegroundColor Red
    Write-Host ""

    if (-not $NoPythonInstall) {
        Write-Host "Installing Python 3.12 automatically (this can take several minutes)..." -ForegroundColor Yellow
        Write-Host ""
        $python = Install-Python
    }

    if (-not $python) {
        Write-Host ""
        Write-Host "Automatic installation did not complete." -ForegroundColor Yellow
        Write-Host "Install Python 3.10+ manually, then re-run this script:" -ForegroundColor Yellow
        Write-Host "  https://www.python.org/downloads/windows/" -ForegroundColor White
        Write-Host '  (tick "Add python.exe to PATH" during setup)' -ForegroundColor Gray
        Write-Host ""
        throw "No suitable Python interpreter found."
    }

    Write-Ok "Installed Python $($python.Version)"
}
Write-Ok "Found Python $($python.Version) at $($python.Path)"

# ---------------------------------------------------------------------------
# 2. Create work directory and virtualenv
# ---------------------------------------------------------------------------
Write-Step "2/7 Creating virtualenv"
if (-not (Test-Path $WorkDir)) {
    New-Item -Path $WorkDir -ItemType Directory -Force | Out-Null
}
$VenvDir = Join-Path $WorkDir "venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

# Strip inherited PYTHONHOME/PYTHONPATH. If this shell (or a parent process,
# such as an MSI custom action) already sits inside another Python environment,
# those variables leak into the new interpreter and cause "SRE module mismatch"
# or a silently broken virtualenv.
if ($env:PYTHONHOME) {
    Write-Host "      Clearing inherited PYTHONHOME" -ForegroundColor DarkGray
    Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
}
if ($env:PYTHONPATH) {
    Write-Host "      Clearing inherited PYTHONPATH" -ForegroundColor DarkGray
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
}

if (Test-Path $VenvPython) {
    Write-Ok "Virtualenv already exists, reusing it"
} else {
    & $python.Path -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtualenv at $VenvDir" }
    Write-Ok "Created $VenvDir"
}

# ---------------------------------------------------------------------------
# 3. Install agent dependencies
# ---------------------------------------------------------------------------
Write-Step "3/7 Installing agent dependencies"
& $VenvPython -m pip install --quiet --upgrade pip
& $VenvPython -m pip install --quiet `
    "httpx>=0.27" "psutil>=5.9" "pydantic>=2.7" "pydantic-settings>=2.3" `
    "pyyaml>=6.0" "pywin32>=306" "WMI>=1.5.1" "cryptography>=42.0" `
    "docker>=7.0" "paramiko>=3.4.0"
# servicemanager / asyncssh / pysnmp are imported lazily inside
# functions, so they are intentionally NOT installed here: the agent starts and
# runs fine without them, and the features that need them report a clear error.
# paramiko is installed because SSH relay is now required by the Veeam bridge.
if ($LASTEXITCODE -ne 0) { throw "Failed to install agent dependencies." }
Write-Ok "Dependencies installed"

# ---------------------------------------------------------------------------
# 4. Download the agent bundle
# ---------------------------------------------------------------------------
Write-Step "4/7 Locating the agent bundle"
$ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$bundleUrl = "$ServerUrl/api/v1/agents/bundles/download?t=$ts"
$bundleZip = Join-Path $WorkDir "agent-bundle.zip"
$hdrFile = Join-Path $WorkDir "bundle-headers.txt"

$curlCommon = @("-sS", "-f", "-L", "-k")

function Test-BundleFile {
    param([string]$Path)
    # A bundle is only usable if it is big enough AND is a real zip with the
    # agent package in it. Guards against proxies that return HTML error pages.
    if (-not (Test-Path $Path)) { return $false }
    $len = (Get-Item $Path).Length
    if ($len -lt 50KB) { return $false }
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
        $archive = [System.IO.Compression.ZipFile]::OpenRead($Path)
        $count = $archive.Entries.Count
        $hasAgent = @($archive.Entries | Where-Object { $_.FullName -like "agent/*" }).Count -gt 0
        $archive.Dispose()
        return ($count -gt 10 -and $hasAgent)
    } catch {
        return $false
    }
}

# The installer ships with the agent bundle next to it, so a machine can be
# installed even when the bundle endpoint is unreachable. Only fall back to the
# network if no usable local bundle is present.
$bundleSource = $null

if (-not $PreferDownload) {
    $candidates = New-Object System.Collections.ArrayList

    if (-not [string]::IsNullOrWhiteSpace($BundlePath)) {
        [void]$candidates.Add($BundlePath)
    }
    if (Test-Path $bundleZip) { [void]$candidates.Add($bundleZip) }

    # Anything zip-shaped sitting beside this script, e.g. the bundled
    # missioncontrol-agent-3.0.0-rc1.zip.
    $searchDirs = @()
    if ($PSScriptRoot) { $searchDirs += $PSScriptRoot }
    $callerDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if ($callerDir -and $callerDir -notin $searchDirs) { $searchDirs += $callerDir }

    foreach ($dir in $searchDirs) {
        foreach ($pattern in @("missioncontrol-agent-*.zip", "agent-bundle*.zip")) {
            $found = Get-ChildItem -Path $dir -Filter $pattern -File -ErrorAction SilentlyContinue
            if ($found) { foreach ($f in @($found)) { [void]$candidates.Add($f.FullName) } }
        }
    }

    foreach ($c in ($candidates | Select-Object -Unique)) {
        if (Test-BundleFile -Path $c) {
            $bundleSource = $c
            break
        }
    }
}

if ($bundleSource) {
    if ($bundleSource -ne $bundleZip) {
        Copy-Item $bundleSource $bundleZip -Force
    }
    Write-Ok "Using local bundle: $(Split-Path $bundleSource -Leaf) ($((Get-Item $bundleZip).Length) bytes)"
    Write-Ok "No download needed - the server is only contacted to register."
    $preExisting = $true
} else {
    if (Test-Path $bundleZip) {
        Write-Host "      Ignoring unusable agent-bundle.zip" -ForegroundColor DarkGray
    }
    $preExisting = $false
}

# curl honours HTTPS_PROXY/http_proxy from the environment. Corporate proxies
# frequently refuse binary downloads with 403, so if the proxy is in play and
# the first attempt is refused, retry with the proxy bypassed.
$proxyVars = @($env:HTTPS_PROXY, $env:HTTP_PROXY, $env:ALL_PROXY) |
             Where-Object { $_ }
if ($proxyVars) {
    Write-Host "      Proxy configured: $($proxyVars -join ', ')" -ForegroundColor DarkGray
}

function Invoke-BundleDownload {
    param([string[]]$ExtraArgs)
    if (Test-Path $bundleZip) { Remove-Item $bundleZip -Force -ErrorAction SilentlyContinue }
    if (Test-Path $hdrFile) { Remove-Item $hdrFile -Force -ErrorAction SilentlyContinue }
    $code = & curl.exe @curlCommon @ExtraArgs -o $bundleZip -D $hdrFile `
        -w "%{http_code}" $bundleUrl
    return @{ Code = "$code"; Exit = $LASTEXITCODE }
}

if (-not $preExisting) {
    $attempt = Invoke-BundleDownload -ExtraArgs @()

    if ($attempt.Code -eq "403" -and $proxyVars) {
        Write-Host "      Server refused (403) - retrying without the proxy" -ForegroundColor Yellow
        $attempt = Invoke-BundleDownload -ExtraArgs @("--noproxy", "*")
    }

    if ($attempt.Code -ne "200") {
        # Surface who actually answered: a proxy or WAF, versus our own nginx.
        $who = "unknown"
        if (Test-Path $hdrFile) {
            $serverLine = Select-String -Path $hdrFile -Pattern "^Server:" -ErrorAction SilentlyContinue |
                          Select-Object -First 1
            if ($serverLine) { $who = $serverLine.Line.Trim() }
        }
        Write-Host ""
        Write-Host "      HTTP $($attempt.Code)  (answered by: $who)" -ForegroundColor Red
        Write-Host "      URL: $bundleUrl" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "      If the server above is not nginx, a proxy or security filter" -ForegroundColor Yellow
        Write-Host "      on this network is blocking the download. To confirm, run:" -ForegroundColor Yellow
        Write-Host "        curl.exe -v -o NUL `"$bundleUrl`"" -ForegroundColor White
        Write-Host "        curl.exe -s -o NUL -w `"%{http_code}`" $ServerUrl/api/v1/health" -ForegroundColor White
        Write-Host ""
        Write-Host "      Workaround: download the bundle on another machine and copy it to" -ForegroundColor Yellow
        Write-Host "        $bundleZip" -ForegroundColor White
        Write-Host "      then re-run this installer - it will reuse it." -ForegroundColor Yellow
        Write-Host ""
        throw "Bundle download failed (HTTP $($attempt.Code))."
    }

    $got = (Get-Item $bundleZip).Length
    if ($got -lt 50KB) {
        throw "Bundle is only $got bytes - that is too small to be a real agent bundle."
    }
    Write-Ok "Downloaded $got bytes"
}

# ---------------------------------------------------------------------------
# 5. Extract bundle
# ---------------------------------------------------------------------------
Write-Step "5/7 Extracting bundle"
$agentDir = Join-Path $WorkDir "agent"
if (Test-Path $agentDir) { Remove-Item $agentDir -Recurse -Force }
& $VenvPython -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $bundleZip $WorkDir
if ($LASTEXITCODE -ne 0) { throw "Failed to extract bundle." }

# The bundle ships __pycache__ compiled on other machines/versions; drop it.
Get-ChildItem -Path $agentDir -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $agentDir -Filter "*.pyc" -Recurse -File -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
Write-Ok "Extracted to $agentDir"

# ---------------------------------------------------------------------------
# 6. Register this agent with the server (one-time token -> API key)
# ---------------------------------------------------------------------------
Write-Step "6/7 Registering agent with server"
if ([string]::IsNullOrWhiteSpace($AgentName)) {
    $AgentName = $env:COMPUTERNAME
}

$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
$osCaption = if ($os) { $os.Caption } else { "Windows" }
$osVersion = if ($os) { "$($os.Version) ($env:PROCESSOR_ARCHITECTURE)" } else { "" }
$ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
       Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
       Select-Object -First 1).IPAddress

$registerPayload = [ordered]@{
    name             = $AgentName
    hostname         = $env:COMPUTERNAME
    operating_system = $osCaption
    os_version       = $osVersion
    ip_address       = $ip
    agent_version    = "3.0.0-rc1-edge"
}
if (-not [string]::IsNullOrWhiteSpace($RegistrationToken)) {
    $registerPayload["registration_token"] = $RegistrationToken
} else {
    Write-Ok "No token supplied - attempting self-registration"
}
$registerBody = $registerPayload | ConvertTo-Json

# Capture body and status separately so a 403 ("needs a token") can be
# distinguished from a genuine failure and explained to the user.
$regTmp = Join-Path $WorkDir "register_response.tmp"
$regBodyFile = Join-Path $WorkDir "register-body.json"

# The payload goes through a file, not the command line. Windows PowerShell
# 5.1 mangles native arguments containing double quotes, which would shred this
# JSON into extra "URLs" and produce a garbage status like 000000000000.
[System.IO.File]::WriteAllText($regBodyFile, $registerBody)

$curlErr = Join-Path $WorkDir "register-curl.err"
# No -L here: registration never redirects, and following one would emit an
# extra %{http_code} per hop.
$regCurl = @("-sS", "-f", "-k")
$regCodeRaw = & curl.exe @regCurl -X POST `
    -H "Content-Type: application/json" `
    --data-binary "@$regBodyFile" `
    -o $regTmp -w "%{http_code}" `
    "$ServerUrl/api/v1/agents/register" 2>$curlErr

# curl writes one 3-digit code per transfer, so the output can be several codes
# run together ("422422"). The last one is the real answer.
$joined = ($regCodeRaw -join "").Trim()
$codeMatches = [regex]::Matches($joined, '\d{3}')
$regCode = if ($codeMatches.Count -gt 0) { $codeMatches[$codeMatches.Count - 1].Value } else { "000" }

Remove-Item $regBodyFile -Force -ErrorAction SilentlyContinue

$registerRaw = ""
if (Test-Path $regTmp) {
    $registerRaw = Get-Content $regTmp -Raw -ErrorAction SilentlyContinue
    Remove-Item $regTmp -Force -ErrorAction SilentlyContinue
}

if ($regCode -eq "403") {
    throw ("This hostname is already registered to Mission Control. Re-installing " +
           "over an existing agent requires a one-time token. Get one from an " +
           "administrator, then re-run with -RegistrationToken <token>. " +
           "Server said: $registerRaw")
}
if ($regCode -eq "400" -and $registerRaw -match "expired") {
    throw "The supplied registration token has expired. Request a new one."
}
if ($regCode -eq "400" -and $registerRaw -match "agent limit") {
    throw "The supplied registration token has already been used. Request a new one."
}
if ($regCode -ne "201") {
    $curlMsg = ""
    if (Test-Path $curlErr) {
        $curlMsg = (Get-Content $curlErr -Raw -ErrorAction SilentlyContinue)
        Remove-Item $curlErr -Force -ErrorAction SilentlyContinue
    }
    Write-Host ""
    Write-Host "      HTTP $regCode from $ServerUrl/api/v1/agents/register" -ForegroundColor Red
    if ($curlMsg) { Write-Host "      curl: $($curlMsg.Trim())" -ForegroundColor DarkGray }
    Write-Host ""
    if ($regCode -eq "000") {
        Write-Host "      The server could not be reached at all (no HTTP response)." -ForegroundColor Yellow
        Write-Host "      Check these on this machine:" -ForegroundColor Yellow
        Write-Host "        1. DNS   : nslookup missioncontrol.optichosting.co.za" -ForegroundColor White
        Write-Host "        2. HTTPS : Test-NetConnection missioncontrol.optichosting.co.za -Port 443" -ForegroundColor White
        Write-Host "        3. Proxy : `$env:HTTPS_PROXY  /  netsh winhttp show proxy" -ForegroundColor White
        Write-Host ""
        Write-Host "      If a proxy is required, set HTTPS_PROXY before running, or add" -ForegroundColor Yellow
        Write-Host "      this server to the proxy bypass list." -ForegroundColor Yellow
    } else {
        Write-Host "      Server said: $registerRaw" -ForegroundColor DarkGray
    }
    Write-Host ""
    throw "Registration failed (HTTP $regCode)."
}

$register = $registerRaw | ConvertFrom-Json
if (-not $register.api_key) {
    throw "Registration response did not contain an API key. Response: $registerRaw"
}
$AgentId = $register.agent_id
Write-Ok "Registered as agent ID $AgentId"

$verifySsl = if ($SkipSslVerify) { "false" } else { "true" }

# Emit a single-quoted YAML scalar. Backslashes are literal inside single
# quotes; inside double quotes YAML treats "\" as an escape, so a path like
# "C:\MissionControlAgent" would either fail to parse (\M is not a valid escape)
# or silently corrupt itself (\r, \t, \n). That crashed the agent on startup.
function ConvertTo-YamlScalar {
    param([string]$Value)
    "'" + ($Value -replace "'", "''") + "'"
}

$config = @"
server_url: $(ConvertTo-YamlScalar $ServerUrl)
verify_ssl: $verifySsl
agent_id: $AgentId
agent_name: $(ConvertTo-YamlScalar $AgentName)
api_key: $($register.api_key)
data_dir: $(ConvertTo-YamlScalar "$WorkDir\data")
config_dir: $(ConvertTo-YamlScalar $WorkDir)
"@
[System.IO.File]::WriteAllText((Join-Path $WorkDir "config.yaml"), $config)
New-Item -Path (Join-Path $WorkDir "data") -ItemType Directory -Force | Out-Null
New-Item -Path (Join-Path $WorkDir "logs") -ItemType Directory -Force | Out-Null
Write-Ok "Wrote config.yaml"

# ---------------------------------------------------------------------------
# 7. Install as a SYSTEM scheduled task
# ---------------------------------------------------------------------------
Write-Step "7/7 Installing scheduled task"
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction `
    -Execute $VenvPython `
    -Argument "-m agent.edge_main --config `"$WorkDir\config.yaml`"" `
    -WorkingDirectory $WorkDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Mission Control Edge Agent" `
    -Force | Out-Null
Write-Ok "Task '$TaskName' registered to start at boot"

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 15

$task = Get-ScheduledTask -TaskName $TaskName
Write-Ok "Task state: $($task.State)"

$logFile = Join-Path $WorkDir "logs\agent.log"
if (Test-Path $logFile) {
    Write-Host ""
    Write-Host "Recent agent log:" -ForegroundColor Cyan
    Get-Content $logFile -Tail 8 -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  $_" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Cyan
Write-Host "  Agent ID : $AgentId" -ForegroundColor Green
Write-Host "  Name     : $AgentName" -ForegroundColor Green
Write-Host "  Log file : $logFile" -ForegroundColor Gray
Write-Host ""
Write-Host "It should appear online in Mission Control within ~30 seconds." -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Gray
Write-Host "  Restart  : Restart-ScheduledTask -TaskName $TaskName" -ForegroundColor White
Write-Host "  Stop     : Stop-ScheduledTask    -TaskName $TaskName" -ForegroundColor White
Write-Host "  Status   : Get-ScheduledTask     -TaskName $TaskName" -ForegroundColor White
Write-Host "  Uninstall: Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false; Remove-Item -Recurse -Force `"$WorkDir`"" -ForegroundColor White
Write-Host ""