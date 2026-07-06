<#
.SYNOPSIS
Docker command module.
#>

Register-McCommand -Name "docker" -HandlerFunction "Invoke-McDockerCommand" -Description "Manages the Mission Control Docker Compose stack" -Usage @("mc docker up", "mc docker down", "mc docker logs") -Examples @("mc docker up", "mc docker down", "mc docker logs") -Options @()

function Invoke-McDockerCommand {
    <#
    .SYNOPSIS
    Dispatches Docker subcommands.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    Assert-McValidSubcommand -Context $Context -AllowedSubcommands @("up", "down", "logs")
    $subcommand = [string]$Context.CommandArguments[1].ToLowerInvariant()
    switch ($subcommand) {
        "up" { return Invoke-McDockerUpCommand -Context $Context }
        "down" { return Invoke-McDockerDownCommand -Context $Context }
        "logs" { return Invoke-McDockerLogsCommand -Context $Context }
    }
}

function Invoke-McDockerUpCommand {
    <#
    .SYNOPSIS
    Builds and starts the Docker stack.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    Write-Progress -Activity "Mission Control Docker" -Status "Building and starting services" -PercentComplete 15
    $output = Invoke-McDockerComposeCapture -ProjectRoot $Context.ProjectRoot -ComposeArguments @("up", "--build", "-d")
    Write-Progress -Activity "Mission Control Docker" -Completed

    [pscustomobject]@{
        Type = "Action"
        Command = "docker up"
        Messages = @(
            [pscustomobject]@{ Level = "INFO"; Message = "Starting Docker stack." },
            [pscustomobject]@{ Level = "SUCCESS"; Message = "Docker stack is running." }
        )
        Output = $output.Output
        ExitCode = $output.ExitCode
    }
}

function Invoke-McDockerDownCommand {
    <#
    .SYNOPSIS
    Stops the Docker stack.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    Write-Progress -Activity "Mission Control Docker" -Status "Stopping services" -PercentComplete 50
    $output = Invoke-McDockerComposeCapture -ProjectRoot $Context.ProjectRoot -ComposeArguments @("down")
    Write-Progress -Activity "Mission Control Docker" -Completed

    [pscustomobject]@{
        Type = "Action"
        Command = "docker down"
        Messages = @(
            [pscustomobject]@{ Level = "INFO"; Message = "Stopping Docker stack." },
            [pscustomobject]@{ Level = "SUCCESS"; Message = "Docker stack stopped." }
        )
        Output = $output.Output
        ExitCode = $output.ExitCode
    }
}

function Invoke-McDockerLogsCommand {
    <#
    .SYNOPSIS
    Returns Docker stack logs.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    $output = Invoke-McDockerComposeCapture -ProjectRoot $Context.ProjectRoot -ComposeArguments @("logs", "--tail", "200")
    [pscustomobject]@{
        Type = "Raw"
        Command = "docker logs"
        Output = $output.Output
        ExitCode = $output.ExitCode
    }
}
