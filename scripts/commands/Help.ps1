<#
.SYNOPSIS
Help command module.
#>

Register-McCommand -Name "help" -HandlerFunction "Invoke-McHelpCommand" -Description "Shows help for CLI commands" -Usage @("mc help", "mc help <command>") -Examples @("mc help", "mc help doctor") -Options @()

function Invoke-McHelpCommand {
    <#
    .SYNOPSIS
    Returns generated CLI help from command metadata.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    $topic = if ($Context.CommandPath.Count -gt 1) { $Context.CommandPath[1] } else { "root" }
    $sections = if ($topic -eq "root") {
        $commands = Get-McRegisteredCommands
        $commandLines = $commands | ForEach-Object {
            $metadata = Get-McCommandMetadata -Name $_
            $description = if ($metadata) { $metadata.Description } else { "" }
            "  mc $_  -  $description"
        }
        
        @(
            [pscustomobject]@{ Title = "Available commands:"; Color = "Cyan"; Lines = $commandLines },
            [pscustomobject]@{ Title = "Global parameters:"; Color = "Cyan"; Lines = @(
                "  --help",
                "  --verbose",
                "  --quiet",
                "  --debug",
                "  --output console|json|json-pretty",
                "  --no-color",
                "  --log",
                "  --config <path>"
            ) },
            [pscustomobject]@{ Title = "Usage:"; Color = "Cyan"; Lines = @(
                "  mc help",
                "  mc help <command>"
            ) }
        )
    }
    else {
        $metadata = Get-McCommandMetadata -Name $topic
        if ($null -eq $metadata) {
            throw "Unknown command '$topic'. Run 'mc help' to see available commands."
        }

        @(
            [pscustomobject]@{ Title = "Description:"; Color = "Cyan"; Lines = @("  $($metadata.Description)") }
            [pscustomobject]@{ Title = "Usage:"; Color = "Cyan"; Lines = ($metadata.Usage | ForEach-Object { "  $_" }) }
            if ($metadata.Examples.Count -gt 0) {
                [pscustomobject]@{ Title = "Examples:"; Color = "Cyan"; Lines = ($metadata.Examples | ForEach-Object { "  $_" }) }
            }
            if ($metadata.Options.Count -gt 0) {
                [pscustomobject]@{ Title = "Options:"; Color = "Cyan"; Lines = ($metadata.Options | ForEach-Object { "  $_" }) }
            }
        )
    }

    [pscustomobject]@{
        Type = "Help"
        Topic = $topic
        Title = "Mission Control Developer CLI"
        Sections = $sections
    }
}