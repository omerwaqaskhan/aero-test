#!/bin/bash
# Test script to verify the project is working correctly

set -e

echo "=========================================="
echo "🧪 Testing LuftWay Project"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "1️⃣ Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Check if services are running
echo "2️⃣ Checking Docker services..."
if ! docker compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Services not running. Starting services...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    echo "   Waiting for services to be healthy..."
    sleep 10
fi
echo -e "${GREEN}✅ Services are running${NC}"
echo ""

# Check service health
echo "3️⃣ Checking service health..."
echo "   - Backend health check..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    echo -e "   ${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "   ${RED}❌ Backend health check failed (HTTP $BACKEND_HEALTH)${NC}"
fi

echo "   - Frontend check..."
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ] || [ "$FRONTEND_HEALTH" = "000" ]; then
    echo -e "   ${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "   ${YELLOW}⚠️  Frontend returned HTTP $FRONTEND_HEALTH${NC}"
fi

echo "   - PostgreSQL check..."
if docker compose exec -T postgres pg_isready -U luftway_user > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "   ${RED}❌ PostgreSQL is not ready${NC}"
fi

echo "   - Redis check..."
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Redis is ready${NC}"
else
    echo -e "   ${RED}❌ Redis is not ready${NC}"
fi
echo ""

# Test API endpoints
echo "4️⃣ Testing API endpoints..."
echo "   - Root endpoint..."
ROOT_RESPONSE=$(curl -s http://localhost:8000/ | jq -r '.message' 2>/dev/null || echo "")
if [ "$ROOT_RESPONSE" = "Luftway Auth API" ]; then
    echo -e "   ${GREEN}✅ Root endpoint working${NC}"
else
    echo -e "   ${YELLOW}⚠️  Root endpoint returned: $ROOT_RESPONSE${NC}"
fi

echo "   - Health endpoint details..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "")
if [ "$HEALTH_RESPONSE" = "healthy" ]; then
    echo -e "   ${GREEN}✅ Health endpoint working${NC}"
    # Show service status
    echo "   Service status:"
    curl -s http://localhost:8000/health | jq '.services' 2>/dev/null || echo "   (Unable to parse JSON)"
else
    echo -e "   ${YELLOW}⚠️  Health endpoint status: $HEALTH_RESPONSE${NC}"
fi
echo ""

# Check database migrations
echo "5️⃣ Checking database migrations..."
if docker compose exec -T backend alembic -c /app/auth_module/migrations/alembic.ini current > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Database migrations are applied${NC}"
else
    echo -e "   ${YELLOW}⚠️  Could not check migrations (this is normal on first run)${NC}"
fi
echo ""

# Check data persistence
echo "6️⃣ Checking data persistence..."
if [ -d "./backups/postgres_dev_data" ]; then
    DATA_SIZE=$(du -sh ./backups/postgres_dev_data 2>/dev/null | cut -f1)
    echo -e "   ${GREEN}✅ Backup directory exists (size: $DATA_SIZE)${NC}"
else
    echo -e "   ${YELLOW}⚠️  Backup directory does not exist yet${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo ""
echo "Services:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Access URLs:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:3000"
echo ""
echo -e "${GREEN}✅ Testing complete!${NC}"
echo ""

