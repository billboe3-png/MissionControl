#!/usr/bin/env bash
# =============================================================================
# Mission Control — Environment Backup Validation
#
# Verifies backups for a specific environment: DEV or LIVE.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 -e <dev|live> [-d backup_dir]"
    exit 1
}

ENV=""
BACKUP_DIR="./backups"

while getopts "e:d:" opt; do
    case "$opt" in
        e) ENV="$OPTARG" ;;
        d) BACKUP_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

if [[ "$ENV" != "dev" && "$ENV" != "live" ]]; then
    usage
fi

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)); }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)); }
warn() { echo -e "  ${YELLOW}!${NC} $1"; ((WARN++)); }

echo ""
echo "  Mission Control — $ENV Backup Validation"
echo "  ─────────────────────────────────────────"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_DUMP="${BACKUP_DIR}/test_pg_${ENV}_${TIMESTAMP}.sql.gz"
CONFIG_SRC=""
CONFIG_DST="${BACKUP_DIR}/config_${ENV}_${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"

if [[ "$ENV" == "live" ]]; then
    COMPOSE_PROJECT="missioncontrol-live"
    DB="missioncontrol_live"
    CONFIG_SRC=".env.production"
else
    COMPOSE_PROJECT="missioncontrol-dev"
    DB="missioncontrol_dev"
    CONFIG_SRC=".env.dev"
fi

# ------------------------------------------------------------------ #
# 1. PostgreSQL Backup                                                 #
# ------------------------------------------------------------------ #

echo ""
echo "  PostgreSQL Backup"

if command -v docker &>/dev/null; then
    if docker compose \
      --project-name "$COMPOSE_PROJECT" \
      exec -T postgres pg_dump -U "$DB" -d "$DB" 2>/dev/null | gzip > "$TEST_DUMP"; then
        SIZE=$(stat -f%z "$TEST_DUMP" 2>/dev/null || stat -c%s "$TEST_DUMP" 2>/dev/null || echo "0")
        if [ "$SIZE" -gt 100 ]; then
            pass "pg_dump successful for $ENV (${SIZE} bytes)"
        else
            fail "pg_dump produced empty or tiny file"
        fi
    else
        fail "pg_dump failed for $ENV"
    fi

    if gzip -t "$TEST_DUMP" 2>/dev/null; then
        pass "pg_dump file is valid gzip"
    else
        fail "pg_dump file is corrupted"
    fi

    rm -f "$TEST_DUMP"
else
    warn "Docker not available, skipping PostgreSQL backup test"
fi

# ------------------------------------------------------------------ #
# 2. Redis Backup                                                      #
# ------------------------------------------------------------------ #

echo ""
echo "  Redis Backup"

if command -v docker &>/dev/null; then
    if docker compose \
      --project-name "$COMPOSE_PROJECT" \
      exec -T redis redis-cli BGSAVE 2>/dev/null | grep -q "OK"; then
        pass "Redis BGSAVE initiated"
    else
        warn "Redis BGSAVE could not be verified"
    fi

    if docker compose \
      --project-name "$COMPOSE_PROJECT" \
      exec -T redis redis-cli LASTSAVE 2>/dev/null | grep -q "^[0-9]"; then
        pass "Redis has snapshot data"
    else
        warn "Redis snapshot status unknown"
    fi
else
    warn "Docker not available, skipping Redis backup test"
fi

# ------------------------------------------------------------------ #
# 3. Configuration Backup                                              #
# ------------------------------------------------------------------ #

echo ""
echo "  Configuration Backup"

mkdir -p "$CONFIG_DST"

if [ -f "$CONFIG_SRC" ]; then
    cp "$CONFIG_SRC" "$CONFIG_DST/"
    pass "$CONFIG_SRC backed up"
else
    warn "$CONFIG_SRC file not found"
fi

for f in docker-compose.yml docker-compose.dev.yml docker-compose.production.yml; do
    if [ -f "$f" ]; then
        cp "$f" "$CONFIG_DST/"
        pass "$f backed up"
    fi
done

if [ -f "nginx/default.conf" ]; then
    mkdir -p "$CONFIG_DST/nginx"
    cp nginx/default.conf "$CONFIG_DST/nginx/"
    pass "nginx/default.conf backed up"
fi

# ------------------------------------------------------------------ #
# 4. Restore Validation                                                #
# ------------------------------------------------------------------ #

echo ""
echo "  Restore Validation"

if [ -f "$CONFIG_DST/$CONFIG_SRC" ]; then
    if grep -q "MISSIONCONTROL_SECRET_KEY" "$CONFIG_DST/$CONFIG_SRC"; then
        pass "Config backup contains secret key"
    else
        warn "Config backup missing secret key"
    fi
else
    warn "Config backup not available for restore test"
fi

# ------------------------------------------------------------------ #
# Cleanup                                                              #
# ------------------------------------------------------------------ #

rm -rf "$CONFIG_DST"

# ------------------------------------------------------------------ #
# Summary                                                              #
# ------------------------------------------------------------------ #

echo ""
echo "  ─────────────────────────────────────────"
echo "  Passed: ${PASS}  Failed: ${FAIL}  Warnings: ${WARN}"

if [ "$FAIL" -gt 0 ]; then
    echo -e "  ${RED}RESULT: VALIDATION FAILED${NC}"
    exit 1
else
    echo -e "  ${GREEN}RESULT: VALIDATION PASSED${NC}"
    exit 0
fi
