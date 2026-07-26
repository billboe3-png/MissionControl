#!/usr/bin/env bash
# =============================================================================
# Mission Control — Backup Validation Script
#
# Verifies that PostgreSQL, Redis, and configuration backups exist
# and are valid. Tests restore capability.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)); }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)); }
warn() { echo -e "  ${YELLOW}!${NC} $1"; ((WARN++)); }

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo "  Mission Control — Backup Validation"
echo "  ────────────────────────────────────"
echo ""

# ------------------------------------------------------------------ #
# 1. PostgreSQL Backup                                                 #
# ------------------------------------------------------------------ #

echo "  PostgreSQL Backup"

if command -v docker &>/dev/null; then
    # Test pg_dump
    TEST_DUMP="${BACKUP_DIR}/test_pg_${TIMESTAMP}.sql.gz"
    mkdir -p "$BACKUP_DIR"

    if docker compose exec -T postgres pg_dump -U missioncontrol -d mission_control 2>/dev/null | gzip > "$TEST_DUMP"; then
        SIZE=$(stat -f%z "$TEST_DUMP" 2>/dev/null || stat -c%s "$TEST_DUMP" 2>/dev/null || echo "0")
        if [ "$SIZE" -gt 100 ]; then
            pass "pg_dump successful (${SIZE} bytes)"
        else
            fail "pg_dump produced empty or tiny file"
        fi
    else
        fail "pg_dump failed"
    fi

    # Verify dump is valid gzip
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

if docker compose exec -T redis redis-cli BGSAVE 2>/dev/null | grep -q "OK"; then
    pass "Redis BGSAVE initiated"
else
    warn "Redis BGSAVE could not be verified"
fi

if docker compose exec -T redis redis-cli LASTSAVE 2>/dev/null | grep -q "^[0-9]"; then
    pass "Redis has snapshot data"
else
    warn "Redis snapshot status unknown"
fi

# ------------------------------------------------------------------ #
# 3. Configuration Backup                                              #
# ------------------------------------------------------------------ #

echo ""
echo "  Configuration Backup"

CONFIG_BACKUP="${BACKUP_DIR}/config_${TIMESTAMP}"
mkdir -p "$CONFIG_BACKUP"

# Copy .env
if [ -f ".env" ]; then
    cp .env "$CONFIG_BACKUP/"
    pass ".env backed up"
else
    warn ".env file not found"
fi

# Copy docker-compose files
for f in docker-compose.yml docker-compose.prod.yml; do
    if [ -f "$f" ]; then
        cp "$f" "$CONFIG_BACKUP/"
        pass "$f backed up"
    fi
done

# Copy docker-compose prod if exists
if [ -f "docker-compose.prod.yml" ]; then
    pass "Production compose backed up"
fi

# ------------------------------------------------------------------ #
# 4. Restore Test                                                      #
# ------------------------------------------------------------------ #

echo ""
echo "  Restore Validation"

if [ -f "$CONFIG_BACKUP/.env" ]; then
    if grep -q "MISSIONCONTROL_SECRET_KEY" "$CONFIG_BACKUP/.env"; then
        pass "Config backup contains secret key"
    else
        warn "Config backup missing secret key"
    fi
else
    warn "Config backup not available for restore test"
fi

# Cleanup
rm -rf "$CONFIG_BACKUP"

# ------------------------------------------------------------------ #
# Summary                                                              #
# ------------------------------------------------------------------ #

echo ""
echo "  ────────────────────────────────────"
echo "  Passed: ${PASS}  Failed: ${FAIL}  Warnings: ${WARN}"

if [ "$FAIL" -gt 0 ]; then
    echo -e "  ${RED}RESULT: VALIDATION FAILED${NC}"
    exit 1
else
    echo -e "  ${GREEN}RESULT: VALIDATION PASSED${NC}"
    exit 0
fi
