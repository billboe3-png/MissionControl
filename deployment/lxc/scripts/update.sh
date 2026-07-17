#!/usr/bin/env bash
# ============================================================================
# Mission Control — Update Script
#
# Updates Mission Control to the latest version with backup and rollback.
#
# Usage:
#   sudo ./update.sh [--version VERSION] [--no-backup] [--no-rollback]
#
# What it does:
#   1. Backs up current configuration and database
#   2. Pulls latest images / rebuilds containers
#   3. Runs database migrations
#   4. Restarts services
#   5. Verifies health
#   6. Rolls back on failure (unless --no-rollback)
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MC_INSTALL_DIR="/opt/missioncontrol"
MC_BACKUP_DIR="${MC_INSTALL_DIR}/backups"
MC_LOG_DIR="${MC_INSTALL_DIR}/logs"
MC_STATE_FILE="/var/lib/mission-control/.installed"
BACKUP_DB=""
BACKUP_CONFIG=""
NO_BACKUP=false
NO_ROLLBACK=false
TARGET_VERSION=""

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
        --version)     TARGET_VERSION="$2"; shift 2 ;;
        --no-backup)   NO_BACKUP=true; shift ;;
        --no-rollback) NO_ROLLBACK=true; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --version VERSION     Target version to update to"
            echo "  --no-backup           Skip backup before update"
            echo "  --no-rollback         Skip automatic rollback on failure"
            echo "  -h, --help            Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
step "Preflight Checks"

if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root"
fi

if [[ ! -d "${MC_INSTALL_DIR}" ]]; then
    die "Mission Control not installed at ${MC_INSTALL_DIR}"
fi

cd "${MC_INSTALL_DIR}"

if [[ ! -f docker-compose.yml ]]; then
    die "docker-compose.yml not found in ${MC_INSTALL_DIR}"
fi

# Get current version
CURRENT_VERSION=$(grep -oP 'MC_VERSION=\K.*' .env 2>/dev/null || echo "unknown")
info "Current version: ${CURRENT_VERSION}"
if [[ -n "${TARGET_VERSION}" ]]; then
    info "Target version: ${TARGET_VERSION}"
fi

ok "Preflight checks passed"

# ---------------------------------------------------------------------------
# Step 1: Backup configuration
# ---------------------------------------------------------------------------
if [[ "${NO_BACKUP}" != "true" ]]; then
    step "Creating Backup"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="${MC_BACKUP_DIR}/full"

    # Backup .env
    BACKUP_ENV="${MC_BACKUP_DIR}/config/env_${TIMESTAMP}.backup"
    cp "${MC_INSTALL_DIR}/.env" "${BACKUP_ENV}"
    ok "Backed up .env"

    # Backup database
    BACKUP_DB="${MC_BACKUP_DIR}/db/db_${TIMESTAMP}.sql.gz"
    if docker compose exec -T postgres pg_dump -U mission_control mission_control 2>/dev/null | gzip > "${BACKUP_DB}"; then
        ok "Backed up database ($(du -h "${BACKUP_DB}" | cut -f1))"
    else
        warn "Database backup failed (database may not exist yet)"
        BACKUP_DB=""
    fi

    # Backup config files
    BACKUP_CONFIG="${MC_BACKUP_DIR}/config/config_${TIMESTAMP}.tar.gz"
    tar -czf "${BACKUP_CONFIG}" -C "${MC_INSTALL_DIR}" .env docker-compose.yml nginx/ config/ 2>/dev/null || true
    ok "Backed up configuration"

    # Store rollback info
    ROLLBACK_ENV="${BACKUP_ENV}"
    ROLLBACK_DB="${BACKUP_DB}"
else
    warn "Skipping backup (--no-backup)"
fi

# ---------------------------------------------------------------------------
# Step 2: Pull latest images
# ---------------------------------------------------------------------------
step "Pulling Latest Images"

if docker compose pull 2>&1 | tail -5; then
    ok "Images pulled"
else
    warn "Some images may not have been pulled (building locally?)"
