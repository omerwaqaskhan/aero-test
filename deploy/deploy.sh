#!/bin/bash
# LuftWay Production Deployment Script
# Run this from the project root directory

set -euo pipefail

echo "=========================================="
echo "🚀 LuftWay Production Deployment"
echo "=========================================="

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production file not found!"
    echo "   Copy .env.production.example to .env.production and fill in all values"
    exit 1
fi

# Check for required environment variables
echo ""
echo "🔍 Checking environment variables..."
source .env.production

REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "JWT_SECRET_KEY"
    "SMTP_HOST"
    "SMTP_USERNAME"
    "SMTP_PASSWORD"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ] || [[ "${!var}" == *"CHANGE_ME"* ]]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Error: Missing or unchanged required environment variables:"
    printf '   - %s\n' "${MISSING_VARS[@]}"
    exit 1
fi

echo "✅ All required environment variables are set"

# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Check if SSL certificates exist
echo ""
echo "🔒 Checking SSL certificates..."
if [ ! -f "./certbot/conf/live/luftway.com/fullchain.pem" ]; then
    echo "⚠️  SSL certificates not found. You need to run SSL setup first."
    echo "   Run: ./deploy/setup-ssl.sh"
    exit 1
fi

# Build and start services
echo ""
echo "🏗️  Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache

echo ""
echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Services are healthy!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Services failed to become healthy"
    echo "   Check logs: docker compose -f docker-compose.prod.yml logs"
    exit 1
fi

# Show running containers
echo ""
echo "📊 Running containers:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Your application is now running at:"
echo "   🌐 https://www.luftway.com"
echo "   📚 API Docs: https://www.luftway.com/docs"
echo ""
echo "Useful commands:"
echo "   View logs: docker compose -f docker-compose.prod.yml logs -f"
echo "   Stop: docker compose -f docker-compose.prod.yml down"
echo "   Restart: docker compose -f docker-compose.prod.yml restart"
echo ""
echo "=========================================="

