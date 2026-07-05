<#
.SYNOPSIS
Sprint command placeholder module.
#>

Register-McCommand -Name "sprint" -HandlerFunction "Invoke-McSprintCommand" -Description "Manages sprints (reserved for future sprint)" -Usage @("mc sprint create <number>") -Examples @("mc sprint create 12") -Options @()

function Invoke-McSprintCommand {
    <#
    .SYNOPSIS
    Returns the sprint placeholder result.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    New-McPlaceholderResult -Name "sprint"
}
