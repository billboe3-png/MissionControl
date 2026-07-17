#!/usr/bin/env bash
# ============================================================================
# Mission Control — Restore Script
#
# Restores Mission Control from a backup archive created by backup.sh.
#
# Usage:
#   sudo ./restore.sh <backup-archive.tar.gz> [--no-db] [--no-confirm]
#
# WARNING: This will overwrite current configuration and data.
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MC_INSTALL_DIR="/opt/missioncontrol"
MC_BACKUP_DIR="${MC_INSTALL_DIR}/backups"
MC_STATE_FILE="/var/lib/mission-control/.initialized"
NO_DB=false
NO_CONFIRM=false
BACKUP_ARCHIVE=""

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
        --no-db)      NO_DB=true; shift ;;
        --no-confirm) NO_CONFIRM=true; shift ;;
        --help|-h)
            echo "Usage: $0 <backup-archive.tar.gz> [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-db       Skip database restore"
            echo "  --no-confirm  Skip confirmation prompt"
            echo "  -h, --help    Show this help"
            exit 0
            ;;
        -*) die "Unknown option: $1" ;;
        *)  BACKUP_ARCHIVE="$1"; shift ;;
    esac
done

# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------
if [[ -z "${BACKUP_ARCHIVE}" ]]; then
    die "Usage: $0 <backup-archive.tar.gz> [--no-db] [--no-confirm]"
fi

if [[ ! -f "${BACKUP_ARCHIVE}" ]]; then
    die "Backup archive not found: ${BACKUP_ARCHIVE}"
fi

if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root"
fi

if [[ ! -d "${MC_INSTALL_DIR}" ]]; then
    die "Mission Control not installed at ${MC_INSTALL_DIR}"
fi

# ---------------------------------------------------------------------------
# Confirmation
# ---------------------------------------------------------------------------
if [[ "${NO_CONFIRM}" != "true" ]]; then
    echo ""
    echo -e "${RED}WARNING: This will overwrite current Mission Control data!${NC}"
    echo ""
    echo "  Backup archive: ${BACKUP_ARCHIVE}"
    echo "  Install dir:    ${MC_INSTALL_DIR}"
    echo ""
    read -p "Continue? (yes/no): " CONFIRM
    if [[ "${CONFIRM}" != "yes" ]]; then
        info "Restore cancelled"
        exit 0
    fi
fi

# ---------------------------------------------------------------------------
# Step 1: Extract backup
# ---------------------------------------------------------------------------
step "Extracting Backup"

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "${TEMP_DIR}"' EXIT

tar -xzf "${BACKUP_ARCHIVE}" -C "${TEMP_DIR}"

# Find the extracted backup directory
BACKUP_DIR=$(find "${TEMP_DIR}" -maxdepth 1 -type d -name "missioncontrol_*" | head -1)
if [[ -z "${BACKUP_DIR}" ]]; then
    die "Invalid backup archive structure"
fi

ok "Backup extracted"

# ---------------------------------------------------------------------------
# Step 2: Stop services
# ---------------------------------------------------------------------------
step "Stopping Services"

cd "${MC_INSTALL_DIR}"
docker compose down --timeout 30 2>/dev/null || true

ok "Services stopped"

# ---------------------------------------------------------------------------
# Step 3: Restore configuration
# ---------------------------------------------------------------------------
step "Restoring Configuration"

# Restore .env
if [[ -f "${BACKUP_DIR}/config/env.backup" ]]; then
    cp "${BACKUP_DIR}/config/env.backup" "${MC_INSTALL_DIR}/.env"
    chmod 600 "${MC_INSTALL_DIR}/.env"
    ok "Environment file restored"
fi

# Restore docker-compose.yml
if [[ -f "${BACKUP_DIR}/config/docker-compose.yml.backup" ]]; then
    cp "${BACKUP_DIR}/config/docker-compose.yml.backup" "${MC_INSTALL_DIR}/docker-compose.yml"
    ok "Docker Compose file restored"
fi

# Restore nginx configuration
if [[ -d "${BACKUP_DIR}/config/nginx" ]]; then
    rm -rf "${MC_INSTALL_DIR}/nginx"
    cp -r "${BACKUP_DIR}/config/nginx" "${MC_INSTALL_DIR}/nginx"
    ok "Nginx configuration restored"