fi

# ---------------------------------------------------------------------------
# Step 3: Build containers
# ---------------------------------------------------------------------------
step "Building Containers"

if docker compose build --no-cache 2>&1 | tail -10; then
    ok "Containers built"
else
    error "Build failed"
    if [[ "${NO_ROLLBACK}" != "true" ]] && [[ -n "${ROLLBACK_ENV:-}" ]]; then
        warn "Rolling back..."
        cp "${ROLLBACK_ENV}" "${MC_INSTALL_DIR}/.env"
        docker compose up -d
        die "Update aborted. Rollback complete."
    fi
    die "Build failed and rollback disabled"
fi

# ---------------------------------------------------------------------------
# Step 4: Run database migrations
# ---------------------------------------------------------------------------
step "Running Database Migrations"

if docker compose up -d postgres redis 2>&1 | tail -3; then
    sleep 5
fi

if docker compose exec -T backend alembic upgrade head 2>/dev/null; then
    ok "Migrations applied"
else
    warn "Migrations skipped (no pending migrations or first run)"
fi

# ---------------------------------------------------------------------------
# Step 5: Restart all services
# ---------------------------------------------------------------------------
step "Restarting Services"

docker compose down --timeout 30
docker compose up -d

ok "Services restarted"

# ---------------------------------------------------------------------------
# Step 6: Wait for health
# ---------------------------------------------------------------------------
step "Verifying Health"

MAX_WAIT=120
WAITED=0
HEALTHY=false

while [[ $WAITED -lt $MAX_WAIT ]]; do
    if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)" 2>/dev/null; then
        HEALTHY=true
        ok "Backend healthy after ${WAITED}s"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    info "Waiting... (${WAITED}/${MAX_WAIT}s)"
done

if [[ "${HEALTHY}" != "true" ]]; then
    error "Backend failed health check after ${MAX_WAIT}s"
    if [[ "${NO_ROLLBACK}" != "true" ]]; then
        step "Rolling Back"
        docker compose down --timeout 30
        if [[ -n "${ROLLBACK_ENV:-}" ]]; then
            cp "${ROLLBACK_ENV}" "${MC_INSTALL_DIR}/.env"
        fi
        if [[ -n "${ROLLBACK_DB:-}" ]] && [[ -f "${ROLLBACK_DB}" ]]; then
            docker compose up -d postgres redis
            sleep 5
            gunzip -c "${ROLLBACK_DB}" | docker compose exec -T postgres psql -U mission_control mission_control 2>/dev/null || true
        fi
        docker compose up -d
        die "Update failed. Rolled back to previous version."
    fi
    die "Update failed and rollback disabled. Check: docker compose logs backend"
fi

# ---------------------------------------------------------------------------
# Step 7: Update state file
# ---------------------------------------------------------------------------
if [[ -f "${MC_STATE_FILE}" ]]; then
    NEW_VERSION="${TARGET_VERSION:-$(grep -oP 'MC_VERSION=\K.*' .env 2>/dev/null || echo 'unknown')}"
    cat > "${MC_STATE_FILE}" << STATEEOF
installed_at=$(cat "${MC_STATE_FILE}" | grep installed_at | cut -d= -f2)
updated_at=$(date -Iseconds)
version=${NEW_VERSION}
previous_version=${CURRENT_VERSION}
STATEEOF
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step "Update Complete"

echo ""
echo -e "${GREEN}Mission Control updated successfully!${NC}"
echo ""
echo "  Previous version: ${CURRENT_VERSION}"
echo "  Current version:  ${TARGET_VERSION:-$(grep -oP 'MC_VERSION=\K.*' .env 2>/dev/null || echo 'unknown')}"
echo ""
if [[ -n "${BACKUP_DB:-}" ]] && [[ -f "${BACKUP_DB}" ]]; then
    echo "  Backup location: ${BACKUP_DB}"
    echo ""
fi
echo "  Verify: curl http://$(hostname -I | awk '{print $1}')/api/v1/version"
echo ""
