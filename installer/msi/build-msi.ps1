<#
.SYNOPSIS
    Build the Mission Control Edge Agent Windows MSI (WiX v3.14).

.DESCRIPTION
    Downloads a portable WiX v3.14 (candle/light + util extension) into a local
    cache under the user profile — no .NET SDK or WiX install required — then
    compiles installer/msi/agent.wxs and produces the MSI.

    The MSI is a thin wrapper: it ships install-agent.ps1 / uninstall-agent.ps1
    and downloads the latest agent bundle from the server at install time.

.USAGE
    .\build-msi.ps1                 # produces output\MissionControlEdgeAgent-3.0.0-rc1.msi
    .\build-msi.ps1 -OutName MissionControlEdgeAgent-3.0.0-rc1
#>
[CmdletBinding()]
param(
    [string]$OutName = "MissionControlEdgeAgent-3.0.0-rc1"
)

$ErrorActionPreference = "Stop"

$Root     = $PSScriptRoot
$BuildDir = Join-Path $Root "build"
$OutDir   = Join-Path $Root "output"
$CacheDir = Join-Path $env:USERPROFILE ".cache\wix314"
$WixBin   = Join-Path $CacheDir "candle.exe"
$UtilExt  = Join-Path $CacheDir "WixUtilExtension.dll"
$UiExt    = Join-Path $CacheDir "WixUIExtension.dll"

New-Item -ItemType Directory -Force -Path $CacheDir, $BuildDir, $OutDir | Out-Null

# ---- 1. Provision portable WiX v3.14 --------------------------------------
if (-not (Test-Path $WixBin)) {
    $zip = Join-Path $CacheDir "wix314-binaries.zip"
    $url = "https://github.com/wixtoolset/wix3/releases/download/wix3141rtm/wix314-binaries.zip"
    $urlAlt = $url -replace "wix3141rtm", "wix314rtm"
    Write-Host "[*] Downloading WiX v3.14 (no .NET SDK needed)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    try {
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    } catch {
        Write-Host "[!] Primary URL failed; trying alternate release tag..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $urlAlt -OutFile $zip -UseBasicParsing
    }
    Expand-Archive -Path $zip -DestinationPath $CacheDir -Force
    if (-not (Test-Path $WixBin)) { throw "WiX binaries missing after download: $CacheDir" }
}
Write-Host "[*] Using WiX: $CacheDir"

# ---- 2. Compile + link ------------------------------------------------
Push-Location $Root
try {
    Write-Host "[*] candle agent.wxs ..."
    & $CacheDir\candle.exe agent.wxs -ext $UtilExt -o (Join-Path $BuildDir "agent.wixobj")
    if ($LASTEXITCODE -ne 0) { throw "candle failed with exit code $LASTEXITCODE" }

    $msi = Join-Path $OutDir "$OutName.msi"
    if (Test-Path $msi) { Remove-Item $msi -Force }
    Write-Host "[*] light (linking) ..."
    & $CacheDir\light.exe (Join-Path $BuildDir "agent.wixobj") -ext $UtilExt -ext $UiExt -o $msi
    if ($LASTEXITCODE -ne 0) { throw "light failed with exit code $LASTEXITCODE" }

    $size = (Get-Item $msi).Length
    Write-Host ""
    Write-Host "[+] MSI built: $msi ($size bytes)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Silent install:  msiexec /i `"$msi`" /qn SERVERURL=https://missioncontrol.optichosting.co.za AGENTNAME=PC-01" -ForegroundColor Cyan
    Write-Host "  Silent uninstall: msiexec /x `"$msi`" /qn" -ForegroundColor Cyan
} finally {
    Pop-Location
}