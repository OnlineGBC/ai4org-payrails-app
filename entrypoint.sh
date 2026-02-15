#!/bin/bash
set -e

# Run Alembic migrations
cd /app/backend
echo "Running database migrations..."
alembic upgrade head

# Optionally seed data
if [ "$SEED_DATA" = "true" ]; then
    echo "Seeding data..."
    python -m app.seed
fi

# Start uvicorn in background
echo "Starting uvicorn..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start nginx in foreground
echo "Starting nginx..."
nginx -g 'daemon off;'
