<#
.SYNOPSIS
Shared output engine for Mission Control CLI command results.
#>

function Write-McOutput {
    <#
    .SYNOPSIS
    Renders a command result using the selected output format.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [pscustomobject] $Context,

        [Parameter()]
        $InputObject
    )

    if ($Context.Options.Output -eq "json") {
        $InputObject | ConvertTo-Json -Depth 10 -Compress
        return
    }

    if ($Context.Options.Output -eq "json-pretty") {
        $InputObject | ConvertTo-Json -Depth 10
        return
    }

    Write-McConsoleOutput -Context $Context -InputObject $InputObject
}

function Write-McConsoleOutput {
    <#
    .SYNOPSIS
    Renders command results to the console.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [pscustomobject] $Context,

        [Parameter()]
        $InputObject
    )

    if ($Context.Options.Quiet -and $InputObject.Type -notin @("Error", "Raw")) {
        return
    }

    switch ($InputObject.Type) {
        "Help" { Write-McHelpOutput -Context $Context -Result $InputObject }
        "Status" { Write-McStatusOutput -Context $Context -Result $InputObject }
        "Version" { Write-McColorLine -Context $Context -Message $InputObject.Message -Color Green }
        "Doctor" { Write-McDoctorOutput -Context $Context -Result $InputObject }
        "Action" { Write-McActionOutput -Context $Context -Result $InputObject }
        "Placeholder" { Write-McColorLine -Context $Context -Message $InputObject.Message -Color Yellow }
        "Raw" { Write-Host $InputObject.Output }
        "Error" { Write-McColorLine -Context $Context -Message "[ERROR] $($InputObject.Error)" -Color Red }
        default { $InputObject | Format-List }
    }
}

function Write-McHelpOutput {
    <#
    .SYNOPSIS
    Renders help output.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][pscustomobject] $Context,
        [Parameter(Mandatory)][pscustomobject] $Result
    )

    Write-McColorLine -Context $Context -Message $Result.Title -Color Green
    Write-Host ""
    foreach ($section in $Result.Sections) {
        Write-McColorLine -Context $Context -Message $section.Title -Color $section.Color
        foreach ($line in $section.Lines) {
            Write-Host $line
        }
        Write-Host ""
    }
}

function Write-McStatusOutput {
    <#
    .SYNOPSIS
    Renders status output.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][pscustomobject] $Context,
        [Parameter(Mandatory)][pscustomobject] $Result
    )

    Write-McColorLine -Context $Context -Message "Mission Control Status" -Color Green
    foreach ($item in $Result.Items) {
        Write-Host "$($item.Name): $($item.Value)"
    }
}

function Write-McDoctorOutput {
    <#
    .SYNOPSIS
    Renders doctor report output.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][pscustomobject] $Context,
        [Parameter(Mandatory)][pscustomobject] $Result
    )

    Write-McColorLine -Context $Context -Message "Mission Control Doctor" -Color Green
    Write-Host ""
    foreach ($section in $Result.Sections) {
        Write-McColorLine -Context $Context -Message $section.Name -Color Cyan
        foreach ($check in $section.Checks) {
            $color = switch ($check.Level) {
                "Pass" { "Green" }
                "Warn" { "Yellow" }
                "Fail" { "Red" }
            }
            $marker = switch ($check.Level) {
                "Pass" { "[OK]" }
                "Warn" { "[WARN]" }
                "Fail" { "[FAIL]" }
            }
            Write-McColorLine -Context $Context -Message ("  {0,-6} {1,-32} {2}" -f $marker, $check.Name, $check.Message) -Color $color
        }
        Write-Host ""
    }

    $statusColor = switch ($Result.OverallStatus) {
        "READY" { "Green" }
        "WARNING" { "Yellow" }
        "FAILED" { "Red" }
    }
    Write-McColorLine -Context $Context -Message "Overall Status: $($Result.OverallStatus)" -Color $statusColor
}

function Write-McActionOutput {
    <#
    .SYNOPSIS
    Renders action command output.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][pscustomobject] $Context,
        [Parameter(Mandatory)][pscustomobject] $Result
    )

    foreach ($line in $Result.Messages) {
        $color = if ($line.Level -eq "SUCCESS") { "Green" } elseif ($line.Level -eq "WARN") { "Yellow" } else { "Cyan" }
        Write-McColorLine -Context $Context -Message $line.Message -Color $color
    }
    if ($Result.Output) {
        Write-Host $Result.Output
    }
}
