<#
.SYNOPSIS
Docker Compose commands for the Mission Control CLI.
#>

function Get-McDockerComposeCommand {
    <#
    .SYNOPSIS
    Finds the Docker Compose command available on this workstation.
    #>
    [CmdletBinding()]
    param()

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        & docker compose version *> $null
        if ($LASTEXITCODE -eq 0) {
            return @{ FilePath = "docker"; Arguments = @("compose") }
        }
    }

    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        return @{ FilePath = "docker-compose"; Arguments = @() }
    }

    throw "Docker Compose was not found. Install Docker Compose v2 or docker-compose."
}

function Invoke-McDockerCompose {
    <#
    .SYNOPSIS
    Runs Docker Compose with common project settings.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $ProjectRoot,

        [Parameter(Mandatory)]
        [string[]] $ComposeArguments
    )

    $compose = Get-McDockerComposeCommand
    Invoke-McNativeCommand `
        -FilePath $compose.FilePath `
        -CommandArguments ($compose.Arguments + $ComposeArguments) `
        -WorkingDirectory $ProjectRoot
}

function Invoke-McDockerComposeCapture {
    <#
    .SYNOPSIS
    Runs Docker Compose and captures output and exit code.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $ProjectRoot,

        [Parameter(Mandatory)]
        [string[]] $ComposeArguments
    )

    $compose = Get-McDockerComposeCommand
    Invoke-McNativeCapture `
        -FilePath $compose.FilePath `
        -CommandArguments ($compose.Arguments + $ComposeArguments) `
        -WorkingDirectory $ProjectRoot
}

function Get-McDockerComposeStatus {
    <#
    .SYNOPSIS
    Returns a short Docker Compose availability status.
    #>
    [CmdletBinding()]
    param()

    try {
        $compose = Get-McDockerComposeCommand
        return "$($compose.FilePath) available"
    }
    catch {
        return "missing"
    }
}

