#!/bin/sh
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Running database seed..."
python -m app.seed.runner

echo "Starting Mission Control..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000