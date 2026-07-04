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

function Invoke-McDockerUp {
    <#
    .SYNOPSIS
    Builds and starts the Mission Control Docker stack.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    Write-Progress -Activity "Mission Control Docker" -Status "Building and starting services" -PercentComplete 15
    Write-McInfo "Starting Docker stack."
    Invoke-McDockerCompose -ProjectRoot $ProjectRoot -ComposeArguments @("up", "--build", "-d")
    Write-Progress -Activity "Mission Control Docker" -Completed
    Write-McSuccess "Docker stack is running."
}

function Invoke-McDockerDown {
    <#
    .SYNOPSIS
    Stops the Mission Control Docker stack.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    Write-Progress -Activity "Mission Control Docker" -Status "Stopping services" -PercentComplete 50
    Write-McInfo "Stopping Docker stack."
    Invoke-McDockerCompose -ProjectRoot $ProjectRoot -ComposeArguments @("down")
    Write-Progress -Activity "Mission Control Docker" -Completed
    Write-McSuccess "Docker stack stopped."
}

function Invoke-McDockerLogs {
    <#
    .SYNOPSIS
    Shows Docker Compose logs.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    Invoke-McDockerCompose -ProjectRoot $ProjectRoot -ComposeArguments @("logs", "--tail", "200")
}
