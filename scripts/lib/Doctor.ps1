<#
.SYNOPSIS
Doctor checks for the Mission Control developer CLI.
#>

function New-McDoctorResult {
    <#
    .SYNOPSIS
    Creates a normalized doctor result.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $Name,

        [Parameter(Mandatory)]
        [ValidateSet("Pass", "Warn", "Fail")]
        [string] $Level,

        [Parameter(Mandatory)]
        [string] $Message
    )

    [pscustomobject]@{
        Name = $Name
        Level = $Level
        Message = $Message
    }
}

function Write-McDoctorResult {
    <#
    .SYNOPSIS
    Writes a colored doctor result line.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Result)

    $color = switch ($Result.Level) {
        "Pass" { "Green" }
        "Warn" { "Yellow" }
        "Fail" { "Red" }
    }
    $marker = switch ($Result.Level) {
        "Pass" { "[OK]" }
        "Warn" { "[WARN]" }
        "Fail" { "[FAIL]" }
    }

    Write-Host ("  {0,-6} {1,-32} {2}" -f $marker, $Result.Name, $Result.Message) -ForegroundColor $color
}


function Test-McCommand {
    <#
    .SYNOPSIS
    Returns true when a command exists on PATH.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $Name)

    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-McCommandVersion {
    <#
    .SYNOPSIS
    Returns the first line of a version command.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $FilePath,

        [Parameter(Mandatory)]
        [string[]] $CommandArguments,

        [Parameter(Mandatory)]
        [string] $ProjectRoot
    )

    $result = Invoke-McNativeCapture -FilePath $FilePath -CommandArguments $CommandArguments -WorkingDirectory $ProjectRoot
    if ($result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($result.Output)) {
        return $null
    }

    return ($result.Output -split "`n")[0].Trim()
}

function Test-McDockerRunning {
    <#
    .SYNOPSIS
    Checks whether Docker daemon is reachable.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    if (-not (Test-McCommand -Name "docker")) {
        return $false
    }

    $result = Invoke-McNativeCapture -FilePath "docker" -CommandArguments @("info") -WorkingDirectory $ProjectRoot
    return $result.ExitCode -eq 0
}

function Get-McContainerStatus {
    <#
    .SYNOPSIS
    Gets a Mission Control container status for the doctor report.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $ContainerName,

        [Parameter(Mandatory)]
        [string] $ProjectRoot
    )

    $inspect = Invoke-McNativeCapture -FilePath "docker" -CommandArguments @(
        "inspect",
        "--format",
        "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{end}}",
        $ContainerName
    ) -WorkingDirectory $ProjectRoot

    if ($inspect.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($inspect.Output)) {
        return "Missing"
    }

    $parts = $inspect.Output.Split("|", 2)
    $state = $parts[0]
    $health = if ($parts.Count -gt 1) { $parts[1] } else { "" }

    if ($state -ne "running") {
        return "Stopped"
    }
    if ($health -eq "healthy") {
        return "Healthy"
    }
    if ($health -eq "starting" -or [string]::IsNullOrWhiteSpace($health)) {
        return "Starting"
    }

    return "Stopped"
}


