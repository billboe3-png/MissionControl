<#
.SYNOPSIS
Configuration loader for Mission Control CLI.
#>

function Get-McConfigDefaults {
    <#
    .SYNOPSIS
    Returns built-in default CLI option values.
    #>
    return [pscustomobject]@{
        output = "console"
        log = $false
        noColor = $false
    }
}

function Resolve-McConfigPath {
    <#
    .SYNOPSIS
    Resolves a configuration path relative to project root when needed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string] $ConfigPath,
        [Parameter(Mandatory)][string] $ProjectRoot
    )

    if ([System.IO.Path]::IsPathRooted($ConfigPath)) {
        return $ConfigPath
    }

    return Join-Path $ProjectRoot $ConfigPath
}

function Validate-McConfig {
    <#
    .SYNOPSIS
    Validates supported configuration properties.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)] $Config)

    $supportedKeys = @("output", "log", "nocolor")

    foreach ($property in $Config.PSObject.Properties) {
        $name = $property.Name
        $normalized = $name.ToLowerInvariant()

        if ($normalized -notin $supportedKeys) {
            throw "Invalid configuration key '$name'. Supported options are: output, log, noColor."
        }

        switch ($normalized) {
            "output" {
                if ($property.Value -isnot [string] -or $property.Value -notin @("console", "json", "json-pretty")) {
                    throw "Invalid configuration value for 'output': '$($property.Value)'. Expected one of console, json, json-pretty."
                }
            }
            "log" {
                if ($property.Value -isnot [bool]) {
                    throw "Invalid configuration value for 'log': must be true or false."
                }
            }
            "nocolor" {
                if ($property.Value -isnot [bool]) {
                    throw "Invalid configuration value for 'noColor': must be true or false."
                }
            }
        }
    }
}

function Load-McConfig {
    <#
    .SYNOPSIS
    Loads and validates a JSON configuration file.
    #>
    [CmdletBinding()]
    param(
        [Parameter()][string] $ConfigPath,
        [Parameter(Mandatory)][string] $ProjectRoot
    )

    if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
        return $null
    }

    $resolvedPath = Resolve-McConfigPath -ConfigPath $ConfigPath -ProjectRoot $ProjectRoot
    if (-not (Test-Path -LiteralPath $resolvedPath)) {
        throw "Configuration file not found: $resolvedPath"
    }

    try {
        $text = Get-Content -LiteralPath $resolvedPath -Raw
        $config = $text | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Invalid JSON in configuration file '$resolvedPath': $($_.Exception.Message)"
    }

    if ($null -eq $config) {
        throw "Configuration file '$resolvedPath' is empty or invalid."
    }

    Validate-McConfig -Config $config
    return $config
}

function Merge-McConfigOptions {
    <#
    .SYNOPSIS
    Merges configuration values into CLI options using CLI precedence.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][pscustomobject] $Options,
        [Parameter()] $Config
    )

    if ($null -eq $Config) {
        return $Options
    }

    $merged = [ordered]@{
        Help = $Options.Help
        Verbose = $Options.Verbose
        Quiet = $Options.Quiet
        Debug = $Options.Debug
        Output = $Options.Output
        NoColor = $Options.NoColor
        Log = $Options.Log
        Config = $Options.Config
        Explicit = $Options.Explicit
    }

    $propertyNames = $Config.PSObject.Properties.Name | ForEach-Object { $_.ToLowerInvariant() }

    if (-not $Options.Explicit.Output -and $propertyNames -contains "output") {
        $merged.Output = $Config.output
    }

    if (-not $Options.Explicit.Log -and $propertyNames -contains "log") {
        $merged.Log = $Config.log
    }

    if (-not $Options.Explicit.NoColor -and $propertyNames -contains "nocolor") {
        $merged.NoColor = $Config.noColor
    }

    return [pscustomobject]$merged
}
