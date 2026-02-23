#!/bin/bash
set -e

# Default PORT to 8080 (Cloud Run sets this env var; local Docker uses default)
export PORT="${PORT:-8080}"

# Resolve ${PORT} in nginx config using sed (envsubst not in slim image)
sed -i "s/\${PORT}/$PORT/g" /etc/nginx/conf.d/default.conf

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

# Wait for uvicorn to be ready before starting nginx
echo "Waiting for uvicorn to be ready..."
python3 -c "
import socket, time, sys
for i in range(30):
    try:
        s = socket.create_connection(('127.0.0.1', 8000), timeout=1)
        s.close()
        print('Uvicorn is ready')
        sys.exit(0)
    except OSError:
        time.sleep(1)
print('ERROR: uvicorn did not start within 30 seconds', file=sys.stderr)
sys.exit(1)
"

# Start nginx in foreground
echo "Starting nginx on port $PORT..."
nginx -g 'daemon off;'
