<#
.SYNOPSIS
    Verifies the Mission Control Docker environment is running correctly.

.DESCRIPTION
    This script checks all services and verifies:
    - All containers are running
    - PostgreSQL is healthy and accepting connections
    - Redis is healthy and responding to PING
    - Backend API is responding
    - Frontend is accessible
    - Nginx is proxying correctly
    - Alembic migrations have been applied

.EXAMPLE
    .\verify.ps1
    .\verify.ps1 -Detailed
#>

param(
    [switch]$Detailed
)

$ErrorActionPreference = "Continue"

# ---------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $ProjectRoot "docker-compose.yml"

# ---------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------
function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "    ✓ $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "    ✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "    i $Message" -ForegroundColor Yellow
}

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  Mission Control - Environment Verify" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White

$passed = 0
$failed = 0
$warnings = 0

# ---------------------------------------------------------------
# 1. Check Container Status
# ---------------------------------------------------------------
Write-Step "Checking container status..."

$services = @("backend", "frontend", "nginx", "postgres", "redis")
$psOutput = & docker compose -f $ComposeFile ps --format "{{.Name}} {{.State}} {{.Health}}" 2>&1

foreach ($service in $services) {
    $found = $false
    foreach ($line in $psOutput) {
        if ($line -match $service) {
            $found = $true
            $parts = $line -split "\s+"
            $state = $parts[1]
            $health = if ($parts.Count -gt 2) { $parts[2] } else { "N/A" }
            
            if ($state -eq "running" -and ($health -eq "healthy" -or $health -eq "N/A" -or $health -eq "")) {
                Write-Success "$service : running ($health)"
                $passed++
            } elseif ($state -eq "running") {
                Write-Info "$service : running ($health)"
                $warnings++
            } else {
                Write-Fail "$service : $state"
                $failed++
            }
            break
        }
    }
    if (-not $found) {
        Write-Fail "$service : not found"
        $failed++
    }
}

# ---------------------------------------------------------------
# 2. Check PostgreSQL
# ---------------------------------------------------------------
Write-Step "Checking PostgreSQL..."

try {
    $pgResult = & docker compose -f $ComposeFile exec -T postgres pg_isready -U mission_control -d mission_control 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "PostgreSQL is accepting connections"
        $passed++
    } else {
        Write-Fail "PostgreSQL is not ready"
        $failed++
    }
} catch {
    Write-Fail "Could not check PostgreSQL: $_"
    $failed++
}

# ---------------------------------------------------------------
# 3. Check Redis
# ---------------------------------------------------------------
Write-Step "Checking Redis..."

try {
    $redisResult = & docker compose -f $ComposeFile exec -T redis redis-cli ping 2>&1
    if ($redisResult -match "PONG") {
        Write-Success "Redis is responding to PING"
        $passed++
    } else {
        Write-Fail "Redis is not responding correctly"
        $failed++
    }
} catch {
    Write-Fail "Could not check Redis: $_"
    $failed++
}

# ---------------------------------------------------------------
# 4. Check Backend API
# ---------------------------------------------------------------
Write-Step "Checking Backend API..."

try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/v1/health/live" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "Backend API is responding (HTTP $($response.StatusCode))"
        $passed++
        
        if ($Detailed) {
            Write-Info "Response: $($response.Content)"
        }
    } else {
        Write-Fail "Backend API returned HTTP $($response.StatusCode)"
        $failed++
    }
} catch {
    Write-Fail "Backend API is not responding: $_"
    $failed++
}

# ---------------------------------------------------------------
# 5. Check Dashboard API
# ---------------------------------------------------------------
Write-Step "Checking Dashboard API..."

try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/v1/dashboard" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "Dashboard API is responding (HTTP $($response.StatusCode))"
        $passed++
        
        if ($Detailed) {
            $dashboard = $response.Content | ConvertFrom-Json
            Write-Info "Application: $($dashboard.application.name) v$($dashboard.application.version)"
        }
    } else {
        Write-Fail "Dashboard API returned HTTP $($response.StatusCode)"
        $failed++
    }
} catch {
    Write-Fail "Dashboard API is not responding: $_"
    $failed++
}

# ---------------------------------------------------------------
# 6. Check Frontend
# ---------------------------------------------------------------
Write-Step "Checking Frontend..."

try {
    $response = Invoke-WebRequest -Uri "http://localhost/" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "Frontend is accessible (HTTP $($response.StatusCode))"
        $passed++
        
        if ($Detailed -and $response.Content -match "<title>(.*?)</title>") {
            Write-Info "Page title: $($Matches[1])"
        }
    } else {
        Write-Fail "Frontend returned HTTP $($response.StatusCode)"
        $failed++
    }
} catch {
    Write-Fail "Frontend is not accessible: $_"
    $failed++
}

# ---------------------------------------------------------------
# 7. Check Nginx
# ---------------------------------------------------------------
Write-Step "Checking Nginx proxy..."

try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/v1/health/live" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200 -and $response.Headers["Server"] -match "nginx") {
        Write-Success "Nginx is proxying requests correctly"
        $passed++
    } elseif ($response.StatusCode -eq 200) {
        Write-Success "Nginx is proxying requests (server header not visible)"
        $passed++
    } else {
        Write-Fail "Nginx proxy is not working correctly"
        $failed++
    }
} catch {
    Write-Fail "Nginx proxy check failed: $_"
    $failed++
}

# ---------------------------------------------------------------
# 8. Check Alembic Migrations
# ---------------------------------------------------------------
Write-Step "Checking database migrations..."

try {
    $alembicResult = & docker compose -f $ComposeFile exec -T backend alembic current 2>&1
    if ($alembicResult -match "Current") {
        Write-Success "Alembic migrations are applied"
        $passed++
        
        if ($Detailed) {
            Write-Info "Current revision: $alembicResult"
        }
    } else {
        Write-Info "Alembic status: $alembicResult"
        $warnings++
    }
} catch {
    Write-Info "Could not check Alembic migrations: $_"
    $warnings++
}

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  Verification Summary" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White
Write-Host ""
Write-Host "  Passed:   $passed" -ForegroundColor Green
Write-Host "  Failed:   $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Gray" })
Write-Host "  Warnings: $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "Gray" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "  ✓ All critical checks passed!" -ForegroundColor Green
} else {
    Write-Host "  ✗ Some checks failed. Review the output above." -ForegroundColor Red
}

Write-Host ""
