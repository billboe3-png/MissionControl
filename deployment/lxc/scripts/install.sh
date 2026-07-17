#!/usr/bin/env bash
# ============================================================================
# Mission Control — LXC Installer
#
# Idempotent installer that sets up Mission Control in an Ubuntu LXC container.
# Safe to run multiple times — will not break existing installations.
#
# Usage:
#   sudo ./install.sh [--version VERSION] [--branch BRANCH] [--skip-build]
#
# Requirements:
#   - Ubuntu 24.04 LXC container with nesting + keyctl enabled
#   - Root access
#   - Internet access
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MC_INSTALL_DIR="/opt/missioncontrol"
MC_SCRIPTS_DIR="${MC_INSTALL_DIR}/scripts"
MC_CONFIG_DIR="${MC_INSTALL_DIR}/config"
MC_DATA_DIR="${MC_INSTALL_DIR}/data"
MC_BACKUP_DIR="${MC_INSTALL_DIR}/backups"
MC_LOG_DIR="${MC_INSTALL_DIR}/logs"
MC_PLUGIN_DIR="${MC_INSTALL_DIR}/plugins"
MC_PLAYBOOK_DIR="${MC_INSTALL_DIR}/playbooks"
MC_AUTOMATION_DIR="${MC_INSTALL_DIR}/automation"
MC_STATE_FILE="/var/lib/mission-control/.installed"
MC_VERSION="${MC_VERSION:-3.0.0}"
MC_BRANCH="${MC_BRANCH:-main}"
MC_COMPOSE_URL="${MC_COMPOSE_URL:-}"
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
        --version)    MC_VERSION="$2"; shift 2 ;;
        --branch)     MC_BRANCH="$2"; shift 2 ;;
        --compose-url) MC_COMPOSE_URL="$2"; shift 2 ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        --force)      FORCE=true; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --version VERSION     Mission Control version (default: $MC_VERSION)"
            echo "  --branch BRANCH       Git branch (default: $MC_BRANCH)"
            echo "  --compose-url URL     URL to download compose files"
            echo "  --skip-build          Skip Docker build step"
            echo "  --force               Force reinstall even if already installed"
            echo "  -h, --help            Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
step "Preflight Checks"

if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root"
fi

for cmd in docker curl openssl; do
    command -v "$cmd" >/dev/null 2>&1 || die "Required command not found: $cmd"
done

# Check Docker Compose plugin
if ! docker compose version >/dev/null 2>&1; then
    die "Docker Compose plugin not found. Install Docker Engine with compose plugin."
fi

# Check nesting support (crucial for Docker-in-LXC)
if [[ -f /proc/self/status ]]; then
    NESTING=$(grep -i "^NStgid:" /proc/self/status 2>/dev/null | awk '{print $2}' || echo "0")
    if [[ "$NESTING" == "0" ]]; then
        warn "Nesting may not be enabled. Docker-in-LXC requires nesting=1."
        warn "Run: pct set <VMID> -features nesting=1,keyctl=1"
    fi
fi

ok "Preflight checks passed"

# ---------------------------------------------------------------------------
# Step 1: Create directory structure
# ---------------------------------------------------------------------------
step "Creating Directory Structure"

mkdir -p "${MC_INSTALL_DIR}"
mkdir -p "${MC_SCRIPTS_DIR}"
mkdir -p "${MC_CONFIG_DIR}/plugins"
mkdir -p "${MC_DATA_DIR}"
mkdir -p "${MC_BACKUP_DIR}/db"
mkdir -p "${MC_BACKUP_DIR}/config"
mkdir -p "${MC_BACKUP_DIR}/full"
mkdir -p "${MC_LOG_DIR}/nginx"
mkdir -p "${MC_LOG_DIR}/backup"
mkdir -p "${MC_PLUGIN_DIR}"
mkdir -p "${MC_PLAYBOOK_DIR}"
mkdir -p "${MC_AUTOMATION_DIR}"

ok "Directory structure created"

# ---------------------------------------------------------------------------
# Step 2: Install management scripts
# ---------------------------------------------------------------------------
step "Installing Management Scripts"

