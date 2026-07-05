<#
.SYNOPSIS
Build command placeholder module.
#>

Register-McCommand -Name "build" -HandlerFunction "Invoke-McBuildCommand" -Description "Builds the project (reserved for future sprint)" -Usage @("mc build") -Examples @("mc build") -Options @()

function Invoke-McBuildCommand {
    <#
    .SYNOPSIS
    Returns the build placeholder result.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    New-McPlaceholderResult -Name "build"
}
