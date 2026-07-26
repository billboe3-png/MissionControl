#!/usr/bin/env bash
# =============================================================================
# Mission Control — Installation Validation Script (Linux/Docker)
#
# Validates a clean installation on Ubuntu, Debian, or Docker Desktop.
# Run this after deployment to verify everything is working.
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

echo ""
echo "  Mission Control — Installation Validation"
echo "  ─────────────────────────────────────────"
echo ""

# ------------------------------------------------------------------ #
# 1. Docker                                                            #
# ------------------------------------------------------------------ #

echo "  Docker"
if command -v docker &>/dev/null; then
    pass "Docker installed: $(docker --version)"
else
    fail "Docker not found"
fi

if command -v docker-compose &>/dev/null || docker compose version &>/dev/null 2>&1; then
    pass "Docker Compose available"
else
    fail "Docker Compose not found"
fi

# ------------------------------------------------------------------ #
# 2. Docker Services                                                   #
# ------------------------------------------------------------------ #

echo ""
echo "  Docker Services"

if docker compose ps 2>/dev/null | grep -q "postgres.*running"; then
    pass "PostgreSQL container running"
else
    warn "PostgreSQL container not running (check docker compose ps)"
fi

if docker compose ps 2>/dev/null | grep -q "redis.*running"; then
    pass "Redis container running"
else
    warn "Redis container not running (check docker compose ps)"
fi

if docker compose ps 2>/dev/null | grep -q "backend.*running"; then
    pass "Backend container running"
else
    warn "Backend container not running (check docker compose ps)"
fi

if docker compose ps 2>/dev/null | grep -q "frontend.*running"; then
    pass "Frontend container running"
else
    warn "Frontend container not running (check docker compose ps)"
fi

# ------------------------------------------------------------------ #
# 3. Configuration                                                     #
# ------------------------------------------------------------------ #

echo ""
echo "  Configuration"

if [ -f ".env" ]; then
    pass ".env file exists"
else
    fail ".env file not found"
fi

if [ -f ".env" ] && grep -q "MISSIONCONTROL_SECRET_KEY" .env && ! grep -q "MISSIONCONTROL_SECRET_KEY=$" .env && ! grep -q 'MISSIONCONTROL_SECRET_KEY=""' .env; then
    pass "MISSIONCONTROL_SECRET_KEY is set"
elif [ -f ".env" ]; then
    fail "MISSIONCONTROL_SECRET_KEY is missing or empty in .env"
fi

if [ -f ".env" ] && grep -q "POSTGRES_PASSWORD" .env; then
    pass "POSTGRES_PASSWORD is set"
elif [ -f ".env" ]; then
    warn "POSTGRES_PASSWORD not set in .env"
fi

# ------------------------------------------------------------------ #
# 4. Health Endpoints                                                  #
# ------------------------------------------------------------------ #

echo ""
echo "  Health Endpoints"

BACKEND_PORT="${BACKEND_PORT:-8000}"
API_URL="http://localhost:${BACKEND_PORT}"

if curl -sf "${API_URL}/api/v1/health/live" >/dev/null 2>&1; then
    pass "Liveness endpoint responding"
else
    warn "Liveness endpoint not reachable (backend may not be started)"
fi

if curl -sf "${API_URL}/api/v1/health/ready" >/dev/null 2>&1; then
    pass "Readiness endpoint responding"
else
    warn "Readiness endpoint not reachable"
fi

if curl -sf "${API_URL}/api/v1/health/subsystems" >/dev/null 2>&1; then
    pass "Subsystem health endpoint responding"
else
    warn "Subsystem health endpoint not reachable"
fi

if curl -sf "${API_URL}/api/v1/version" >/dev/null 2>&1; then
    VERSION=$(curl -sf "${API_URL}/api/v1/version" | grep -o '"version":"[^"]*"' | head -1 | cut -d'"' -f4)
    pass "Version endpoint responding: ${VERSION:-unknown}"
else
    warn "Version endpoint not reachable"
fi

# ------------------------------------------------------------------ #
# 5. Frontend                                                          #
# ------------------------------------------------------------------ #

echo ""
echo "  Frontend"

FRONTEND_PORT="${FRONTEND_PORT:-3000}"

if curl -sf "http://localhost:${FRONTEND_PORT}" >/dev/null 2>&1; then
    pass "Frontend serving on port ${FRONTEND_PORT}"
else
    warn "Frontend not reachable on port ${FRONTEND_PORT}"
fi

# ------------------------------------------------------------------ #
# 6. Database                                                          #
# ------------------------------------------------------------------ #

echo ""
echo "  Database"

if docker compose exec -T postgres pg_isready -U missioncontrol 2>/dev/null; then
    pass "PostgreSQL is accepting connections"
else
    warn "PostgreSQL connection test failed"
fi

TABLE_COUNT=$(docker compose exec -T postgres psql -U missioncontrol -d mission_control -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null | tr -d ' ')
if [ -n "$TABLE_COUNT" ] && [ "$TABLE_COUNT" -gt 10 ]; then
    pass "Database has ${TABLE_COUNT} tables"
else
    warn "Database table count unknown (${TABLE_COUNT:-0})"
fi

# ------------------------------------------------------------------ #
# 7. Redis                                                             #
# ------------------------------------------------------------------ #

echo ""
echo "  Redis"

if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    pass "Redis is responding to PING"
else
    warn "Redis PING failed"
fi

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
