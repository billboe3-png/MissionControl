<#
.SYNOPSIS
Command registry for the Mission Control CLI framework.
#>

$script:CommandRegistry = @{}

function Register-McCommand {
    <#
    .SYNOPSIS
    Registers a command with the CLI framework.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Name,

        [Parameter(Mandatory)]
        [string] $HandlerFunction,

        [string] $Description = "",

        [string[]] $Usage = @(),

        [string[]] $Examples = @(),

        [string[]] $Options = @()
    )

    $script:CommandRegistry[$Name.ToLowerInvariant()] = [pscustomobject]@{
        HandlerFunction = $HandlerFunction
        Description = $Description
        Usage = $Usage
        Examples = $Examples
        Options = $Options
    }
}

function Get-McCommandHandler {
    <#
    .SYNOPSIS
    Retrieves a command handler function name by command name.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Name
    )

    $key = $Name.ToLowerInvariant()
    if ($script:CommandRegistry.ContainsKey($key)) {
        return $script:CommandRegistry[$key].HandlerFunction
    }
    return $null
}

function Get-McRegisteredCommands {
    <#
    .SYNOPSIS
    Returns all registered command names.
    #>
    [CmdletBinding()]
    param()

    return $script:CommandRegistry.Keys | Sort-Object
}

function Get-McCommandMetadata {
    <#
    .SYNOPSIS
    Retrieves full command metadata by command name.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Name
    )

    $key = $Name.ToLowerInvariant()
    if ($script:CommandRegistry.ContainsKey($key)) {
        return $script:CommandRegistry[$key]
    }
    return $null
}
