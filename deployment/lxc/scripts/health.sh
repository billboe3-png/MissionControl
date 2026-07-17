#!/usr/bin/env bash
# ============================================================================
# Mission Control — Health Check Script
#
# Comprehensive health verification for all Mission Control services.
#
# Usage:
#   ./health.sh [--status-only] [--json] [--quiet]
#
# Checks: Docker, Compose, Containers, Database, Redis, API, Frontend,
#         Nginx, Plugins, Disk, Memory, CPU, Network
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MC_INSTALL_DIR="/opt/missioncontrol"
STATUS_ONLY=false
JSON_OUTPUT=false
QUIET=false
TOTAL=0
PASSED=0
FAILED=0
WARNED=0

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { [[ "${QUIET}" != "true" ]] && echo -e "${BLUE}[INFO]${NC}  $*" || true; }
ok()    { echo -e "${GREEN}[PASS]${NC} $*"; PASSED=$((PASSED + 1)); TOTAL=$((TOTAL + 1)); }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; WARNED=$((WARNED + 1)); TOTAL=$((TOTAL + 1)); }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; FAILED=$((FAILED + 1)); TOTAL=$((TOTAL + 1)); }
step()  { [[ "${QUIET}" != "true" ]] && echo -e "\n${CYAN}━━━ $* ━━━${NC}" || true; }

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --status-only) STATUS_ONLY=true; shift ;;
        --json)        JSON_OUTPUT=true; shift ;;
        --quiet)       QUIET=true; shift ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --status-only   Show container status only"
            echo "  --json          Output results as JSON"
            echo "  --quiet         Suppress output, exit code reflects result"
            echo "  -h, --help      Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Status-only mode
# ---------------------------------------------------------------------------
if [[ "${STATUS_ONLY}" == "true" ]]; then
    cd "${MC_INSTALL_DIR}" 2>/dev/null || { echo "Install dir not found"; exit 1; }
    docker compose ps
    exit 0
fi

# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
step "Infrastructure"

# Check Docker
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        ok "Docker daemon running"
    else
        fail "Docker daemon not responding"
    fi
else
    fail "Docker not installed"
fi

# Check Docker Compose
if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose available"
else
    fail "Docker Compose not available"
fi

step "Containers"

cd "${MC_INSTALL_DIR}" 2>/dev/null || { fail "Install dir not accessible"; exit 1; }

for service in backend frontend nginx postgres redis; do
    STATUS=$(docker compose ps --format json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        s = json.loads(line)
        if s.get('Service') == '${service}':
            print(s.get('State', 'unknown'))
            break
    except: pass
print('not found')
" 2>/dev/null || echo "not found")

    case "$STATUS" in
        running) ok "Container ${service} running" ;;
        exited)  fail "Container ${service} stopped" ;;
        *)       fail "Container ${service} not found" ;;
    esac
done

step "Services"

# Database (PostgreSQL)
if docker compose exec -T postgres pg_isready -U mission_control -d mission_control 2>/dev/null; then
    ok "PostgreSQL accepting connections"
else
    fail "PostgreSQL not ready"
fi

# Redis
if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    ok "Redis responding (PONG)"
else
    fail "Redis not responding"
fi

# Backend API
if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)" 2>/dev/null; then
    ok "Backend API live"
else
    fail "Backend API not responding"
fi

# Backend readiness (checks DB + Redis)
if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=2)" 2>/dev/null; then
    ok "Backend ready (DB + Redis connected)"
else
    warn "Backend readiness check failed"
fi

# Frontend
if docker compose exec -T frontend wget -q -O /dev/null http://127.0.0.1:3000/ 2>/dev/null; then
    ok "Frontend serving"
else
    warn "Frontend not responding"
fi

# Nginx
if docker compose exec -T nginx wget -q -O /dev/null http://127.0.0.1:80/ 2>/dev/null; then
    ok "Nginx proxying"
else
    fail "Nginx not responding"
fi

step "System Resources"

# Disk usage
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [[ $DISK_USAGE -lt 80 ]]; then
    ok "Disk usage: ${DISK_USAGE}%"
elif [[ $DISK_USAGE -lt 90 ]]; then
    warn "Disk usage: ${DISK_USAGE}% (high)"
else
    fail "Disk usage: ${DISK_USAGE}% (critical)"
fi

# Memory usage
MEM_TOTAL=$(free -m | awk '/^Mem:/ {print $2}')
MEM_USED=$(free -m | awk '/^Mem:/ {print $3}')
MEM_PERCENT=$((MEM_USED * 100 / MEM_TOTAL))
if [[ $MEM_PERCENT -lt 80 ]]; then
    ok "Memory usage: ${MEM_PERCENT}% (${MEM_USED}/${MEM_TOTAL} MB)"
elif [[ $MEM_PERCENT -lt 90 ]]; then
    warn "Memory usage: ${MEM_PERCENT}% (${MEM_USED}/${MEM_TOTAL} MB) (high)"
else
    fail "Memory usage: ${MEM_PERCENT}% (${MEM_USED}/${MEM_TOTAL} MB) (critical)"
fi

# CPU load
CPU_LOAD=$(awk '{print $1}' /proc/loadavg)
CPU_COUNT=$(nproc 2>/dev/null || echo 1)
CPU_PERCENT=$(awk "BEGIN {printf \"%.0f\", (${CPU_LOAD} / ${CPU_COUNT}) * 100}")
if [[ $CPU_PERCENT -lt 80 ]]; then
    ok "CPU load: ${CPU_LOAD} (${CPU_PERCENT}% of ${CPU_COUNT} cores)"
elif [[ $CPU_PERCENT -lt 90 ]]; then
    warn "CPU load: ${CPU_LOAD} (${CPU_PERCENT}% of ${CPU_COUNT} cores) (high)"
else
    fail "CPU load: ${CPU_LOAD} (${CPU_PERCENT}% of ${CPU_COUNT} cores) (critical)"
fi

step "Plugins"

# Check plugin directory
PLUGIN_COUNT=$(find "${MC_INSTALL_DIR}/plugins" -maxdepth 1 -type d 2>/dev/null | wc -l)
PLUGIN_COUNT=$((PLUGIN_COUNT - 1))  # Exclude the plugins dir itself
if [[ $PLUGIN_COUNT -gt 0 ]]; then
    ok "${PLUGIN_COUNT} plugin(s) installed"
else
    info "No plugins installed"
fi

step "Network"

# Check external connectivity
if curl -sf --max-time 5 https://registry-1.docker.io/v2/ >/dev/null 2>&1; then
    ok "Docker registry reachable"
else
    warn "Docker registry not reachable (image pulls may fail)"
fi

# Check DNS
if host -W 2 registry-1.docker.io >/dev/null 2>&1 || nslookup registry-1.docker.io >/dev/null 2>&1; then
    ok "DNS resolution working"
else
    warn "DNS resolution may have issues"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step "Summary"

echo ""
if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}All checks passed!${NC} (${PASSED} passed, ${WARNED} warnings)"
else
    echo -e "${RED}${FAILED} check(s) failed${NC} (${PASSED} passed, ${WARNED} warnings)"
fi
echo ""

# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------
if [[ "${JSON_OUTPUT}" == "true" ]]; then
    cat << JSONEOF
{
  "timestamp": "$(date -Iseconds)",
  "total": ${TOTAL},
  "passed": ${PASSED},
  "failed": ${FAILED},
  "warned": ${WARNED},
  "healthy": $([[ $FAILED -eq 0 ]] && echo "true" || echo "false")
}
JSONEOF
fi

# Exit code
exit $FAILED
