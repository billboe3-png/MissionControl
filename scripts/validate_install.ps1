<#
.SYNOPSIS
    Mission Control — Installation Validation Script (Windows)

.DESCRIPTION
    Validates a clean installation on Windows with Docker Desktop.
    Run this after deployment to verify everything is working.

.EXAMPLE
    .\validate_install.ps1
#>

$ErrorActionPreference = "Continue"

$pass = 0
$fail = 0
$warn = 0

function Pass { param([string]$msg); Write-Host "  + $msg" -ForegroundColor Green; $script:pass++ }
function Fail { param([string]$msg); Write-Host "  x $msg" -ForegroundColor Red; $script:fail++ }
function Warn { param([string]$msg); Write-Host "  ! $msg" -ForegroundColor Yellow; $script:warn++ }

Write-Host ""
Write-Host "  Mission Control - Installation Validation (Windows)"
Write-Host "  --------------------------------------------------"
Write-Host ""

# ------------------------------------------------------------------ #
# 1. Docker                                                            #
# ------------------------------------------------------------------ #

Write-Host "  Docker"
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Pass "Docker installed: $(docker --version)"
} else {
    Fail "Docker not found"
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    $composeVer = docker compose version 2>$null
    if ($composeVer) {
        Pass "Docker Compose available"
    } else {
        Fail "Docker Compose not found"
    }
}

# ------------------------------------------------------------------ #
# 2. Docker Services                                                   #
# ------------------------------------------------------------------ #

Write-Host ""
Write-Host "  Docker Services"

$services = docker compose ps --format "{{.Name}} {{.Status}}" 2>$null
if ($services) {
    foreach ($line in $services -split "`n") {
        $parts = $line -split " ", 2
        $name = $parts[0]
        $status = $parts[1]
        if ($status -match "Up") {
            Pass "$name is running"
        } else {
            Warn "$name status: $status"
        }
    }
} else {
    Warn "Could not list Docker services"
}

# ------------------------------------------------------------------ #
# 3. Configuration                                                     #
# ------------------------------------------------------------------ #

Write-Host ""
Write-Host "  Configuration"

if (Test-Path ".env") {
    Pass ".env file exists"
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "MISSIONCONTROL_SECRET_KEY=.+") {
        Pass "MISSIONCONTROL_SECRET_KEY is set"
    } else {
        Fail "MISSIONCONTROL_SECRET_KEY is missing in .env"
    }
    if ($envContent -match "POSTGRES_PASSWORD=.+") {
        Pass "POSTGRES_PASSWORD is set"
    } else {
        Warn "POSTGRES_PASSWORD not set"
    }
} else {
    Fail ".env file not found"
}

# ------------------------------------------------------------------ #
# 4. Health Endpoints                                                  #
# ------------------------------------------------------------------ #

Write-Host ""
Write-Host "  Health Endpoints"

$port = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { "8000" }
$baseUrl = "http://localhost:$port"

try {
    $live = Invoke-RestMethod -Uri "$baseUrl/api/v1/health/live" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Pass "Liveness endpoint responding"
} catch {
    Warn "Liveness endpoint not reachable"
}

try {
    $ready = Invoke-RestMethod -Uri "$baseUrl/api/v1/health/ready" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Pass "Readiness endpoint responding"
} catch {
    Warn "Readiness endpoint not reachable"
}

try {
    $subs = Invoke-RestMethod -Uri "$baseUrl/api/v1/health/subsystems" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Pass "Subsystem health endpoint responding"
} catch {
    Warn "Subsystem health endpoint not reachable"
}

try {
    $ver = Invoke-RestMethod -Uri "$baseUrl/api/v1/version" -Method Get -TimeoutSec 5 -ErrorAction Stop
    Pass "Version endpoint responding: $($ver.version)"
} catch {
    Warn "Version endpoint not reachable"
}

# ------------------------------------------------------------------ #
# 5. Frontend                                                          #
# ------------------------------------------------------------------ #

Write-Host ""
Write-Host "  Frontend"

$fePort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3000" }
try {
    Invoke-RestMethod -Uri "http://localhost:$fePort" -Method Get -TimeoutSec 5 -ErrorAction Stop | Out-Null
    Pass "Frontend serving on port $fePort"
} catch {
    Warn "Frontend not reachable on port $fePort"
}

# ------------------------------------------------------------------ #
# Summary                                                              #
# ------------------------------------------------------------------ #

Write-Host ""
Write-Host "  --------------------------------------------------"
Write-Host "  Passed: $pass  Failed: $fail  Warnings: $warn"

if ($fail -gt 0) {
    Write-Host "  RESULT: VALIDATION FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  RESULT: VALIDATION PASSED" -ForegroundColor Green
    exit 0
}
