<#
.SYNOPSIS
Git commands for the Mission Control CLI.
#>

function Invoke-McGitStatus {
    <#
    .SYNOPSIS
    Displays repository status.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    Assert-McExecutable -Name "git"
    Assert-McGitRepository -ProjectRoot $ProjectRoot
    Invoke-McNativeCommand -FilePath "git" -CommandArguments @("status", "--short", "--branch") -WorkingDirectory $ProjectRoot
}

function Invoke-McGitCommit {
    <#
    .SYNOPSIS
    Creates a Git commit with the supplied message.
    #>
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)]
        [string] $ProjectRoot,

        [Parameter(Mandatory)]
        [ValidateNotNullOrEmpty()]
        [string] $Message
    )

    Assert-McExecutable -Name "git"
    Assert-McGitRepository -ProjectRoot $ProjectRoot

    if ($Message.Trim().Length -lt 3) {
        throw "Commit message must be at least 3 characters."
    }

    if ($PSCmdlet.ShouldProcess($ProjectRoot, "Create Git commit")) {
        Invoke-McNativeCommand -FilePath "git" -CommandArguments @("commit", "-m", $Message) -WorkingDirectory $ProjectRoot
    }
}
