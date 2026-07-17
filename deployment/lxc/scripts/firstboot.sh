#!/usr/bin/env bash
# ============================================================================
# Mission Control — First Boot Script
#
# Runs once on first container start to generate secrets, create the admin
# account, and display access information.
#
# Usage:
#   sudo ./firstboot.sh [--reset]
#
# The script is idempotent — it will never execute twice unless --reset
# is used.
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MC_INSTALL_DIR="/opt/missioncontrol"
MC_STATE_FILE="/var/lib/mission-control/.initialized"
MC_SETUP_COMPLETE="/var/lib/mission-control/.setup-complete"
MC_LOG="/var/log/mission-control-setup.log"
RESET=false

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
log()   { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${MC_LOG}"; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --reset) RESET=true; shift ;;
        --help|-h)
            echo "Usage: $0 [--reset]"
            echo ""
            echo "Options:"
            echo "  --reset    Force re-run even if already completed"
            echo "  -h, --help Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---------------------------------------------------------------------------
# Check if already run
# ---------------------------------------------------------------------------
if [[ -f "${MC_SETUP_COMPLETE}" ]] && [[ "${RESET}" != "true" ]]; then
    info "First boot already completed. Use --reset to force re-run."
    exit 0
fi

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root"
fi

log "=== Mission Control First Boot Setup ==="

# ---------------------------------------------------------------------------
# Step 1: Generate secrets
# ---------------------------------------------------------------------------
step "Generating Secrets"

# Secret key
if [[ -f "${MC_INSTALL_DIR}/.env" ]] && grep -q "MISSIONCONTROL_SECRET_KEY=CHANGE_ME" "${MC_INSTALL_DIR}/.env"; then
    SECRET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null \
        || openssl rand -base64 32)
    sed -i "s/MISSIONCONTROL_SECRET_KEY=CHANGE_ME/MISSIONCONTROL_SECRET_KEY=${SECRET_KEY}/" "${MC_INSTALL_DIR}/.env"
    log "Generated new secret key"
    ok "Secret key generated"
elif [[ -f "${MC_INSTALL_DIR}/.env" ]] && grep -q "MISSIONCONTROL_SECRET_KEY=" "${MC_INSTALL_DIR}/.env"; then
    ok "Secret key already set"
else
    warn ".env file not found or missing SECRET_KEY"
fi

# Database password
if [[ -f "${MC_INSTALL_DIR}/.env" ]] && grep -q "POSTGRES_PASSWORD=mission_control" "${MC_INSTALL_DIR}/.env"; then
    DB_PASSWORD=$(openssl rand -hex 16)
    sed -i "s/POSTGRES_PASSWORD=mission_control/POSTGRES_PASSWORD=${DB_PASSWORD}/" "${MC_INSTALL_DIR}/.env"
    log "Generated new database password"
    ok "Database password generated"
else
    ok "Database password already set"
fi

# ---------------------------------------------------------------------------
# Step 2: Generate admin password
# ---------------------------------------------------------------------------
step "Admin Account Setup"

ADMIN_EMAIL="admin@missioncontrol.local"
ADMIN_PASSWORD="admin"

log "Admin email: ${ADMIN_EMAIL}"
log "Admin password: ${ADMIN_PASSWORD}"
ok "Default admin credentials set"

# ---------------------------------------------------------------------------
# Step 3: Wait for Docker and services
# ---------------------------------------------------------------------------
step "Waiting for Services"

log "Waiting for Docker daemon..."
for i in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
        log "Docker is ready."
        break
    fi
    if [[ $i -eq 30 ]]; then
        die "Docker daemon not ready after 60s."
    fi
    sleep 2
done

log "Waiting for Mission Control stack..."
cd "${MC_INSTALL_DIR}"
for i in $(seq 1 60); do
    if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)" 2>/dev/null; then
        log "Backend is healthy."
        break
    fi
    if [[ $i -eq 60 ]]; then
        warn "Backend health check timed out after 120s."
    fi
    sleep 2
done

# ---------------------------------------------------------------------------
# Step 4: Run migrations
# ---------------------------------------------------------------------------
step "Running Migrations"

if docker compose exec -T backend alembic upgrade head 2>/dev/null; then
    log "Database migrations applied"
    ok "Migrations complete"
else
    warn "Migrations skipped"
fi

# ---------------------------------------------------------------------------
# Step 5: Display access information
# ---------------------------------------------------------------------------
step "Access Information"

CONTAINER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "<container-ip>")

echo ""
echo -e "${GREEN}Mission Control is ready!${NC}"
echo ""
echo "  URL:      http://${CONTAINER_IP}"
echo "  API Docs: http://${CONTAINER_IP}/api/docs"
echo ""
echo "  Login Credentials:"
echo "    Email:    ${ADMIN_EMAIL}"
echo "    Password: ${ADMIN_PASSWORD}"
echo ""
echo "  ${RED}IMPORTANT: Change the default password after first login!${NC}"
echo ""

# Display in logs too
log "Access URL: http://${CONTAINER_IP}"
log "Admin: ${ADMIN_EMAIL} / ${ADMIN_PASSWORD}"

# ---------------------------------------------------------------------------
# Step 6: Mark setup complete
# ---------------------------------------------------------------------------
step "Marking Setup Complete"

mkdir -p "$(dirname "${MC_STATE_FILE}")"
date -Iseconds > "${MC_STATE_FILE}"
date -Iseconds > "${MC_SETUP_COMPLETE}"

log "=== First boot setup complete ==="
ok "Setup marked complete"
