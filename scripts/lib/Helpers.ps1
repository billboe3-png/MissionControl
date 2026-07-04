<#
.SYNOPSIS
Shared helper functions for the Mission Control CLI.
#>

function Get-McProjectRoot {
    <#
    .SYNOPSIS
    Resolves the repository root from the scripts directory.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ScriptRoot)

    return (Resolve-Path -LiteralPath (Join-Path $ScriptRoot "..")).Path
}

function Invoke-McNativeCommand {
    <#
    .SYNOPSIS
    Runs a native command and fails on non-zero exit code.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FilePath,

        [string[]] $CommandArguments = @(),

        [Parameter(Mandatory)]
        [string] $WorkingDirectory
    )

    Push-Location -LiteralPath $WorkingDirectory
    try {
        & $FilePath @CommandArguments
        if ($LASTEXITCODE -ne 0) {
            throw "'$FilePath $($CommandArguments -join " ")' failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-McPlaceholder {
    <#
    .SYNOPSIS
    Reports an intentionally unimplemented command.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Name)

    Write-McWarning "Command '$Name' is reserved for a future sprint."
}
