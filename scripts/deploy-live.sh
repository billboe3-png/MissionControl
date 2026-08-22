#!/usr/bin/env bash
set -euo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-missioncontrol-live}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-${SCRIPT_DIR}/.env.production}"

cd "${SCRIPT_DIR}"

echo "==> Deploying LIVE environment"
echo "    Project : ${COMPOSE_PROJECT_NAME}"
echo "    Env file: ${ENV_FILE}"
echo "    Branch  : $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
echo "    Commit  : $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

if [[ "${COMPOSE_PROJECT_NAME}" != "missioncontrol-live" ]]; then
  echo "ERROR: LIVE deployment requires COMPOSE_PROJECT_NAME=missioncontrol-live" >&2
  exit 1
fi

docker compose \
  --project-name "${COMPOSE_PROJECT_NAME}" \
  --env-file "${ENV_FILE}" \
  -f docker-compose.yml \
  -f docker-compose.production.yml \
  up -d --build

echo "==> LIVE deployment complete"
echo "    URL: https://missioncontrol.optichosting.co.za"
