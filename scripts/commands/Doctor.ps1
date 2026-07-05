<#
.SYNOPSIS
Doctor command module.
#>

Register-McCommand -Name "doctor" -HandlerFunction "Invoke-McDoctorCommand" -Description "Checks local tools, repository state, Docker services, and backend endpoints" -Usage @("mc doctor", "mc doctor --output console|json|json-pretty") -Examples @("mc doctor", "mc doctor --output json") -Options @("--output")

function Invoke-McDoctorCommand {
    <#
    .SYNOPSIS
    Returns environment, Docker, and HTTP health checks.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][pscustomobject] $Context)

    $sections = [System.Collections.Generic.List[object]]::new()
    $allChecks = [System.Collections.Generic.List[object]]::new()

    $environment = @(Get-McEnvironmentDoctorResults -ProjectRoot $Context.ProjectRoot)
    $sections.Add([pscustomobject]@{ Name = "Environment"; Checks = $environment })
    foreach ($check in $environment) { $allChecks.Add($check) }

    if (Test-McDockerRunning -ProjectRoot $Context.ProjectRoot) {
        $services = @(Get-McServiceDoctorResults -ProjectRoot $Context.ProjectRoot)
        $sections.Add([pscustomobject]@{ Name = "Docker Services"; Checks = $services })
        foreach ($check in $services) { $allChecks.Add($check) }

        $backend = Get-McContainerStatus -ContainerName "missioncontrol-backend-1" -ProjectRoot $Context.ProjectRoot
        if ($backend -in @("Healthy", "Starting")) {
            $http = @(Get-McBackendEndpointDoctorResults)
            $sections.Add([pscustomobject]@{ Name = "Backend HTTP"; Checks = $http })
            foreach ($check in $http) { $allChecks.Add($check) }
        }
    }

    $overall = if ($allChecks.Level -contains "Fail") {
        "FAILED"
    }
    elseif ($allChecks.Level -contains "Warn") {
        "WARNING"
    }
    else {
        "READY"
    }

    [pscustomobject]@{
        Type = "Doctor"
        OverallStatus = $overall
        Sections = @($sections)
    }
}
