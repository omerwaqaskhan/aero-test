"""Pytest configuration and shared fixtures for search_booking_module tests."""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import uuid

# Disable scheduler for tests
os.environ["DISABLE_SCHEDULER"] = "1"

from auth_module.infrastructure.db.database import Base, get_db
from auth_module.main import app

# Test database setup
# Use PostgreSQL for tests (SQLite doesn't support UUID type)
import os
from sqlalchemy import text

# Use the same database URL as the main app
TEST_DB_URL = os.getenv("DATABASE_URL", "postgresql://luftway_user:luftway_password@postgres:5432/luftway_auth_dev")
engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def setup_database():
    """Set up and tear down database for each test. Not autouse - only use when needed."""
    from sqlalchemy import text
    
    # Import models to ensure they're registered
    from auth_module.infrastructure.db.models import UserModel, TenantModel
    from search_booking_module.infrastructure.db.models import (
        HotelModel, OfferModel, RoomModel, ReviewModel
    )
    from search_booking_module.infrastructure.db.user_models import (
        FavoriteModel, BookingModel, PriceAlertModel, SavedSearchModel, UserReviewModel
    )
    
    # Create tables using raw SQL - much faster and avoids FK resolution issues
    db = TestingSessionLocal()
    try:
        # Create all tables in one transaction
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS favorites (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_favorites_user_hotel UNIQUE (user_id, hotel_id)
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS bookings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
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
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                target_price NUMERIC(10, 2) NOT NULL,
                currency VARCHAR(10) NOT NULL DEFAULT 'USD',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                triggered_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS saved_searches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                search_query JSONB NOT NULL,
                name VARCHAR(255),
                notification_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_reviews (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                title VARCHAR(255),
                text TEXT,
                published BOOLEAN NOT NULL DEFAULT FALSE,
                helpful_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_user_review_hotel UNIQUE (user_id, hotel_id)
            )
        """))
        db.commit()
    finally:
        db.close()
    
    yield
    
    # Cleanup - drop tables
    try:
        db = TestingSessionLocal()
        db.execute(text("DROP TABLE IF EXISTS user_reviews CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS saved_searches CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS price_alerts CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS bookings CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS favorites CASCADE"))
        db.commit()
        db.close()
    except:
        pass  # Ignore cleanup errors

@pytest.fixture
def db_session(setup_database):
    """Provide a database session."""
    # Ensure setup_database runs first (it's autouse, but explicit dependency helps)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    """Provide a test client."""
    # Use TestClient with lifespan disabled to avoid hanging
    # TestClient should handle lifespan, but we'll be explicit
    return TestClient(app, base_url="http://test")

