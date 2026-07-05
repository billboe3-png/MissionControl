<#
.SYNOPSIS
Status command module.
#>

Register-McCommand -Name "status" -HandlerFunction "Invoke-McStatusCommand" -Description "Shows local developer environment status" -Usage @("mc status") -Examples @("mc status") -Options @()

function Invoke-McStatusCommand {
    <#
    .SYNOPSIS
    Returns local developer environment status.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    [pscustomobject]@{
        Type = "Status"
        Items = @(
            [pscustomobject]@{ Name = "Project root"; Value = $Context.ProjectRoot },
            [pscustomobject]@{ Name = "PowerShell"; Value = $PSVersionTable.PSVersion.ToString() },
            [pscustomobject]@{ Name = ".env"; Value = $(if (Test-Path -LiteralPath (Join-Path $Context.ProjectRoot ".env")) { "present" } else { "missing" }) },
            [pscustomobject]@{ Name = "Docker Compose"; Value = Get-McDockerComposeStatus },
            [pscustomobject]@{ Name = "Git"; Value = $(if (Get-Command git -ErrorAction SilentlyContinue) { "available" } else { "missing" }) }
        )
    }
}