<#
.SYNOPSIS
Version command module.
#>

Register-McCommand -Name "version" -HandlerFunction "Invoke-McVersionCommand" -Description "Shows CLI version" -Usage @("mc version") -Examples @("mc version") -Options @()

function Invoke-McVersionCommand {
    <#
    .SYNOPSIS
    Returns CLI version.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    $version = Get-McCliVersion
    [pscustomobject]@{
        Type = "Version"
        Version = $version
        Message = "Mission Control CLI $version"
    }
}
