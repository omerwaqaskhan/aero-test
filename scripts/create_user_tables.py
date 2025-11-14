"""Script to create user feature tables directly."""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from auth_module.infrastructure.db.database import DATABASE_URL

def create_tables():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('favorites', 'bookings', 'price_alerts', 'saved_searches', 'user_reviews');
        """))
        existing = [row[0] for row in result]
        
        if existing:
            print(f"Tables already exist: {', '.join(existing)}")
            return
        
        # Create enums
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE bookingstatus AS ENUM ('pending', 'confirmed', 'cancelled', 'completed', 'refunded');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE pricealertstatus AS ENUM ('active', 'triggered', 'inactive');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        # Create favorites table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS favorites (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid()::text,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, hotel_id)
            );
            CREATE INDEX IF NOT EXISTS ix_favorites_user_id ON favorites(user_id);
            CREATE INDEX IF NOT EXISTS ix_favorites_hotel_id ON favorites(hotel_id);
        """))
        
        # Create bookings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bookings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid()::text,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
                booking_reference VARCHAR(100) UNIQUE,
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                guests INTEGER NOT NULL DEFAULT 1,
                rooms INTEGER NOT NULL DEFAULT 1,
                guest_name VARCHAR(255) NOT NULL,
                guest_email VARCHAR(255) NOT NULL,
                guest_phone VARCHAR(50),
                total_price NUMERIC(10, 2) NOT NULL,
                currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                taxes_included BOOLEAN NOT NULL DEFAULT FALSE,
                status bookingstatus NOT NULL DEFAULT 'pending',
                provider VARCHAR(50),
                provider_booking_id VARCHAR(255),
                affiliate_link TEXT,
                booked_at TIMESTAMP NOT NULL DEFAULT NOW(),
                confirmed_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                special_requests TEXT,
                cancellation_policy JSONB NOT NULL DEFAULT '{}',
                booking_metadata JSONB NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS ix_bookings_user_id ON bookings(user_id);
            CREATE INDEX IF NOT EXISTS ix_bookings_hotel_id ON bookings(hotel_id);
            CREATE INDEX IF NOT EXISTS ix_bookings_offer_id ON bookings(offer_id);
            CREATE INDEX IF NOT EXISTS ix_bookings_status ON bookings(status);
            CREATE INDEX IF NOT EXISTS ix_bookings_guest_email ON bookings(guest_email);
            CREATE INDEX IF NOT EXISTS ix_bookings_check_in ON bookings(check_in);
            CREATE INDEX IF NOT EXISTS ix_bookings_check_out ON bookings(check_out);
        """))
        
        # Create price_alerts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid()::text,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                target_price NUMERIC(10, 2) NOT NULL,
                currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                check_in DATE,
                check_out DATE,
                guests INTEGER,
                rooms INTEGER,
                status pricealertstatus NOT NULL DEFAULT 'active',
                last_checked_at TIMESTAMP,
                triggered_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS ix_price_alerts_user_id ON price_alerts(user_id);
            CREATE INDEX IF NOT EXISTS ix_price_alerts_hotel_id ON price_alerts(hotel_id);
            CREATE INDEX IF NOT EXISTS ix_price_alerts_status ON price_alerts(status);
        """))
        
        # Create saved_searches table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS saved_searches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid()::text,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                search_query JSONB NOT NULL DEFAULT '{}',
                name VARCHAR(255),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS ix_saved_searches_user_id ON saved_searches(user_id);
        """))
        
        # Create user_reviews table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_reviews (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid()::text,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                title VARCHAR(500),
                text TEXT,
                published BOOLEAN NOT NULL DEFAULT FALSE,
                moderated_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS ix_user_reviews_user_id ON user_reviews(user_id);
            CREATE INDEX IF NOT EXISTS ix_user_reviews_hotel_id ON user_reviews(hotel_id);
        """))
        
        conn.commit()
        print("✓ All user feature tables created successfully!")

if __name__ == "__main__":
    create_tables()

