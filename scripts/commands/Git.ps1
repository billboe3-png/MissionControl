<#
.SYNOPSIS
Git command module.
#>

Register-McCommand -Name "git" -HandlerFunction "Invoke-McGitCommand" -Description "Provides safe wrappers around common Git commands" -Usage @("mc git status", 'mc git commit "<message>"') -Examples @("mc git status", 'mc git commit "fix bug"') -Options @()

function Invoke-McGitCommand {
    <#
    .SYNOPSIS
    Dispatches Git subcommands.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    Assert-McArgumentCount -Arguments $Context.CommandArguments -Minimum 2 -Usage "mc git <status|commit>"
    $subcommand = [string]$Context.CommandArguments[1].ToLowerInvariant()
    switch ($subcommand) {
        "status" { return Invoke-McGitStatusCommand -Context $Context }
        "commit" { return Invoke-McGitCommitCommand -Context $Context }
        default { throw "Unknown git command '$subcommand'. Run 'mc git --help'." }
    }
}

function Invoke-McGitStatusCommand {
    <#
    .SYNOPSIS
    Returns Git status output.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    Assert-McExecutable -Name "git"
    Assert-McGitRepository -ProjectRoot $Context.ProjectRoot
    $output = Invoke-McNativeCapture -FilePath "git" -CommandArguments @("status", "--short", "--branch") -WorkingDirectory $Context.ProjectRoot

    [pscustomobject]@{
        Type = "Raw"
        Command = "git status"
        Output = $output.Output
        ExitCode = $output.ExitCode
    }
}

function Invoke-McGitCommitCommand {
    <#
    .SYNOPSIS
    Creates a Git commit.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    Assert-McArgumentCount -Arguments $Context.CommandArguments -Minimum 3 -Usage 'mc git commit "<message>"'
    $message = $Context.CommandArguments[2..($Context.CommandArguments.Count - 1)] -join " "
    if ($message.Trim().Length -lt 3) {
        throw "Commit message must be at least 3 characters."
    }

    Assert-McExecutable -Name "git"
    Assert-McGitRepository -ProjectRoot $Context.ProjectRoot
    $output = Invoke-McNativeCapture -FilePath "git" -CommandArguments @("commit", "-m", $message) -WorkingDirectory $Context.ProjectRoot

    [pscustomobject]@{
        Type = "Raw"
        Command = "git commit"
        Output = $output.Output
        ExitCode = $output.ExitCode
    }
}
