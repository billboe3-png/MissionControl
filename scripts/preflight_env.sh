#!/usr/bin/env bash
# =============================================================================
# Mission Control — Environment Pre-flight Validator
#
# Checks that an environment is correctly isolated and deployable without
# touching live services. Run before any deployment.
# =============================================================================

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo "Usage: $0 -e <dev|live>"
    exit 1
}

ENV=""
while getopts "e:" opt; do
    case "$opt" in
        e) ENV="$OPTARG" ;;
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
echo "  Mission Control — $ENV Pre-flight Validation"
echo "  ─────────────────────────────────────────────────"

# ------------------------------------------------------------------ #
# 1. Git state                                                        #
# ------------------------------------------------------------------ #

echo ""
echo "  Git"

if [[ "$ENV" == "live" ]]; then
    EXPECTED_BRANCH="main"
    EXPECTED_URL="missioncontrol.optichosting.co.za"
else
    EXPECTED_BRANCH="develop"
    EXPECTED_URL="missioncontroldev.optichosting.co.za"
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
if [[ "$CURRENT_BRANCH" == "$EXPECTED_BRANCH" ]]; then
    pass "Branch is $EXPECTED_BRANCH"
else
    fail "Branch is $CURRENT_BRANCH, expected $EXPECTED_BRANCH"
fi

if git diff --quiet 2>/dev/null; then
    pass "Working tree is clean"
else
    warn "Working tree has uncommitted changes"
fi

# ------------------------------------------------------------------ #
# 2. Environment files                                                #
# ------------------------------------------------------------------ #

echo ""
echo "  Environment files"

ENV_FILE=""
if [[ "$ENV" == "live" ]]; then
    ENV_FILE=".env.production"
else
    ENV_FILE=".env.dev"
fi

if [[ -f "$ENV_FILE" ]]; then
    pass "$ENV_FILE exists"

    if grep -q "CHANGE_ME" "$ENV_FILE"; then
        fail "$ENV_FILE contains placeholder secrets"
    else
        pass "$ENV_FILE has no obvious placeholder secrets"
    fi
else
    fail "$ENV_FILE missing"
fi

if [[ -f ".env" ]]; then
    warn ".env exists; prefer $ENV_FILE with explicit env_file overrides"
fi

# ------------------------------------------------------------------ #
# 3. Docker and compose                                               #
# ------------------------------------------------------------------ #

echo ""
echo "  Docker"

if command -v docker &>/dev/null; then
    pass "Docker is available"
else
    fail "Docker is not installed or not in PATH"
fi

if docker compose version &>/dev/null; then
    pass "Docker Compose is available"
else
    fail "Docker Compose is not available"
fi

# ------------------------------------------------------------------ #
# 4. Config validation                                                #
# ------------------------------------------------------------------ #

echo ""
echo "  Configuration"

if [[ -f "docker-compose.yml" ]]; then
    pass "docker-compose.yml exists"
else
    fail "docker-compose.yml missing"
fi

if [[ -f "nginx/default.conf" ]]; then
    pass "nginx/default.conf exists"
else
    fail "nginx/default.conf missing"
fi

if [[ -f "scripts/deploy-dev.sh" && -f "scripts/deploy-live.sh" ]]; then
    pass "Deploy scripts present"
else
    fail "Deploy scripts missing"
fi

# ------------------------------------------------------------------ #
# 5. Isolation checks                                                 #
# ------------------------------------------------------------------ #

echo ""
echo "  Isolation"

if grep -q "$EXPECTED_URL" nginx/default.conf; then
    pass "Nginx routes $EXPECTED_URL"
else
    fail "Nginx does not route $EXPECTED_URL"
fi

OTHER_URL=""
if [[ "$ENV" == "live" ]]; then
    OTHER_URL="missioncontroldev.optichosting.co.za"
else
    OTHER_URL="missioncontrol.optichosting.co.za"
fi

if grep -q "$OTHER_URL" nginx/default.conf; then
    warn "Nginx also routes $OTHER_URL; ensure this host is intended"
else
    pass "Nginx does not expose $OTHER_URL on this config"
fi

if grep -q "missioncontrol-${ENV}-backend-1" nginx/default.conf; then
    pass "Backend upstream is environment-scoped"
else
    fail "Backend upstream is not environment-scoped"
fi

if grep -q "missioncontrol-${ENV}-frontend-1" nginx/default.conf; then
    pass "Frontend upstream is environment-scoped"
else
    fail "Frontend upstream is not environment-scoped"
fi

# ------------------------------------------------------------------ #
# 6. .gitignore safety                                                #
# ------------------------------------------------------------------ #

echo ""
echo "  Secrets hygiene"

if [[ -f ".env" ]] && ! grep -q "^\.env$" .gitignore; then
    fail ".env exists but is not gitignored"
else
    pass ".env handling is safe"
fi

if [[ -f "$ENV_FILE" ]] && ! grep -q "^${ENV_FILE}$" .gitignore; then
    fail "$ENV_FILE exists but is not gitignored"
else
    pass "$ENV_FILE handling is safe"
fi

# ------------------------------------------------------------------ #
# 7. Compose project guard                                            #
# ------------------------------------------------------------------ #

echo ""
echo "  Compose project guard"

EXPECTED_PROJECT=""
if [[ "$ENV" == "live" ]]; then
    EXPECTED_PROJECT="missioncontrol-live"
else
    EXPECTED_PROJECT="missioncontrol-dev"
fi

if [[ "${COMPOSE_PROJECT_NAME:-}" == "$EXPECTED_PROJECT" ]]; then
    pass "COMPOSE_PROJECT_NAME is $EXPECTED_PROJECT"
else
    warn "COMPOSE_PROJECT_NAME is '${COMPOSE_PROJECT_NAME:-unset}', expected $EXPECTED_PROJECT"
fi

# ------------------------------------------------------------------ #
# Summary                                                             #
# ------------------------------------------------------------------ #

echo ""
echo "  ─────────────────────────────────────────────────"
echo "  Passed: ${PASS}  Failed: ${FAIL}  Warnings: ${WARN}"

if [ "$FAIL" -gt 0 ]; then
    echo -e "  ${RED}RESULT: PRE-FLIGHT FAILED${NC}"
    exit 1
else
    echo -e "  ${GREEN}RESULT: PRE-FLIGHT PASSED${NC}"
    exit 0
fi
