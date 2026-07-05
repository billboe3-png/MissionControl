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

function Write-McColorLine {
    <#
    .SYNOPSIS
    Writes one line with optional color.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [pscustomobject] $Context,

        [Parameter(Mandatory)]
        [string] $Message,

        [string] $Color = "White"
    )

    if ($Context.Options.NoColor) {
        Write-Host $Message
    }
    else {
        Write-Host $Message -ForegroundColor $Color
    }
}

function New-McPlaceholderResult {
    <#
    .SYNOPSIS
    Creates a placeholder result for unimplemented commands.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Name)

    [pscustomobject]@{
        Type = "Placeholder"
        Message = "Command '$Name' is reserved for a future sprint."
    }
}

function Invoke-McNativeCapture {
    <#
    .SYNOPSIS
    Runs a native command and returns captured output and exit code.
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
        $output = & $FilePath @CommandArguments 2>&1
        return [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output = ($output -join "`n").Trim()
        }
    }
    finally {
        Pop-Location
    }
}
