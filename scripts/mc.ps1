<#
.SYNOPSIS
Mission Control developer CLI.

.DESCRIPTION
Loads the Mission Control CLI framework, parses arguments, dispatches commands,
and renders command results. Requires PowerShell 7 or later.

.EXAMPLE
./scripts/mc.ps1 status

.EXAMPLE
./scripts/mc.ps1 doctor --output json-pretty
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "Mission Control CLI requires PowerShell 7 or later."
}

$libPath = Join-Path $PSScriptRoot "lib"
$commandPath = Join-Path $PSScriptRoot "commands"

foreach ($libFile in @(
    "Registry.ps1",
    "Bootstrap.ps1",
    "Config.ps1",
    "Output.ps1",
    "Logger.ps1",
    "Validation.ps1",
    "Helpers.ps1",
    "Docker.ps1",
    "Git.ps1",
    "Http.ps1",
    "Doctor.ps1",
    "Version.ps1"
)) {
    . (Join-Path $libPath $libFile)
}

foreach ($commandFile in (Get-ChildItem -LiteralPath $commandPath -Filter "*.ps1" | Sort-Object Name)) {
    . $commandFile.FullName
}

$context = $null
try {
    $context = New-McContext -ScriptRoot $PSScriptRoot -Arguments $Arguments
    Initialize-McLogger -Context $context

    if ($context.Options.Debug) {
        Write-McLog -Context $context -Level DEBUG -Message "Dispatching command: $($context.CommandPath -join ' ')"
    }

    $result = Invoke-McCommand -Context $context
    Write-McOutput -Context $context -InputObject $result
}
catch {
    $message = $_.Exception.Message
    if ($null -ne $context) {
        Write-McLog -Context $context -Level ERROR -Message $message
        Write-McOutput -Context $context -InputObject ([pscustomobject]@{
            Type = "Error"
            Error = $message
        })
    }
    else {
        Write-Host "[ERROR] $message" -ForegroundColor Red
    }
    exit 1
}