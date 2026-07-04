<#
.SYNOPSIS
Logging and terminal output helpers for the Mission Control CLI.
#>

$script:McLogFile = $null

function Initialize-McLogging {
    <#
    .SYNOPSIS
    Initializes CLI file logging.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    $logDirectory = Join-Path $ProjectRoot "logs"
    if (-not (Test-Path -LiteralPath $logDirectory)) {
        New-Item -ItemType Directory -Path $logDirectory | Out-Null
    }

    $script:McLogFile = Join-Path $logDirectory "mc.log"
}

function Write-McLog {
    <#
    .SYNOPSIS
    Writes a timestamped log line.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet("INFO", "WARN", "ERROR", "SUCCESS")]
        [string] $Level,

        [Parameter(Mandatory)]
        [string] $Message
    )

    $color = switch ($Level) {
        "INFO" { "Cyan" }
        "WARN" { "Yellow" }
        "ERROR" { "Red" }
        "SUCCESS" { "Green" }
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] [$Level] $Message"
    Write-Host $line -ForegroundColor $color

    if ($script:McLogFile) {
        Add-Content -LiteralPath $script:McLogFile -Value $line
    }
}

function Write-McInfo {
    <#
    .SYNOPSIS
    Writes an informational message.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Message)
    Write-McLog -Level INFO -Message $Message
}

function Write-McSuccess {
    <#
    .SYNOPSIS
    Writes a success message.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Message)
    Write-McLog -Level SUCCESS -Message $Message
}

function Write-McWarning {
    <#
    .SYNOPSIS
    Writes a warning message.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Message)
    Write-McLog -Level WARN -Message $Message
}

function Write-McError {
    <#
    .SYNOPSIS
    Writes an error message.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Message)
    Write-McLog -Level ERROR -Message $Message
}
