"""Simplified unit tests - direct API testing approach."""

import pytest
from datetime import date, timedelta
import uuid
from fastapi.testclient import TestClient

# Disable scheduler before any imports
import os
os.environ["DISABLE_SCHEDULER"] = "1"

from auth_module.main import app
from auth_module.infrastructure.db.database import SessionLocal
from auth_module.infrastructure.db.models import UserModel, TenantModel
from search_booking_module.infrastructure.db.models import HotelModel
from auth_module.core.security import PasswordManager, JWTManager

client = TestClient(app)

def get_or_create_tenant(db, slug="test-tenant-default"):
    """Get existing tenant or create one."""
    tenant = db.query(TenantModel).filter(TenantModel.slug == slug).first()
    if not tenant:
        tenant = TenantModel(
            id=uuid.uuid4(),
            slug=slug,
            name="Test Tenant",
            status="active"
        )
        db.add(tenant)
        db.commit()
    return tenant

def get_or_create_user(db, tenant, email="test@example.com"):
    """Get existing user or create one."""
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        user = UserModel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=email,
            password_hash=PasswordManager.hash_password("testpassword123"),
            first_name="Test",
            last_name="User",
            role="user",
            status="active",
            email_verified=True
        )
        db.add(user)
        db.commit()
    return user

def get_or_create_hotel(db, name="Test Hotel"):
    """Get existing hotel or create one."""
    hotel = db.query(HotelModel).filter(HotelModel.name == name).first()
    if not hotel:
        hotel = HotelModel(
            id=str(uuid.uuid4()),
            name=name,
            city="Test City",
            country="Test Country",
            address="123 Test St",
            latitude=40.7128,
            longitude=-74.0060,
            stars=4,
            rating=4.5,
            images=["https://example.com/image.jpg"],
            amenities=["WiFi", "Pool"],
            description="A test hotel"
        )
        db.add(hotel)
        db.commit()
    return hotel

def get_auth_token(user):
    """Generate auth token."""
    return JWTManager.generate_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        role=user.role,
        permissions=[]
    )

def test_create_favorite():
    """Test creating a favorite - minimal setup."""
    db = SessionLocal()
    try:
        tenant = get_or_create_tenant(db)
        user = get_or_create_user(db, tenant)
        hotel = get_or_create_hotel(db)
        token = get_auth_token(user)
        
        # Ensure favorites table exists
        from sqlalchemy import text
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_favorites_user_hotel UNIQUE (user_id, hotel_id)
                )
            """))
            db.commit()
        except Exception as e:
            db.rollback()
            # Table might already exist, continue
        
        response = client.post(
            "/api/v1/user/favorites",
            json={"hotel_id": str(hotel.id)},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["hotel_id"] == str(hotel.id)
        assert data["user_id"] == str(user.id)
    finally:
        db.close()

def test_get_favorites():
    """Test getting favorites."""
    db = SessionLocal()
    try:
        tenant = get_or_create_tenant(db)
        user = get_or_create_user(db, tenant)
        hotel = get_or_create_hotel(db)
        token = get_auth_token(user)
        
        # Ensure favorites table exists and create a favorite
        from sqlalchemy import text
        from search_booking_module.infrastructure.db.user_models import FavoriteModel
        
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_favorites_user_hotel UNIQUE (user_id, hotel_id)
                )
            """))
            db.commit()
        except:
            db.rollback()
        
        # Create favorite directly
        favorite = FavoriteModel(
            id=str(uuid.uuid4()),
            user_id=str(user.id),
            hotel_id=str(hotel.id)
        )
        db.add(favorite)
        db.commit()
        
        response = client.get(
            "/api/v1/user/favorites",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(f["hotel_id"] == str(hotel.id) for f in data)
    finally:
        db.close()

def test_create_booking():
    """Test creating a booking."""
    db = SessionLocal()
    try:
        tenant = get_or_create_tenant(db)
        user = get_or_create_user(db, tenant)
        hotel = get_or_create_hotel(db)
        token = get_auth_token(user)
        
        # Ensure bookings table exists
        from sqlalchemy import text
        try:
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
            db.commit()
        except:
            db.rollback()
        
        check_in = date.today() + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
        
        response = client.post(
            "/api/v1/user/bookings",
            json={
                "hotel_id": str(hotel.id),
                "check_in": str(check_in),
                "check_out": str(check_out),
                "guests": 2,
                "rooms": 1,
                "guest_name": "Test Guest",
                "guest_email": "guest@example.com",
                "total_price": 200.00,
                "currency": "USD"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["hotel_id"] == str(hotel.id)
        assert data["guests"] == 2
    finally:
        db.close()

