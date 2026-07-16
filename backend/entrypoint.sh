#!/bin/sh
set -e

# ---------------------------------------------------------------
# Startup Diagnostics
# ---------------------------------------------------------------
echo "============================================"
echo "  Mission Control - Startup"
echo "============================================"
echo ""
echo "  Hostname:    $(hostname)"
echo "  User:        $(id)"
echo "  POSTGRES_HOST=${POSTGRES_HOST:-<unset>}"
echo "  POSTGRES_PORT=${POSTGRES_PORT:-<unset>}"
echo "  POSTGRES_DB=${POSTGRES_DB:-<unset>}"
echo "  POSTGRES_USER=${POSTGRES_USER:-<unset>}"
echo "  REDIS_HOST=${REDIS_HOST:-<unset>}"
echo "  REDIS_PORT=${REDIS_PORT:-<unset>}"
echo ""

# ---------------------------------------------------------------
# DNS Resolution Test (temporary diagnostics)
# ---------------------------------------------------------------
echo "--- DNS Resolution ---"
PG_HOST="${POSTGRES_HOST:-postgres}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_DB="${POSTGRES_DB:-mission_control}"
PG_USER="${POSTGRES_USER:-mission_control}"
PG_PASS="${POSTGRES_PASSWORD:-mission_control}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

python -c "
import socket, sys
for name in ['${PG_HOST}', '${REDIS_HOST}']:
    try:
        ip = socket.gethostbyname(name)
        print(f'  {name} -> {ip}')
    except Exception as e:
        print(f'  {name} -> FAILED: {type(e).__name__}: {e}', file=sys.stderr)
" || echo "  (DNS check script failed)"


# ---------------------------------------------------------------
# Wait for PostgreSQL
# ---------------------------------------------------------------
echo ""
echo "Waiting for PostgreSQL at ${PG_HOST}:${PG_PORT}..."
MAX_RETRIES=30
RETRY_COUNT=0

while true; do
    CHECK_OUTPUT=$(python -c "
import sys, socket

# Step 1: DNS resolution
try:
    ip = socket.gethostbyname('${PG_HOST}')
    sys.stderr.write(f'  DNS: {ip}\n')
except Exception as e:
    sys.stderr.write(f'  DNS FAILED: {type(e).__name__}: {e}\n')
    sys.exit(1)

# Step 2: TCP connection
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(('${PG_HOST}', ${PG_PORT}))
    s.close()
    sys.stderr.write(f'  TCP: connected\n')
except Exception as e:
    sys.stderr.write(f'  TCP FAILED: {type(e).__name__}: {e}\n')
    sys.exit(1)

# Step 3: PostgreSQL protocol check (psycopg)
try:
    import psycopg
    conn = psycopg.connect(
        host='${PG_HOST}',
        port=${PG_PORT},
        dbname='${PG_DB}',
        user='${PG_USER}',
        password='${PG_PASS}',
        connect_timeout=3,
    )
    conn.close()
    sys.stderr.write(f'  PostgreSQL: ready\n')
except ImportError:
    sys.stderr.write(f'  psycopg not installed, skipping protocol check\n')
except Exception as e:
    sys.stderr.write(f'  PostgreSQL FAILED: {type(e).__name__}: {e}\n')
    sys.exit(1)

sys.exit(0)
" 2>&1)

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "${CHECK_OUTPUT}"
        echo "PostgreSQL is ready."
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: PostgreSQL not available after ${MAX_RETRIES} attempts"
        echo "${CHECK_OUTPUT}"
        exit 1
    fi
    echo "  [${RETRY_COUNT}/${MAX_RETRIES}] Waiting..."
    echo "${CHECK_OUTPUT}"
    sleep 2
done


# ---------------------------------------------------------------
# Wait for Redis
# ---------------------------------------------------------------
echo ""
echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
RETRY_COUNT=0

while true; do
    CHECK_OUTPUT=$(python -c "
import sys, socket

# Step 1: DNS resolution
try:
    ip = socket.gethostbyname('${REDIS_HOST}')
    sys.stderr.write(f'  DNS: {ip}\n')
except Exception as e:
    sys.stderr.write(f'  DNS FAILED: {type(e).__name__}: {e}\n')
    sys.exit(1)

# Step 2: TCP connection
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    s.connect(('${REDIS_HOST}', ${REDIS_PORT}))
    s.close()
    sys.stderr.write(f'  TCP: connected\n')
except Exception as e:
    sys.stderr.write(f'  TCP FAILED: {type(e).__name__}: {e}\n')
    sys.exit(1)

# Step 3: Redis protocol check
try:
    import redis as redis_lib
    r = redis_lib.Redis(host='${REDIS_HOST}', port=${REDIS_PORT}, socket_timeout=3)
    r.ping()
    sys.stderr.write(f'  Redis: ready\n')
except ImportError:
    sys.stderr.write(f'  redis library not installed, skipping protocol check\n')
except Exception as e:
    sys.stderr.write(f'  Redis FAILED: {type(e).__name__}: {e}\n')
    sys.exit(1)

sys.exit(0)
" 2>&1)

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "${CHECK_OUTPUT}"
        echo "Redis is ready."
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Redis not available after ${MAX_RETRIES} attempts"
        echo "${CHECK_OUTPUT}"
        exit 1
    fi
    echo "  [${RETRY_COUNT}/${MAX_RETRIES}] Waiting..."
    echo "${CHECK_OUTPUT}"
    sleep 2
done


# ---------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------
echo ""
echo "Validating configuration..."
python -c "from app.core.startup_check import validate_all; validate_all()"

# ---------------------------------------------------------------
# Apply database migrations
# ---------------------------------------------------------------
echo "Applying database migrations..."
if ! alembic upgrade head; then
    echo "Migration issue detected, stamping head..."
    alembic stamp head
fi

# ---------------------------------------------------------------
# Run database seed
# ---------------------------------------------------------------
echo "Running database seed..."
python -m app.seed.runner

# ---------------------------------------------------------------
# Start Mission Control
# ---------------------------------------------------------------
echo ""
echo "Starting Mission Control..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000
