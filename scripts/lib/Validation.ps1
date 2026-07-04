<#
.SYNOPSIS
Validation helpers for the Mission Control CLI.
#>

function Assert-McArgumentCount {
    <#
    .SYNOPSIS
    Validates a minimum CLI argument count.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string[]] $Arguments,

        [Parameter(Mandatory)]
        [int] $Minimum,

        [Parameter(Mandatory)]
        [string] $Usage
    )

    if ($Arguments.Count -lt $Minimum) {
        throw "Invalid arguments. Usage: $Usage"
    }
}

function Assert-McExecutable {
    <#
    .SYNOPSIS
    Ensures a command is available on PATH.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required executable '$Name' was not found on PATH."
    }
}

function Assert-McGitRepository {
    <#
    .SYNOPSIS
    Ensures the current project root is a Git repository.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot ".git"))) {
        throw "Project root is not a Git repository: $ProjectRoot"
    }
}
