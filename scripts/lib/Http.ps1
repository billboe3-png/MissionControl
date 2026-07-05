<#
.SYNOPSIS
HTTP helpers for the Mission Control CLI framework.
#>

function Invoke-McHttpStatusCheck {
    <#
    .SYNOPSIS
    Gets HTTP status for a local endpoint.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Path)

    $uri = "http://localhost$Path"
    try {
        $response = Invoke-WebRequest -Uri $uri -Method Get -UseBasicParsing -TimeoutSec 5 -SkipHttpErrorCheck
        return [string]$response.StatusCode
    }
    catch {
        return "unreachable"
    }
}
