<#
.SYNOPSIS
Clean command placeholder module.
#>

Register-McCommand -Name "clean" -HandlerFunction "Invoke-McCleanCommand" -Description "Cleans build artifacts (reserved for future sprint)" -Usage @("mc clean") -Examples @("mc clean") -Options @()

function Invoke-McCleanCommand {
    <#
    .SYNOPSIS
    Returns the clean placeholder result.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    New-McPlaceholderResult -Name "clean"
}
