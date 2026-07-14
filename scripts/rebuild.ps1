<#
.SYNOPSIS
    Completely rebuilds the Mission Control Docker environment from scratch.

.DESCRIPTION
    This script performs a full clean rebuild of all Docker services:
    1. Stops all running containers
    2. Removes containers, networks, and anonymous volumes
    3. Prunes Docker builder cache
    4. Rebuilds all images without cache
    5. Starts all services
    6. Verifies all services are healthy

.EXAMPLE
    .\rebuild.ps1
    .\rebuild.ps1 -SkipPrune
    .\rebuild.ps1 -SkipVerify
#>

param(
    [switch]$SkipPrune,
    [switch]$SkipVerify,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

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

function Write-Warning {
    param([string]$Message)
    Write-Host "    ⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "    ✗ $Message" -ForegroundColor Red
}

function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# ---------------------------------------------------------------
# Pre-flight Checks
# ---------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor White
Write-Host "  Mission Control - Docker Rebuild" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White

Write-Step "Running pre-flight checks..."

# Check Docker is available
if (-not (Test-CommandExists "docker")) {
    Write-Error "Docker is not installed or not in PATH"
    exit 1
}
Write-Success "Docker found: $(docker --version)"

# Check Docker Compose is available
$composeCmd = $null
if (docker compose version 2>$null) {
    $composeCmd = "docker compose"
    Write-Success "Docker Compose v2 found"
} elseif (Test-CommandExists "docker-compose") {
    $composeCmd = "docker-compose"
    Write-Success "Docker Compose v1 found"
} else {
    Write-Error "Docker Compose is not installed"
    exit 1
}

# Check .env file exists
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Warning ".env file not found"
    $exampleEnv = Join-Path $ProjectRoot ".env.example"
    if (Test-Path $exampleEnv) {
        Write-Host "    Copying .env.example to .env..."
        Copy-Item $exampleEnv $envFile
        Write-Success "Created .env from .env.example"
        Write-Warning "Please update .env with your actual values before starting"
    } else {
        Write-Error "No .env or .env.example found"
        exit 1
    }
}

# Check for required environment variables
$envContent = Get-Content $envFile -Raw
if ($envContent -match "MISSIONCONTROL_SECRET_KEY=CHANGE_ME") {
    Write-Warning "MISSIONCONTROL_SECRET_KEY is set to CHANGE_ME"
    Write-Host "    Generating a new key..."
    $newKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>$null
    if ($newKey) {
        $envContent = $envContent -replace "MISSIONCONTROL_SECRET_KEY=CHANGE_ME", "MISSIONCONTROL_SECRET_KEY=$newKey"
        Set-Content -Path $envFile -Value $envContent
        Write-Success "Generated and saved new MISSIONCONTROL_SECRET_KEY"
    } else {
        Write-Error "Could not generate MISSIONCONTROL_SECRET_KEY. Please install cryptography: pip install cryptography"
    }
}

# ---------------------------------------------------------------
# Step 1: Stop all running containers
# ---------------------------------------------------------------
Write-Step "Stopping all running containers..."
& docker compose -f $ComposeFile down --remove-orphans 2>&1 | ForEach-Object { if ($Verbose) { Write-Host "    $_" } }
Write-Success "Containers stopped"

# ---------------------------------------------------------------
# Step 2: Remove images
# ---------------------------------------------------------------
Write-Step "Removing Mission Control images..."
$images = & docker images --format "{{.Repository}}:{{.Tag}}" | Select-String "missioncontrol" 2>$null
if ($images) {
    foreach ($image in $images) {
        & docker rmi $image -f 2>$null | Out-Null
    }
    Write-Success "Images removed"
} else {
    Write-Success "No images to remove"
}

# ---------------------------------------------------------------
# Step 3: Prune Docker builder cache
# ---------------------------------------------------------------
if (-not $SkipPrune) {
    Write-Step "Pruning Docker builder cache..."
    & docker builder prune -f 2>&1 | ForEach-Object { if ($Verbose) { Write-Host "    $_" } }
    Write-Success "Builder cache pruned"

    Write-Step "Pruning Docker system (dangling images, unused networks)..."
    & docker system prune -f 2>&1 | ForEach-Object { if ($Verbose) { Write-Host "    $_" } }
    Write-Success "System pruned"
}

# ---------------------------------------------------------------
# Step 4: Rebuild all images without cache
# ---------------------------------------------------------------
Write-Step "Rebuilding all images (no cache)..."
& docker compose -f $ComposeFile build --no-cache 2>&1 | ForEach-Object { Write-Host "    $_" }
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed"
    exit 1
}
Write-Success "All images built successfully"

# ---------------------------------------------------------------
# Step 5: Start all services
# ---------------------------------------------------------------
Write-Step "Starting all services..."
& docker compose -f $ComposeFile up -d 2>&1 | ForEach-Object { if ($Verbose) { Write-Host "    $_" } }
Write-Success "Services started"

# ---------------------------------------------------------------
# Step 6: Wait for services to be healthy
# ---------------------------------------------------------------
if (-not $SkipVerify) {
    Write-Step "Waiting for services to become healthy (this may take a minute)..."
    
    $maxWait = 120
    $elapsed = 0
    $interval = 5
    
    while ($elapsed -lt $maxWait) {
        $services = & docker compose -f $ComposeFile ps --format "{{.Name}} {{.Health}}" 2>$null
        $allHealthy = $true
        $statusLines = @()
        
        foreach ($line in $services) {
            $parts = $line -split " "
            $name = $parts[0]
            $health = if ($parts.Count -gt 1) { $parts[1] } else { "starting" }
            $statusLines += "$name : $health"
            if ($health -ne "healthy" -and $health -notlike "running*") {
                $allHealthy = $false
            }
        }
        
        Write-Host "`r    [$elapsed s] Services: $($statusLines -join ' | ')" -NoNewline
        
        if ($allHealthy) {
            Write-Host ""
            Write-Success "All services are healthy!"
            break
        }
        
        Start-Sleep -Seconds $interval
        $elapsed += $interval
    }
    
    if ($elapsed -ge $maxWait) {
        Write-Host ""
        Write-Warning "Some services may not be fully healthy yet"
        Write-Host "    Check with: docker compose ps"
    }
    
    # ---------------------------------------------------------------
    # Step 7: Verify services
    # ---------------------------------------------------------------
    Write-Step "Verifying services..."
    
    # Check API health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/api/v1/health/live" -TimeoutSec 5 -UseBasicParsing
        Write-Success "API health check: $($response.StatusCode)"
    } catch {
        Write-Warning "API health check failed: $_"
    }
    
    # Check frontend
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/" -TimeoutSec 5 -UseBasicParsing
        Write-Success "Frontend check: $($response.StatusCode)"
    } catch {
        Write-Warning "Frontend check failed: $_"
    }
    
    # Show container status
    Write-Step "Container status:"
    & docker compose -f $ComposeFile ps
}

# ---------------------------------------------------------------
# Done
# ---------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Rebuild Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Services are running at: http://localhost" -ForegroundColor White
Write-Host ""
Write-Host "  Useful commands:" -ForegroundColor White
Write-Host "    docker compose ps          - Show container status" -ForegroundColor Gray
Write-Host "    docker compose logs -f     - Follow logs" -ForegroundColor Gray
Write-Host "    docker compose down        - Stop all services" -ForegroundColor Gray
Write-Host ""