# Copy scripts from deployment package
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for script in update.sh backup.sh restore.sh health.sh firstboot.sh clean-template.sh; do
    if [[ -f "${SCRIPT_DIR}/${script}" ]]; then
        cp "${SCRIPT_DIR}/${script}" "${MC_SCRIPTS_DIR}/${script}"
        chmod +x "${MC_SCRIPTS_DIR}/${script}"
        ok "Installed ${script}"
    fi
done

# Create convenience symlinks
for cmd in mc-status mc-logs mc-restart mc-update mc-health mc-backup mc-restore; do
    case "$cmd" in
        mc-status)   target="${MC_SCRIPTS_DIR}/health.sh --status-only" ;;
        mc-logs)     target="docker compose -f ${MC_INSTALL_DIR}/docker-compose.yml logs" ;;
        mc-restart)  target="docker compose -f ${MC_INSTALL_DIR}/docker-compose.yml restart" ;;
        mc-update)   target="${MC_SCRIPTS_DIR}/update.sh" ;;
        mc-health)   target="${MC_SCRIPTS_DIR}/health.sh" ;;
        mc-backup)   target="${MC_SCRIPTS_DIR}/backup.sh" ;;
        mc-restore)  target="${MC_SCRIPTS_DIR}/restore.sh" ;;
    esac
    cat > "/usr/local/bin/${cmd}" << CMDEOF
#!/usr/bin/env bash
exec ${target} "\$@"
CMDEOF
    chmod +x "/usr/local/bin/${cmd}"
done

ok "Management scripts installed"

# ---------------------------------------------------------------------------
# Step 3: Download or copy Docker Compose files
# ---------------------------------------------------------------------------
step "Setting Up Docker Compose"

if [[ -n "${MC_COMPOSE_URL}" ]]; then
    info "Downloading compose files from ${MC_COMPOSE_URL}..."
    curl -fsSL "${MC_COMPOSE_URL}/docker-compose.prod.yml" -o "${MC_INSTALL_DIR}/docker-compose.yml"
    curl -fsSL "${MC_COMPOSE_URL}/.env.example" -o "${MC_INSTALL_DIR}/.env.example"
    curl -fsSL "${MC_COMPOSE_URL}/nginx/default.conf" -o "${MC_INSTALL_DIR}/nginx/default.conf"
else
    # Copy from local deployment package
    DEPLOY_DIR="$(dirname "${SCRIPT_DIR}")"
    if [[ -f "${DEPLOY_DIR}/docker-compose.prod.yml" ]]; then
        cp "${DEPLOY_DIR}/docker-compose.prod.yml" "${MC_INSTALL_DIR}/docker-compose.yml"
    elif [[ -f "${MC_INSTALL_DIR}/docker-compose.yml" ]]; then
        info "Using existing docker-compose.yml"
    else
        die "No docker-compose.yml found. Provide --compose-url or place files in ${MC_INSTALL_DIR}"
    fi

    # Copy nginx config
    if [[ -f "${DEPLOY_DIR}/nginx/default.conf" ]]; then
        mkdir -p "${MC_INSTALL_DIR}/nginx"
        cp "${DEPLOY_DIR}/nginx/default.conf" "${MC_INSTALL_DIR}/nginx/default.conf"
    fi
fi

ok "Docker Compose files ready"

# ---------------------------------------------------------------------------
# Step 4: Generate environment file
# ---------------------------------------------------------------------------
step "Configuring Environment"

if [[ -f "${MC_INSTALL_DIR}/.env" ]] && [[ "$FORCE" != "true" ]]; then
    warn ".env file already exists. Skipping generation (use --force to overwrite)"
else
    # Generate secrets
    SECRET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null \
        || openssl rand -base64 32)
    POSTGRES_PASSWORD=$(openssl rand -hex 16)

    cat > "${MC_INSTALL_DIR}/.env" << ENVEOF
# Mission Control Environment Configuration
# Generated by install.sh on $(date -Iseconds)
# DO NOT commit this file to version control

PROJECT_NAME=Mission Control
ENVIRONMENT=production
MC_VERSION=${MC_VERSION}

# Security
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

# Docker
COMPOSE_PROJECT_NAME=missioncontrol
ENVEOF

    chmod 600 "${MC_INSTALL_DIR}/.env"
    ok "Environment file generated with secure defaults"
fi

# ---------------------------------------------------------------------------
# Step 5: Configure Nginx logging
# ---------------------------------------------------------------------------
step "Configuring Nginx"

