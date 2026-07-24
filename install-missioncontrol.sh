#!/usr/bin/env bash
# ============================================================================
# Mission Control — Production Installer
#
# One-shot installer for Ubuntu 24.04 (GCE, bare metal, or VM).
# Installs Docker, clones the repo, builds containers, and starts services.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/billboe3-png/MissionControl/main/install-missioncontrol.sh | bash
#   # or
#   ./install-missioncontrol.sh [--branch BRANCH] [--dir DIR] [--skip-build]
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_URL="https://github.com/billboe3-png/MissionControl.git"
MC_DIR="${MC_DIR:-/opt/MissionControl}"
MC_BRANCH="${MC_BRANCH:-develop}"
SKIP_BUILD=false
FORCE=false

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
step()  { echo -e "\n${CYAN}━━━ $* ━━━${NC}"; }
die()   { error "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)     MC_BRANCH="$2"; shift 2 ;;
        --dir)        MC_DIR="$2"; shift 2 ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        --force)      FORCE=true; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --branch BRANCH   Git branch (default: main)"
            echo "  --dir DIR         Install directory (default: /opt/MissionControl)"
            echo "  --skip-build      Skip Docker build step"
            echo "  --force           Overwrite existing .env"
            echo "  -h, --help        Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---------------------------------------------------------------------------
# Step 0: Detect Docker execution method
# ---------------------------------------------------------------------------
# After fresh Docker install, the current user is in the "docker" group but
# group membership isn't active until the next login. We detect whether
# Docker works without sudo, and wrap all docker commands accordingly.
# The script runs as the calling user (not root) for security.
# ---------------------------------------------------------------------------

USE_SUDO_DOCKER=false

if docker info >/dev/null 2>&1; then
    info "Docker accessible without sudo"
else
    if command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
        info "Docker requires sudo (you may be prompted for your password)"
        USE_SUDO_DOCKER=true
    else
        die "Docker is installed but not accessible. Log out and back in, or run: sudo usermod -aG docker \$USER"
    fi
fi

# Wrapper that prepends sudo when needed (preserves COMPOSE_FILE env var)
dc() {
    if [[ "$USE_SUDO_DOCKER" == "true" ]]; then
        sudo -E docker compose "$@"
    else
        docker compose "$@"
    fi
}

# Use the production compose file and a stable project name
# (absolute path — COMPOSE_FILE is resolved before cd into MC_DIR)
export COMPOSE_FILE="${MC_DIR}/docker-compose.prod.yml"
export COMPOSE_PROJECT_NAME="missioncontrol"

# ---------------------------------------------------------------------------
# Step 1: Install system dependencies
# ---------------------------------------------------------------------------
step "Installing System Dependencies"

export DEBIAN_FRONTEND=noninteractive

sudo apt-get update -qq
sudo apt-get install -y -qq \
    git curl wget ca-certificates gnupg jq unzip

ok "System dependencies installed"

# ---------------------------------------------------------------------------
# Step 2: Install Docker (idempotent)
# ---------------------------------------------------------------------------
step "Installing Docker"

if command -v docker >/dev/null 2>&1; then
    ok "Docker already installed: $(docker --version)"
else
    info "Installing Docker Engine..."
    curl -fsSL https://get.docker.com | sudo sh

    # Add current user to docker group
    sudo usermod -aG docker "$USER"
    ok "Docker installed"

    # Re-detect sudo requirement (Docker was just installed fresh)
    if docker info >/dev/null 2>&1; then
        info "Docker accessible without sudo"
        USE_SUDO_DOCKER=false
    elif sudo docker info >/dev/null 2>&1; then
        info "Docker requires sudo (user will need password)"
        USE_SUDO_DOCKER=true
    fi
fi

if dc version >/dev/null 2>&1; then
    ok "Docker Compose plugin ready"
else
    die "Docker Compose plugin not found"
fi

# ---------------------------------------------------------------------------
# Step 3: Clone or update repository
# ---------------------------------------------------------------------------
step "Cloning Repository"

if [[ -d "${MC_DIR}/.git" ]]; then
    info "Repository exists at ${MC_DIR}"
    if [[ "$FORCE" == "true" ]]; then
        info "Force mode: pulling latest changes..."
        cd "${MC_DIR}"
        git fetch origin
        git checkout "${MC_BRANCH}"
        git pull origin "${MC_BRANCH}"
    else
        info "Use --force to pull latest changes"
    fi
