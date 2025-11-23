#!/bin/bash
# Entrypoint script for LuftWay Backend
# Runs database migrations before starting the application

set -uo pipefail  # Don't exit on error, we handle them explicitly

echo "=========================================="
echo "🚀 LuftWay Backend - Starting Up"
echo "=========================================="

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-luftway_user}"

# Try to connect (works with or without password in docker network)
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
    echo "   Database not ready, waiting..."
    sleep 2
done
echo "✅ Database is ready!"

# Run migrations for auth_module
echo ""
echo "📦 Running auth_module migrations..."
cd /app/auth_module/migrations
if alembic upgrade head; then
    echo "   ✅ auth_module migrations successful"
else
    echo "   ⚠️  Warning: auth_module migrations failed, continuing..."
fi

# Run migrations for search_booking_module
echo ""
echo "📦 Running search_booking_module migrations..."
cd /app/search_booking_module/migrations
if alembic upgrade head; then
    echo "   ✅ search_booking_module migrations successful"
else
    echo "   ⚠️  Warning: search_booking_module migrations failed, continuing..."
fi

# Run migrations for revenue_module
echo ""
echo "📦 Running revenue_module migrations..."
cd /app/revenue_module/migrations
if alembic upgrade head; then
    echo "   ✅ revenue_module migrations successful"
else
    echo "   ⚠️  Warning: revenue_module migrations failed, continuing..."
fi

echo ""
echo "✅ All migrations completed!"
echo "=========================================="
echo "🚀 Starting application..."
echo "=========================================="

# Execute the main command (uvicorn)
exec "$@"

