#!/bin/bash

# LuftWay - Database Setup and Hotel Data Population Script
# This script fixes database tables and populates hotel data

set -e  # Exit on error

echo "=========================================="
echo "🚀 LuftWay Database Setup & Population"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker compose ps | grep -q "luftway-backend"; then
    echo -e "${RED}❌ Backend container is not running!${NC}"
    echo "Please start with: docker compose up -d"
    exit 1
fi

echo -e "${BLUE}Step 1/4: Fixing hotel_listings table schema...${NC}"
docker compose exec backend python -c "
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.getenv('DATABASE_URL'))

print('Fixing hotel_listings table...')
with engine.begin() as conn:
    # Drop tables in correct order (FK dependencies)
    conn.execute(text('DROP TABLE IF EXISTS sponsored_placements CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS listing_payments CASCADE'))
    conn.execute(text('DROP TABLE IF EXISTS hotel_listings CASCADE'))
    
    # Create hotel_listings with correct schema
    conn.execute(text('''
        CREATE TABLE hotel_listings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            hotel_id UUID NOT NULL UNIQUE REFERENCES hotels(id) ON DELETE CASCADE,
            package VARCHAR(20) NOT NULL DEFAULT 'free',
            owner_email VARCHAR(255) NOT NULL,
            owner_name VARCHAR(255),
            owner_phone VARCHAR(50),
            verified BOOLEAN NOT NULL DEFAULT FALSE,
            verification_token VARCHAR(255) UNIQUE,
            stripe_customer_id VARCHAR(255),
            current_period_start TIMESTAMP,
            current_period_end TIMESTAMP,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_hotel_listings_hotel_id ON hotel_listings(hotel_id);
        CREATE INDEX ix_hotel_listings_package ON hotel_listings(package);
        CREATE INDEX ix_hotel_listings_owner_email ON hotel_listings(owner_email);
        CREATE INDEX ix_hotel_listings_verified ON hotel_listings(verified);
        CREATE INDEX ix_hotel_listings_status ON hotel_listings(status);
    '''))
    
    # Recreate dependent tables
    conn.execute(text('''
        CREATE TABLE listing_payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            listing_id UUID NOT NULL REFERENCES hotel_listings(id) ON DELETE CASCADE,
            stripe_payment_intent_id VARCHAR(255) UNIQUE,
            amount NUMERIC(10, 2) NOT NULL,
            currency VARCHAR(10) NOT NULL DEFAULT 'USD',
            status VARCHAR(20) NOT NULL,
            package VARCHAR(20) NOT NULL,
            period_start TIMESTAMP,
            period_end TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_listing_payments_listing_id ON listing_payments(listing_id);
    '''))
    
    conn.execute(text('''
        CREATE TABLE sponsored_placements (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
            listing_id UUID REFERENCES hotel_listings(id) ON DELETE SET NULL,
            placement_type VARCHAR(50) NOT NULL,
            search_criteria JSONB NOT NULL DEFAULT '{}',
            cpc_bid NUMERIC(10, 2) NOT NULL,
            daily_budget NUMERIC(10, 2),
            total_budget NUMERIC(10, 2),
            spent_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
            impressions INTEGER NOT NULL DEFAULT 0,
            clicks INTEGER NOT NULL DEFAULT 0,
            conversions INTEGER NOT NULL DEFAULT 0,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            starts_at TIMESTAMP NOT NULL,
            ends_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_sponsored_placements_hotel_id ON sponsored_placements(hotel_id);
    '''))

print('✅ Hotel listings tables fixed!')
" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Hotel listings table fixed successfully!${NC}"
else
    echo -e "${RED}❌ Failed to fix hotel listings table${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 2/4: Verifying all database tables...${NC}"
docker compose exec backend python -c "
from search_booking_module.infrastructure.db.models import HotelModel, RoomModel, ReviewModel, OfferModel
from revenue_module.infrastructure.db.models import LeadModel, SubscriptionModel, HotelListingModel
from auth_module.infrastructure.db.models import UserModel
from auth_module.infrastructure.db.database import SessionLocal

db = SessionLocal()
print('=== DATABASE STATUS ===')
print(f'Users: {db.query(UserModel).count()}')
print(f'Hotels: {db.query(HotelModel).count()}')
print(f'Rooms: {db.query(RoomModel).count()} (will populate)')
print(f'Offers: {db.query(OfferModel).count()}')
print(f'Reviews: {db.query(ReviewModel).count()} (will add more)')
print(f'Leads: {db.query(LeadModel).count()}')
print(f'Subscriptions: {db.query(SubscriptionModel).count()}')
print(f'Hotel Listings: {db.query(HotelListingModel).count()}')
print(f'Hotels with rooms: {db.query(HotelModel).join(RoomModel).distinct().count()} / 100')
print(f'Hotels with reviews: {db.query(HotelModel).join(ReviewModel).distinct().count()} / 100')
db.close()
print('✅ All tables verified!')
" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database verification complete!${NC}"
else
    echo -e "${RED}❌ Database verification failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 3/4: Starting hotel data scraper...${NC}"
echo -e "${YELLOW}⏱️  This will take 15-20 minutes to complete${NC}"
echo -e "${YELLOW}📊 Scraping 100 hotels for rooms, reviews, amenities, etc.${NC}"
echo ""

# Start scraper in background
docker compose exec -d backend python -m search_booking_module.scraping.rescrape_hotels

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Hotel data scraper started in background!${NC}"
else
    echo -e "${RED}❌ Failed to start hotel data scraper${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 4/4: Monitoring scraper progress...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring (scraper will continue in background)${NC}"
echo ""

# Monitor for 30 seconds then exit
timeout 30s docker compose logs -f backend | grep -i "scraping\|updated\|rooms\|reviews" || true

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "📊 WHAT'S HAPPENING NOW:"
echo "  - Hotel data scraper is running in the background"
echo "  - It will take 15-20 minutes to complete"
echo "  - You can monitor progress with the commands below"
echo ""
echo "📝 USEFUL COMMANDS:"
echo ""
echo "  # Monitor scraper progress:"
echo "  docker compose logs -f backend | grep -i 'scraping\|updated\|rooms'"
echo ""
echo "  # Check current database stats:"
echo "  docker compose exec backend python -c \\"
echo "from search_booking_module.infrastructure.db.models import HotelModel, RoomModel, ReviewModel"
echo "from auth_module.infrastructure.db.database import SessionLocal"
echo "db = SessionLocal()"
echo "print(f'Hotels: {db.query(HotelModel).count()}')"
echo "print(f'Rooms: {db.query(RoomModel).count()}')"
echo "print(f'Reviews: {db.query(ReviewModel).count()}')"
echo "print(f'Hotels with rooms: {db.query(HotelModel).join(RoomModel).distinct().count()}')"
echo "db.close()\\"
echo ""
echo "  # Check if scraper is still running:"
echo "  docker compose exec backend ps aux | grep rescrape"
echo ""
echo "  # View full backend logs:"
echo "  docker compose logs backend"
echo ""
echo "=========================================="
echo -e "${GREEN}✅ All database tables are ready!${NC}"
echo -e "${YELLOW}⏱️  Hotel data scraper is running...${NC}"
echo "=========================================="
echo ""