function Get-McEnvironmentDoctorResults {
    <#
    .SYNOPSIS
    Builds environment doctor checks.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    $results = [System.Collections.Generic.List[object]]::new()
    $psVersion = $PSVersionTable.PSVersion.ToString()
    $results.Add((New-McDoctorResult -Name "PowerShell Version" -Level "Pass" -Message $psVersion))

    if (Test-McCommand -Name "git") {
        $gitVersion = Get-McCommandVersion -FilePath "git" -CommandArguments @("--version") -ProjectRoot $ProjectRoot
        $results.Add((New-McDoctorResult -Name "Git Installed" -Level "Pass" -Message "available"))
        $results.Add((New-McDoctorResult -Name "Git Version" -Level "Pass" -Message $gitVersion))
    }
    else {
        $results.Add((New-McDoctorResult -Name "Git Installed" -Level "Fail" -Message "missing"))
        $results.Add((New-McDoctorResult -Name "Git Version" -Level "Fail" -Message "unavailable"))
    }

    $dockerInstalled = Test-McCommand -Name "docker"
    $dockerRunning = $dockerInstalled -and (Test-McDockerRunning -ProjectRoot $ProjectRoot)
    $results.Add((New-McDoctorResult -Name "Docker Installed" -Level $(if ($dockerInstalled) { "Pass" } else { "Fail" }) -Message $(if ($dockerInstalled) { "available" } else { "missing" })))
    $results.Add((New-McDoctorResult -Name "Docker Running" -Level $(if ($dockerRunning) { "Pass" } elseif ($dockerInstalled) { "Warn" } else { "Fail" }) -Message $(if ($dockerRunning) { "running" } elseif ($dockerInstalled) { "not running" } else { "unavailable" })))

    try {
        $compose = Get-McDockerComposeCommand
        $results.Add((New-McDoctorResult -Name "Docker Compose" -Level "Pass" -Message "$($compose.FilePath) available"))
    }
    catch {
        $results.Add((New-McDoctorResult -Name "Docker Compose" -Level "Fail" -Message "missing"))
    }

    foreach ($tool in @("python", "node", "npm")) {
        $installed = Test-McCommand -Name $tool
        $label = switch ($tool) {
            "python" { "Python" }
            "node" { "Node" }
            "npm" { "npm" }
        }
        $results.Add((New-McDoctorResult -Name "$label Installed" -Level $(if ($installed) { "Pass" } else { "Warn" }) -Message $(if ($installed) { "available" } else { "missing" })))
        if ($tool -eq "python") {
            $version = if ($installed) { Get-McCommandVersion -FilePath "python" -CommandArguments @("--version") -ProjectRoot $ProjectRoot } else { "unavailable" }
            $results.Add((New-McDoctorResult -Name "Python Version" -Level $(if ($installed) { "Pass" } else { "Warn" }) -Message $version))
        }
    }

    $isGitRepo = Test-Path -LiteralPath (Join-Path $ProjectRoot ".git")
    $remote = if ($isGitRepo -and (Test-McCommand -Name "git")) {
        Get-McCommandVersion -FilePath "git" -CommandArguments @("remote", "get-url", "origin") -ProjectRoot $ProjectRoot
    }
    else {
        $null
    }
    $isGitHub = $remote -and $remote.Contains("github.com")
    $results.Add((New-McDoctorResult -Name "GitHub Repository" -Level $(if ($isGitHub) { "Pass" } elseif ($isGitRepo) { "Warn" } else { "Fail" }) -Message $(if ($isGitHub) { $remote } elseif ($isGitRepo) { "origin is not GitHub or is missing" } else { "not a git repository" })))

    $branch = if ($isGitRepo -and (Test-McCommand -Name "git")) {
        Get-McCommandVersion -FilePath "git" -CommandArguments @("branch", "--show-current") -ProjectRoot $ProjectRoot
    }
    else {
        $null
    }
    $results.Add((New-McDoctorResult -Name "Current Branch" -Level $(if ($branch) { "Pass" } else { "Warn" }) -Message $(if ($branch) { $branch } else { "detached or unavailable" })))

    $status = if ($isGitRepo -and (Test-McCommand -Name "git")) {
        Invoke-McNativeCapture -FilePath "git" -CommandArguments @("status", "--porcelain") -WorkingDirectory $ProjectRoot
    }
    else {
        $null
    }
    $clean = $status -and $status.ExitCode -eq 0 -and [string]::IsNullOrWhiteSpace($status.Output)
    $results.Add((New-McDoctorResult -Name "Working Tree Clean" -Level $(if ($clean) { "Pass" } else { "Warn" }) -Message $(if ($clean) { "clean" } else { "uncommitted changes present" })))

    return $results
}

function Get-McServiceDoctorResults {
    <#
    .SYNOPSIS
    Builds Docker service doctor checks.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    $services = [ordered]@{
        "Mission Control Backend" = "missioncontrol-backend-1"
        "Mission Control Frontend" = "missioncontrol-frontend-1"
        "Mission Control PostgreSQL" = "missioncontrol-postgres-1"
        "Mission Control Redis" = "missioncontrol-redis-1"
        "Mission Control Nginx" = "missioncontrol-nginx-1"
    }

    foreach ($service in $services.GetEnumerator()) {
        $status = Get-McContainerStatus -ContainerName $service.Value -ProjectRoot $ProjectRoot
        $level = switch ($status) {
            "Healthy" { "Pass" }
            "Starting" { "Warn" }
            "Stopped" { "Fail" }
            "Missing" { "Warn" }
            default { "Warn" }
        }
        New-McDoctorResult -Name $service.Key -Level $level -Message $status
    }
}

function Get-McBackendEndpointDoctorResults {
    <#
    .SYNOPSIS
    Builds backend HTTP endpoint checks.
    #>
    [CmdletBinding()]
    param()

    foreach ($path in @("/health", "/ready", "/version")) {
        $status = Invoke-McHttpStatusCheck -Path $path
        $level = if ($status -match "^2\d\d$") { "Pass" } elseif ($status -eq "unreachable") { "Warn" } else { "Warn" }
        New-McDoctorResult -Name "GET $path" -Level $level -Message "HTTP $status"
    }
}

