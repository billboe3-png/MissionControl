#!/usr/bin/env bash
# ============================================================================
# Mission Control — Backup Script
#
# Creates timestamped backups of database, configuration, plugins, playbooks,
# automation, and logs. Compresses everything into a single archive.
#
# Usage:
#   sudo ./backup.sh [--output-dir DIR] [--full] [--no-db]
#
# Backups are stored in /opt/missioncontrol/backups/
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MC_INSTALL_DIR="/opt/missioncontrol"
MC_BACKUP_DIR="${MC_INSTALL_DIR}/backups"
MC_LOG_DIR="${MC_INSTALL_DIR}/logs/backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR=""
FULL_BACKUP=false
NO_DB=false

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
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --full)       FULL_BACKUP=true; shift ;;
        --no-db)      NO_DB=true; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --output-dir DIR  Custom output directory"
            echo "  --full            Include full system backup"
            echo "  --no-db           Skip database backup"
            echo "  -h, --help        Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root"
fi

BACKUP_BASE="${OUTPUT_DIR:-${MC_BACKUP_DIR}}"
BACKUP_NAME="missioncontrol_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_BASE}/${BACKUP_NAME}"
LOG_FILE="${MC_LOG_DIR}/backup_${TIMESTAMP}.log"

mkdir -p "${BACKUP_BASE}"
mkdir -p "${MC_LOG_DIR}"
mkdir -p "${BACKUP_PATH}/db"
mkdir -p "${BACKUP_PATH}/config"
mkdir -p "${BACKUP_PATH}/plugins"
mkdir -p "${BACKUP_PATH}/playbooks"
mkdir -p "${BACKUP_PATH}/automation"
mkdir -p "${BACKUP_PATH}/logs"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"
}

# ---------------------------------------------------------------------------
# Step 1: Backup database
# ---------------------------------------------------------------------------
step "Database Backup"

if [[ "${NO_DB}" != "true" ]]; then
    cd "${MC_INSTALL_DIR}"

    if docker compose exec -T postgres pg_dump -U mission_control mission_control 2>/dev/null | gzip > "${BACKUP_PATH}/db/missioncontrol.sql.gz"; then
        DB_SIZE=$(du -h "${BACKUP_PATH}/db/missioncontrol.sql.gz" | cut -f1)
        ok "Database backed up (${DB_SIZE})"
        log "Database backup: ${DB_SIZE}"
    else
        warn "Database backup failed (database may not be running or doesn't exist)"
        log "WARNING: Database backup failed"
    fi
else
    info "Skipping database backup (--no-db)"
fi

# ---------------------------------------------------------------------------
# Step 2: Backup configuration
# ---------------------------------------------------------------------------
step "Configuration Backup"

# Environment file
if [[ -f "${MC_INSTALL_DIR}/.env" ]]; then
    cp "${MC_INSTALL_DIR}/.env" "${BACKUP_PATH}/config/env.backup"
    ok "Environment file backed up"
    log "Environment file backed up"
fi

# Docker Compose file
if [[ -f "${MC_INSTALL_DIR}/docker-compose.yml" ]]; then
    cp "${MC_INSTALL_DIR}/docker-compose.yml" "${BACKUP_PATH}/config/docker-compose.yml.backup"
    ok "Docker Compose file backed up"
fi

# Nginx configuration
if [[ -d "${MC_INSTALL_DIR}/nginx" ]]; then
    cp -r "${MC_INSTALL_DIR}/nginx" "${BACKUP_PATH}/config/nginx"
    ok "Nginx configuration backed up"
fi

# Application config directory
if [[ -d "${MC_INSTALL_DIR}/config" ]]; then
    cp -r "${MC_INSTALL_DIR}/config" "${BACKUP_PATH}/config/app"
    ok "Application configuration backed up"
fi

# ---------------------------------------------------------------------------
# Step 3: Backup plugins
# ---------------------------------------------------------------------------
step "Plugin Backup"

if [[ -d "${MC_INSTALL_DIR}/plugins" ]] && [[ -n "$(ls -A "${MC_INSTALL_DIR}/plugins" 2>/dev/null)" ]]; then
    cp -r "${MC_INSTALL_DIR}/plugins" "${BACKUP_PATH}/plugins"
    ok "Plugins backed up"
    log "Plugins backed up"
else
    info "No plugins to backup"
fi

# ---------------------------------------------------------------------------
# Step 4: Backup playbooks
# ---------------------------------------------------------------------------
step "Playbook Backup"

