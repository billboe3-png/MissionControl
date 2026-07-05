<#
.SYNOPSIS
Project initialization command module.
#>

Register-McCommand -Name "init" -HandlerFunction "Invoke-McInitCommand" -Description "Performs idempotent project initialization" -Usage @("mc init") -Examples @("mc init") -Options @()

function Invoke-McInitCommand {
    <#
    .SYNOPSIS
    Performs idempotent project initialization.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    $messages = [System.Collections.Generic.List[object]]::new()
    Write-Progress -Activity "Mission Control init" -Status "Checking project files" -PercentComplete 25

    $envFile = Join-Path $Context.ProjectRoot ".env"
    $envExample = Join-Path $Context.ProjectRoot ".env.example"
    if (-not (Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath $envExample)) {
        Copy-Item -LiteralPath $envExample -Destination $envFile
        $messages.Add([pscustomobject]@{ Level = "SUCCESS"; Message = "Created .env from .env.example." })
    }
    else {
        $messages.Add([pscustomobject]@{ Level = "INFO"; Message = ".env already exists or .env.example is unavailable." })
    }

    Write-Progress -Activity "Mission Control init" -Status "Checking developer folders" -PercentComplete 70
    foreach ($path in @("logs", "scripts/lib", "scripts/commands", "scripts/config", "scripts/templates")) {
        $fullPath = Join-Path $Context.ProjectRoot $path
        if (-not (Test-Path -LiteralPath $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath | Out-Null
            $messages.Add([pscustomobject]@{ Level = "SUCCESS"; Message = "Created $path." })
        }
    }

    Write-Progress -Activity "Mission Control init" -Completed
    $messages.Add([pscustomobject]@{ Level = "SUCCESS"; Message = "Project initialization complete." })

    [pscustomobject]@{
        Type = "Action"
        Command = "init"
        Messages = @($messages)
    }
}
