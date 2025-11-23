-- Fix Revenue Module Tables
-- Run with: docker compose exec -T postgres psql -U luftway_user luftway_auth_dev < fix_schema.sql

-- Drop and recreate revenue tables in correct order
DROP TABLE IF EXISTS sponsored_placements CASCADE;
DROP TABLE IF EXISTS listing_payments CASCADE;
DROP TABLE IF EXISTS hotel_listings CASCADE;

-- Create hotel_listings with correct schema
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

-- Recreate listing_payments
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

CREATE INDEX ix_listing_payments_listing_id ON listing_payments(listing_id);
CREATE INDEX ix_listing_payments_created_at ON listing_payments(created_at);

-- Recreate sponsored_placements
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
CREATE INDEX ix_sponsored_placements_listing_id ON sponsored_placements(listing_id);
CREATE INDEX ix_sponsored_placements_status ON sponsored_placements(status);
CREATE INDEX ix_sponsored_placements_starts_at ON sponsored_placements(starts_at);

-- Done
SELECT 'Tables fixed successfully!' as status;