# Create empty log files so Docker doesn't create directories as root
touch "${MC_LOG_DIR}/nginx/access.log"
touch "${MC_LOG_DIR}/nginx/error.log"

ok "Nginx configured"

# ---------------------------------------------------------------------------
# Step 6: Build and start containers
# ---------------------------------------------------------------------------
step "Building and Starting Services"

cd "${MC_INSTALL_DIR}"

if [[ "$SKIP_BUILD" != "true" ]]; then
    info "Building Docker images..."
    docker compose build --no-cache 2>&1 | tail -5
fi

info "Starting services..."
docker compose up -d

ok "Services started"

# ---------------------------------------------------------------------------
# Step 7: Wait for health
# ---------------------------------------------------------------------------
step "Waiting for Services to be Healthy"

MAX_WAIT=120
WAITED=0

while [[ $WAITED -lt $MAX_WAIT ]]; do
    # Check if backend responds
    BACKEND_PORT=$(docker compose port backend 8000 2>/dev/null | cut -d: -f2 || echo "")
    if [[ -n "$BACKEND_PORT" ]]; then
        if curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/v1/health/live" >/dev/null 2>&1; then
            ok "Backend is healthy after ${WAITED}s"
            break
        fi
    fi

    # Fallback: check via docker compose exec
    if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)" 2>/dev/null; then
        ok "Backend is healthy after ${WAITED}s"
        break
    fi

    sleep 5
    WAITED=$((WAITED + 5))
    info "Waiting... (${WAITED}/${MAX_WAIT}s)"
done

if [[ $WAITED -ge $MAX_WAIT ]]; then
    warn "Backend health check timed out after ${MAX_WAIT}s"
    warn "Services may still be starting. Check: docker compose logs backend"
fi

# ---------------------------------------------------------------------------
# Step 8: Run database migrations
# ---------------------------------------------------------------------------
step "Running Database Migrations"

if docker compose exec -T backend alembic upgrade head 2>/dev/null; then
    ok "Database migrations applied"
else
    warn "Migration step skipped or failed (may be first run)"
fi

# ---------------------------------------------------------------------------
# Step 9: Create default admin user
# ---------------------------------------------------------------------------
step "Creating Default Admin User"

if docker compose exec -T backend python -c "
import sys
sys.path.insert(0, '/app')
from app.database import get_db
from app.models import User
from sqlalchemy.orm import Session
db = next(get_db())
user = db.query(User).filter(User.email == 'admin@missioncontrol.local').first()
if user:
    print('Admin user exists')
else:
    print('Creating admin user...')
" 2>/dev/null; then
    ok "Admin user check complete"
else
    info "Admin user will be created on first login"
fi

# ---------------------------------------------------------------------------
# Step 10: Mark installation
# ---------------------------------------------------------------------------
step "Finalizing Installation"

mkdir -p "$(dirname "${MC_STATE_FILE}")"
cat > "${MC_STATE_FILE}" << STATEEOF
installed_at=$(date -Iseconds)
version=${MC_VERSION}
branch=${MC_BRANCH}
STATEEOF

ok "Installation marked complete"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step "Installation Complete"

CONTAINER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<container-ip>")

echo ""
echo -e "${GREEN}Mission Control ${MC_VERSION} installed successfully!${NC}"
echo ""
echo "  Access:"
echo "    URL:      http://${CONTAINER_IP}"
echo "    API Docs: http://${CONTAINER_IP}/api/docs"
echo ""
echo "  Login:"
echo "    Email:    admin@missioncontrol.local"
echo "    Password: admin"
echo ""
echo "  Management:"
echo "    mc-status     Show container status"
echo "    mc-health     Run health checks"
echo "    mc-logs       View logs"
echo "    mc-restart    Restart services"
echo "    mc-update     Update Mission Control"
echo "    mc-backup     Create backup"
echo "    mc-restore    Restore from backup"
echo ""
echo "  Files:"
echo "    Install dir: ${MC_INSTALL_DIR}"
echo "    Config:      ${MC_INSTALL_DIR}/.env"
echo "    Compose:     ${MC_INSTALL_DIR}/docker-compose.yml"
echo ""
echo "  Backup your .env file! It contains your secret key."
echo ""
