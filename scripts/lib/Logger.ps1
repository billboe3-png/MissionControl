<#
.SYNOPSIS
Shared logger for the Mission Control CLI framework.
#>

function Initialize-McLogger {
    <#
    .SYNOPSIS
    Initializes logging for a command context.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    $logDirectory = Join-Path $Context.ProjectRoot "logs"
    if (-not (Test-Path -LiteralPath $logDirectory)) {
        New-Item -ItemType Directory -Path $logDirectory | Out-Null
    }

    $Context.LogFile = Join-Path $logDirectory "mc.log"
}

function Write-McLog {
    <#
    .SYNOPSIS
    Writes a timestamped log entry to file and optionally console.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [pscustomobject] $Context,

        [Parameter(Mandatory)]
        [ValidateSet("INFO", "WARN", "ERROR", "DEBUG", "SUCCESS")]
        [string] $Level,

        [Parameter(Mandatory)]
        [string] $Message
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] [$Level] $Message"

    if ($Context.Options.Log -or $Level -in @("ERROR", "DEBUG")) {
        Add-Content -LiteralPath $Context.LogFile -Value $line
    }

    if (-not $Context.Options.Quiet -and ($Context.Options.Verbose -or $Level -in @("ERROR", "DEBUG"))) {
        $color = switch ($Level) {
            "INFO" { "Cyan" }
            "WARN" { "Yellow" }
            "ERROR" { "Red" }
            "DEBUG" { "DarkGray" }
            "SUCCESS" { "Green" }
        }
        Write-McColorLine -Context $Context -Message $line -Color $color
    }
}
