<#
.SYNOPSIS
Test command placeholder module.
#>

Register-McCommand -Name "test" -HandlerFunction "Invoke-McTestCommand" -Description "Runs tests (reserved for future sprint)" -Usage @("mc test") -Examples @("mc test") -Options @()

function Invoke-McTestCommand {
    <#
    .SYNOPSIS
    Returns the test placeholder result.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    New-McPlaceholderResult -Name "test"
}
