<#
.SYNOPSIS
Lint command placeholder module.
#>

Register-McCommand -Name "lint" -HandlerFunction "Invoke-McLintCommand" -Description "Runs linting (reserved for future sprint)" -Usage @("mc lint") -Examples @("mc lint") -Options @()

function Invoke-McLintCommand {
    <#
    .SYNOPSIS
    Returns the lint placeholder result.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    New-McPlaceholderResult -Name "lint"
}
