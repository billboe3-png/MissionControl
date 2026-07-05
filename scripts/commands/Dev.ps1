<#
.SYNOPSIS
Dev command placeholder module.
#>

Register-McCommand -Name "dev" -HandlerFunction "Invoke-McDevCommand" -Description "Starts development environment (reserved for future sprint)" -Usage @("mc dev") -Examples @("mc dev") -Options @()

function Invoke-McDevCommand {
    <#
    .SYNOPSIS
    Returns the dev placeholder result.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    New-McPlaceholderResult -Name "dev"
}
