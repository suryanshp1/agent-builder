#!/bin/bash
set -e

echo "==================================================="
echo "AgentBuilder Backend Initialization"
echo "==================================================="

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -p 5432 -U agentbuilder -q; do
  echo "  PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ PostgreSQL is ready!"

echo "Running database initialization (idempotent)..."
python /app/scripts/init_db.py || {
    echo "⚠️  Init script had issues (may be already initialized)"
}

echo "==================================================="
echo "Starting FastAPI application..."
echo "==================================================="

# Execute the main command (passed as arguments to this script)
exec "$@"
