<#
.SYNOPSIS
Project commands, help, status, version, and initialization.
#>

$script:McVersion = "0.1.0"

function Show-McHelp {
    <#
    .SYNOPSIS
    Shows CLI help.
    #>
    [CmdletBinding()]
    param()

    Write-Host "Mission Control Developer CLI" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  mc help"
    Write-Host "  mc init"
    Write-Host "  mc status"
    Write-Host "  mc doctor"
    Write-Host "  mc version"
    Write-Host "  mc docker up|down|logs"
    Write-Host "  mc git status"
    Write-Host '  mc git commit "<message>"'
    Write-Host ""
    Write-Host "Future commands:" -ForegroundColor Yellow
    Write-Host "  mc sprint create <number>"
    Write-Host "  mc build"
    Write-Host "  mc clean"
    Write-Host "  mc lint"
    Write-Host "  mc test"
}

function Show-McVersion {
    <#
    .SYNOPSIS
    Shows CLI version.
    #>
    [CmdletBinding()]
    param()

    Write-Host "Mission Control CLI $script:McVersion" -ForegroundColor Green
}

function Initialize-McProject {
    <#
    .SYNOPSIS
    Performs idempotent developer project initialization.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    Write-Progress -Activity "Mission Control init" -Status "Checking project files" -PercentComplete 25
    $envFile = Join-Path $ProjectRoot ".env"
    $envExample = Join-Path $ProjectRoot ".env.example"

    if (-not (Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath $envExample)) {
        Copy-Item -LiteralPath $envExample -Destination $envFile
        Write-McSuccess "Created .env from .env.example."
    }
    else {
        Write-McInfo ".env already exists or .env.example is unavailable."
    }

    Write-Progress -Activity "Mission Control init" -Status "Checking developer folders" -PercentComplete 70
    foreach ($path in @("logs", "scripts/lib")) {
        $fullPath = Join-Path $ProjectRoot $path
        if (-not (Test-Path -LiteralPath $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath | Out-Null
            Write-McSuccess "Created $path."
        }
    }

    Write-Progress -Activity "Mission Control init" -Completed
    Write-McSuccess "Project initialization complete."
}

function Show-McStatus {
    <#
    .SYNOPSIS
    Shows local developer environment status.
    #>
    [CmdletBinding()]
    param([Parameter(Mandatory)][string] $ProjectRoot)

    Write-Host "Mission Control Status" -ForegroundColor Green
    Write-Host "Project root: $ProjectRoot"
    Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
    Write-Host ".env: $(if (Test-Path -LiteralPath (Join-Path $ProjectRoot ".env")) { "present" } else { "missing" })"
    Write-Host "Docker Compose: $(Get-McDockerComposeStatus)"
    Write-Host "Git: $(if (Get-Command git -ErrorAction SilentlyContinue) { "available" } else { "missing" })"
}

function Get-McDockerComposeStatus {
    <#
    .SYNOPSIS
    Returns a short Docker Compose availability status.
    #>
    [CmdletBinding()]
    param()

    try {
        $compose = Get-McDockerComposeCommand
        return "$($compose.FilePath) available"
    }
    catch {
        return "missing"
    }
}