else
    info "Cloning to ${MC_DIR}..."
    sudo mkdir -p "$(dirname "${MC_DIR}")"
    sudo chown "$USER:" "$(dirname "${MC_DIR}")"
    git clone --branch "${MC_BRANCH}" "${REPO_URL}" "${MC_DIR}"
fi

cd "${MC_DIR}"
ok "Repository ready at ${MC_DIR} (branch: $(git branch --show-current))"

# ---------------------------------------------------------------------------
# Step 4: Create .env file
# ---------------------------------------------------------------------------
step "Configuring Environment"

if [[ -f ".env" ]] && [[ "$FORCE" != "true" ]]; then
    ok ".env already exists (use --force to regenerate)"
else
    SECRET_KEY=$(openssl rand -base64 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)

    cat > .env << ENVEOF
# Mission Control — Production Environment
# Generated by install-missioncontrol.sh on $(date -Iseconds)
# DO NOT commit this file to version control

PROJECT_NAME=Mission Control
ENVIRONMENT=production
MISSIONCONTROL_SECRET_KEY=${SECRET_KEY}

# PostgreSQL
POSTGRES_DB=mission_control
POSTGRES_USER=mission_control
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Backend
BACKEND_CORS_ORIGINS=http://localhost,http://localhost:80
ENVEOF

    chmod 600 .env
    ok "Environment file generated with secure defaults"
fi

# ---------------------------------------------------------------------------
# Step 5: Build and start containers
# ---------------------------------------------------------------------------
step "Building and Starting Services"

if [[ "$SKIP_BUILD" != "true" ]]; then
    info "Building Docker images (this may take several minutes)..."
    dc build --no-cache 2>&1 | tail -10
fi

info "Starting services..."
dc up -d

ok "Services started"

# ---------------------------------------------------------------------------
# Step 6: Wait for backend health
# ---------------------------------------------------------------------------
step "Waiting for Backend"

MAX_WAIT=120
WAITED=0

while [[ $WAITED -lt $MAX_WAIT ]]; do
    if dc exec -T backend \
        python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)" \
        >/dev/null 2>&1; then
        ok "Backend is healthy after ${WAITED}s"
        break
    fi

    sleep 5
    WAITED=$((WAITED + 5))
    info "Waiting... (${WAITED}/${MAX_WAIT}s)"
done

if [[ $WAITED -ge $MAX_WAIT ]]; then
    warn "Backend health check timed out after ${MAX_WAIT}s"
    warn "Check logs: dc logs backend"
fi

# ---------------------------------------------------------------------------
# Step 7: Print summary
# ---------------------------------------------------------------------------
step "Installation Complete"

HOST_IP=$(curl -s --connect-timeout 3 -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip 2>/dev/null \
    || curl -s --connect-timeout 3 https://ifconfig.me 2>/dev/null \
    || hostname -I 2>/dev/null | awk '{print $1}' \
    || echo "<server-ip>")

echo ""
echo -e "${GREEN}Mission Control is running!${NC}"
echo ""
echo "  URL:      http://${HOST_IP}"
echo "  API Docs: http://${HOST_IP}/api/docs"
echo ""
echo "  The setup wizard will guide you through creating your first admin account."
echo "  Visit the URL above and follow the on-screen instructions."
echo ""
# Determine the compose command to show in summary
if [[ "$USE_SUDO_DOCKER" == "true" ]]; then
    COMPOSE_PREFIX="sudo "
else
    COMPOSE_PREFIX=""
fi

echo "  Management:"
echo "    cd ${MC_DIR}"
echo "    ${COMPOSE_PREFIX}docker compose logs -f        # View logs"
echo "    ${COMPOSE_PREFIX}docker compose restart         # Restart"
echo "    ${COMPOSE_PREFIX}docker compose down            # Stop"
echo ""
echo "  Files:"
echo "    Install dir: ${MC_DIR}"
echo "    Config:      ${MC_DIR}/.env"
echo "    Compose:     ${MC_DIR}/docker-compose.prod.yml"
echo ""
echo "  Backup your .env file! It contains your secret key."
echo ""
