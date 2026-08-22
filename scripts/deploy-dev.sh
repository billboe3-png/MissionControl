#!/usr/bin/env bash
set -euo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-missioncontrol-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-${SCRIPT_DIR}/.env.dev}"

cd "${SCRIPT_DIR}"

echo "==> Deploying DEV environment"
echo "    Project : ${COMPOSE_PROJECT_NAME}"
echo "    Env file: ${ENV_FILE}"
echo "    Branch  : $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
echo "    Commit  : $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

docker compose \
  --project-name "${COMPOSE_PROJECT_NAME}" \
  --env-file "${ENV_FILE}" \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up -d --build

echo "==> DEV deployment complete"
echo "    URL: https://missioncontroldev.optichosting.co.za"