if [[ -d "${MC_INSTALL_DIR}/playbooks" ]] && [[ -n "$(ls -A "${MC_INSTALL_DIR}/playbooks" 2>/dev/null)" ]]; then
    cp -r "${MC_INSTALL_DIR}/playbooks" "${BACKUP_PATH}/playbooks"
    ok "Playbooks backed up"
    log "Playbooks backed up"
else
    info "No playbooks to backup"
fi

# ---------------------------------------------------------------------------
# Step 5: Backup automation
# ---------------------------------------------------------------------------
step "Automation Backup"

if [[ -d "${MC_INSTALL_DIR}/automation" ]] && [[ -n "$(ls -A "${MC_INSTALL_DIR}/automation" 2>/dev/null)" ]]; then
    cp -r "${MC_INSTALL_DIR}/automation" "${BACKUP_PATH}/automation"
    ok "Automation configs backed up"
    log "Automation configs backed up"
else
    info "No automation configs to backup"
fi

# ---------------------------------------------------------------------------
# Step 6: Backup logs
# ---------------------------------------------------------------------------
step "Log Backup"

if [[ -d "${MC_INSTALL_DIR}/logs" ]]; then
    find "${MC_INSTALL_DIR}/logs" -type f -name "*.log" -exec cp {} "${BACKUP_PATH}/logs/" \; 2>/dev/null || true
    ok "Logs backed up"
    log "Logs backed up"
else
    info "No logs to backup"
fi

# ---------------------------------------------------------------------------
# Step 7: Full system backup
# ---------------------------------------------------------------------------
if [[ "${FULL_BACKUP}" == "true" ]]; then
    step "Full System Backup"

    # Backup Docker volumes
    info "Backing up PostgreSQL volume..."
    docker run --rm \
        -v missioncontrol_postgres_data:/data:ro \
        -v "${BACKUP_PATH}/db:/backup" \
        alpine tar -czf /backup/postgres_volume.tar.gz -C /data . 2>/dev/null \
        && ok "PostgreSQL volume backed up" \
        || warn "PostgreSQL volume backup failed"

    info "Backing up Redis volume..."
    docker run --rm \
        -v missioncontrol_redis_data:/data:ro \
        -v "${BACKUP_PATH}/db:/backup" \
        alpine tar -czf /backup/redis_volume.tar.gz -C /data . 2>/dev/null \
        && ok "Redis volume backed up" \
        || warn "Redis volume backup failed"
fi

# ---------------------------------------------------------------------------
# Step 8: Create compressed archive
# ---------------------------------------------------------------------------
step "Creating Compressed Archive"

ARCHIVE_NAME="${BACKUP_NAME}.tar.gz"
ARCHIVE_PATH="${BACKUP_BASE}/${ARCHIVE_NAME}"

tar -czf "${ARCHIVE_PATH}" -C "${BACKUP_BASE}" "${BACKUP_NAME}"

# Calculate sizes
ARCHIVE_SIZE=$(du -h "${ARCHIVE_PATH}" | cut -f1)
BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)

ok "Archive created: ${ARCHIVE_PATH} (${ARCHIVE_SIZE})"

# Remove uncompressed directory
rm -rf "${BACKUP_PATH}"

# ---------------------------------------------------------------------------
# Step 9: Cleanup old backups (keep last 10)
# ---------------------------------------------------------------------------
step "Cleaning Old Backups"

BACKUP_COUNT=$(ls -1 "${BACKUP_BASE}"/missioncontrol_*.tar.gz 2>/dev/null | wc -l)
if [[ $BACKUP_COUNT -gt 10 ]]; then
    REMOVE_COUNT=$((BACKUP_COUNT - 10))
    ls -1t "${BACKUP_BASE}"/missioncontrol_*.tar.gz | tail -n "${REMOVE_COUNT}" | xargs rm -f
    ok "Removed ${REMOVE_COUNT} old backup(s)"
    log "Removed ${REMOVE_COUNT} old backup(s)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step "Backup Complete"

echo ""
echo -e "${GREEN}Backup created successfully!${NC}"
echo ""
echo "  Archive:    ${ARCHIVE_PATH}"
echo "  Size:       ${ARCHIVE_SIZE}"
echo "  Timestamp:  ${TIMESTAMP}"
echo ""
echo "  Contents:"
[[ "${NO_DB}" != "true" ]] && echo "    - Database"
echo "    - Configuration"
echo "    - Plugins"
echo "    - Playbooks"
echo "    - Automation"
echo "    - Logs"
[[ "${FULL_BACKUP}" == "true" ]] && echo "    - Docker volumes"
echo ""
echo "  Restore: sudo ./restore.sh ${ARCHIVE_PATH}"
echo ""
log "Backup complete: ${ARCHIVE_PATH} (${ARCHIVE_SIZE})"