fi

# Restore application configuration
if [[ -d "${BACKUP_DIR}/config/app" ]]; then
    rm -rf "${MC_INSTALL_DIR}/config"
    cp -r "${BACKUP_DIR}/config/app" "${MC_INSTALL_DIR}/config"
    ok "Application configuration restored"
fi

# ---------------------------------------------------------------------------
# Step 4: Restore plugins
# ---------------------------------------------------------------------------
step "Restoring Plugins"

if [[ -d "${BACKUP_DIR}/plugins" ]] && [[ -n "$(ls -A "${BACKUP_DIR}/plugins" 2>/dev/null)" ]]; then
    rm -rf "${MC_INSTALL_DIR}/plugins"
    cp -r "${BACKUP_DIR}/plugins" "${MC_INSTALL_DIR}/plugins"
    ok "Plugins restored"
else
    info "No plugins in backup"
fi

# ---------------------------------------------------------------------------
# Step 5: Restore playbooks
# ---------------------------------------------------------------------------
step "Restoring Playbooks"

if [[ -d "${BACKUP_DIR}/playbooks" ]] && [[ -n "$(ls -A "${BACKUP_DIR}/playbooks" 2>/dev/null)" ]]; then
    rm -rf "${MC_INSTALL_DIR}/playbooks"
    cp -r "${BACKUP_DIR}/playbooks" "${MC_INSTALL_DIR}/playbooks"
    ok "Playbooks restored"
else
    info "No playbooks in backup"
fi

# ---------------------------------------------------------------------------
# Step 6: Restore automation
# ---------------------------------------------------------------------------
step "Restoring Automation"

if [[ -d "${BACKUP_DIR}/automation" ]] && [[ -n "$(ls -A "${BACKUP_DIR}/automation" 2>/dev/null)" ]]; then
    rm -rf "${MC_INSTALL_DIR}/automation"
    cp -r "${BACKUP_DIR}/automation" "${MC_INSTALL_DIR}/automation"
    ok "Automation configs restored"
else
    info "No automation configs in backup"
fi

# ---------------------------------------------------------------------------
# Step 7: Restore database
# ---------------------------------------------------------------------------
if [[ "${NO_DB}" != "true" ]]; then
    step "Restoring Database"

    DB_BACKUP="${BACKUP_DIR}/db/missioncontrol.sql.gz"
    if [[ -f "${DB_BACKUP}" ]]; then
        info "Starting database containers..."
        docker compose up -d postgres redis
        sleep 10

        info "Restoring database..."
        if gunzip -c "${DB_BACKUP}" | docker compose exec -T postgres psql -U mission_control mission_control 2>/dev/null; then
            ok "Database restored"
        else
            warn "Database restore encountered errors (database may need manual intervention)"
        fi
    else
        warn "No database backup found in archive"
    fi
else
    info "Skipping database restore (--no-db)"
fi

# ---------------------------------------------------------------------------
# Step 8: Start services
# ---------------------------------------------------------------------------
step "Starting Services"

docker compose up -d

ok "Services started"

# ---------------------------------------------------------------------------
# Step 9: Verify health
# ---------------------------------------------------------------------------
step "Verifying Health"

MAX_WAIT=120
WAITED=0

while [[ $WAITED -lt $MAX_WAIT ]]; do
    if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)" 2>/dev/null; then
        ok "Backend healthy after ${WAITED}s"
        break
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    info "Waiting... (${WAITED}/${MAX_WAIT}s)"
done

if [[ $WAITED -ge $MAX_WAIT ]]; then
    warn "Health check timed out. Check: docker compose logs backend"
fi

# ---------------------------------------------------------------------------
# Step 10: Reset first-boot marker
# ---------------------------------------------------------------------------
step "Resetting First-Boot Marker"

if [[ -f "${MC_STATE_FILE}" ]]; then
    rm -f "${MC_STATE_FILE}"
    ok "First-boot marker removed (will re-initialize on next boot if needed)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step "Restore Complete"

echo ""
echo -e "${GREEN}Mission Control restored successfully!${NC}"
echo ""
echo "  Restored from: ${BACKUP_ARCHIVE}"
echo ""
echo "  Verify: curl http://$(hostname -I | awk '{print $1}')/api/v1/version"
echo ""
