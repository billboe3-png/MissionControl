<#
.SYNOPSIS
Mission Control developer CLI.

.DESCRIPTION
Dispatches Mission Control developer commands to library modules. Requires
PowerShell 7 or later.

.EXAMPLE
./scripts/mc.ps1 status

.EXAMPLE
./scripts/mc.ps1 docker up
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
@(
    "Logging.ps1",
    "Validation.ps1",
    "Helpers.ps1",
    "Docker.ps1",
    "Git.ps1",
    "Doctor.ps1",
    "Project.ps1"
) | ForEach-Object {
    . (Join-Path $libPath $_)
}

function Invoke-McCommand {
    <#
    .SYNOPSIS
    Dispatches parsed CLI arguments to command handlers.
    #>
    [CmdletBinding()]
    param(
        [string[]] $CommandArguments
    )

    $root = Get-McProjectRoot -ScriptRoot $PSScriptRoot
    Initialize-McLogging -ProjectRoot $root
    $command = if ($CommandArguments.Count -gt 0) { $CommandArguments[0] } else { "help" }
    $scope = if ($CommandArguments.Count -gt 1) { $CommandArguments[1] } else { $null }

    try {
        switch ($command.ToLowerInvariant()) {
            "help" { Show-McHelp; break }
            "version" { Show-McVersion; break }
            "status" { Show-McStatus -ProjectRoot $root; break }
            "doctor" { Invoke-McDoctor -ProjectRoot $root; break }
            "init" { Initialize-McProject -ProjectRoot $root; break }
            "docker" {
                Assert-McArgumentCount -Arguments $CommandArguments -Minimum 2 -Usage "mc docker <up|down|logs>"
                switch ($scope.ToLowerInvariant()) {
                    "up" { Invoke-McDockerUp -ProjectRoot $root; break }
                    "down" { Invoke-McDockerDown -ProjectRoot $root; break }
                    "logs" { Invoke-McDockerLogs -ProjectRoot $root; break }
                    default { throw "Unknown docker command '$scope'. Run 'mc help'." }
                }
                break
            }
            "git" {
                Assert-McArgumentCount -Arguments $CommandArguments -Minimum 2 -Usage "mc git <status|commit>"
                switch ($scope.ToLowerInvariant()) {
                    "status" { Invoke-McGitStatus -ProjectRoot $root; break }
                    "commit" {
                        Assert-McArgumentCount -Arguments $CommandArguments -Minimum 3 -Usage 'mc git commit "<message>"'
                        Invoke-McGitCommit -ProjectRoot $root -Message ($CommandArguments[2..($CommandArguments.Count - 1)] -join " ")
                        break
                    }
                    default { throw "Unknown git command '$scope'. Run 'mc help'." }
                }
                break
            }
            "sprint" { Invoke-McPlaceholder -Name "sprint"; break }
            "build" { Invoke-McPlaceholder -Name "build"; break }
            "clean" { Invoke-McPlaceholder -Name "clean"; break }
            "lint" { Invoke-McPlaceholder -Name "lint"; break }
            "test" { Invoke-McPlaceholder -Name "test"; break }
            default { throw "Unknown command '$command'. Run 'mc help'." }
        }
    }
    catch {
        Write-McError $_.Exception.Message
        exit 1
    }
}

Invoke-McCommand -CommandArguments $Arguments
