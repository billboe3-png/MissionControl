<#
.SYNOPSIS
CLI bootstrap, argument parsing, and dispatch helpers.
#>

function New-McContext {
    <#
    .SYNOPSIS
    Creates a framework context from raw CLI arguments.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $ScriptRoot,

        [string[]] $Arguments = @()
    )

    $parsed = Split-McArguments -Arguments $Arguments
    $projectRoot = Get-McProjectRoot -ScriptRoot $ScriptRoot

    $config = $null
    if (-not [string]::IsNullOrWhiteSpace($parsed.Options.Config)) {
        $config = Load-McConfig -ConfigPath $parsed.Options.Config -ProjectRoot $projectRoot
    }

    $options = Merge-McConfigOptions -Options $parsed.Options -Config $config

    [pscustomobject]@{
        ScriptRoot = $ScriptRoot
        ProjectRoot = $projectRoot
        CommandPath = $parsed.CommandPath
        CommandArguments = $parsed.CommandArguments
        Options = $options
        ConfigPath = $options.Config
        LogFile = $null
    }
}

function Split-McArguments {
    <#
    .SYNOPSIS
    Splits global parameters from command arguments.
    #>
    [CmdletBinding()]
    param([string[]] $Arguments = @())

    $options = [ordered]@{
        Help = $false
        Verbose = $false
        Quiet = $false
        Debug = $false
        Output = "console"
        NoColor = $false
        Log = $false
        Config = $null
        Explicit = [ordered]@{
            Output = $false
            NoColor = $false
            Log = $false
            Config = $false
        }
    }

    $commandArguments = [System.Collections.Generic.List[string]]::new()
    for ($index = 0; $index -lt $Arguments.Count; $index++) {
        $argument = $Arguments[$index]
        switch ($argument) {
            "--help" { $options.Help = $true; continue }
            "--verbose" { $options.Verbose = $true; continue }
            "--quiet" { $options.Quiet = $true; continue }
            "--debug" { $options.Debug = $true; $options.Verbose = $true; continue }
            "--no-color" { $options.NoColor = $true; $options.Explicit.NoColor = $true; continue }
            "--log" { $options.Log = $true; $options.Explicit.Log = $true; continue }
            "--output" {
                $index++
                if ($index -ge $Arguments.Count) {
                    throw "Missing value for --output."
                }
                if ($Arguments[$index] -notin @("console", "json", "json-pretty")) {
                    throw "Unsupported output format '$($Arguments[$index])'."
                }
                $options.Output = $Arguments[$index]
                $options.Explicit.Output = $true
                continue
            }
            "--config" {
                $index++
                if ($index -ge $Arguments.Count) {
                    throw "Missing value for --config."
                }
                $options.Config = $Arguments[$index]
                $options.Explicit.Config = $true
                continue
            }
            default {
                $commandArguments.Add($argument)
            }
        }
    }

    if ($commandArguments.Count -eq 0) {
        $commandArguments.Add("help")
    }

    $commandPath = if ($options.Help -and $commandArguments[0] -ne "help") {
        @("help") + @($commandArguments)
    }
    else {
        @($commandArguments)
    }

    [pscustomobject]@{
        Options = [pscustomobject]$options
        CommandPath = [string[]]$commandPath
        CommandArguments = [string[]]$commandArguments
    }
}

function Invoke-McCommand {
    <#
    .SYNOPSIS
    Dispatches a parsed command context to command modules via registry.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    $command = [string]$Context.CommandPath[0].ToLowerInvariant()
    $handler = Get-McCommandHandler -Name $command

    if ($null -eq $handler) {
        throw "Unknown command '$command'. Run 'mc help'."
    }

    & $handler -Context $Context
}
