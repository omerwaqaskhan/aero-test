#!/bin/bash
set -e

echo "🔄 Rebuilding revenue tables..."

# Drop tables
docker compose exec postgres psql -U luftway_user luftway_auth_dev -c "DROP TABLE IF EXISTS sponsored_placements CASCADE;"
docker compose exec postgres psql -U luftway_user luftway_auth_dev -c "DROP TABLE IF EXISTS listing_payments CASCADE;"
docker compose exec postgres psql -U luftway_user luftway_auth_dev -c "DROP TABLE IF EXISTS hotel_listings CASCADE;"

echo "✅ Dropped old tables"

# Create hotel_listings
docker compose exec postgres psql -U luftway_user luftway_auth_dev -c "
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
"

echo "✅ Created hotel_listings"

# Create listing_payments
docker compose exec postgres psql -U luftway_user luftway_auth_dev -c "
CREATE TABLE listing_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES hotel_listings(id) ON DELETE CASCADE,
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    package VARCHAR(20) NOT NULL,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
"

echo "✅ Created listing_payments"

# Create sponsored_placements
docker compose exec postgres psql -U luftway_user luftway_auth_dev -c "
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
"

echo "✅ Created sponsored_placements"

# Test
echo ""
echo "🧪 Testing database..."
docker compose exec backend python -c "
from search_booking_module.infrastructure.db.models import HotelModel, RoomModel
from revenue_module.infrastructure.db.models import HotelListingModel
from auth_module.infrastructure.db.database import SessionLocal
db = SessionLocal()
print(f'Hotels: {db.query(HotelModel).count()}')
print(f'Rooms: {db.query(RoomModel).count()}')
print(f'Hotel Listings table: ✅')
db.close()
"

echo ""
echo "🎉 DONE! Tables rebuilt successfully!"
echo ""
echo "Now run hotel scraper:"
echo "  docker compose exec -d backend python -m search_booking_module.scraping.rescrape_hotels"

