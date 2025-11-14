"""Unit tests for hotel owner dashboard features."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import uuid

from auth_module.infrastructure.db.database import Base, get_db
from auth_module.infrastructure.db.models import UserModel
from search_booking_module.infrastructure.db.models import HotelModel
from revenue_module.infrastructure.db.models import HotelListingModel, LeadModel
from auth_module.main import app

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_owner.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def owner_user(db_session):
    """Create a hotel owner user."""
    user = UserModel(
        id=str(uuid.uuid4()),
        email="owner@hotel.com",
        password_hash=PasswordManager.hash_password("testpassword123"),
        first_name="Hotel",
        last_name="Owner",
        is_active=True,
        is_verified=True,
        role="user",
        tenant_id=str(uuid.uuid4())
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_hotel(db_session):
    """Create a test hotel."""
    hotel = HotelModel(
        id=str(uuid.uuid4()),
        name="Test Hotel",
        city="Test City",
        country="Test Country",
        address="123 Test St",
        latitude=40.7128,
        longitude=-74.0060,
        stars=4,
        rating=4.5,
        review_count=100,
        images=["https://example.com/image.jpg"],
        amenities=["WiFi", "Pool"],
        description="A test hotel"
    )
    db_session.add(hotel)
    db_session.commit()
    db_session.refresh(hotel)
    return hotel

@pytest.fixture
def hotel_listing(db_session, owner_user, test_hotel):
    """Create a hotel listing."""
    listing = HotelListingModel(
        id=str(uuid.uuid4()),
        hotel_id=test_hotel.id,
        owner_email=owner_user.email,
        owner_name="Hotel Owner",
        package="premium",
        status="active",
        verified=True
    )
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing

@pytest.fixture
def auth_headers(owner_user):
    """Get authentication headers."""
    token = JWTManager.generate_access_token(
        user_id=str(owner_user.id),
        tenant_id=str(owner_user.tenant_id),
        email=owner_user.email,
        role=owner_user.role,
        permissions=[]
    )
    return {"Authorization": f"Bearer {token}"}

class TestOwnerListings:
    """Test owner listing endpoints."""
    
    def test_get_owner_listing(self, client, owner_user, hotel_listing, auth_headers):
        """Test getting owner's listing."""
        response = client.get(
            "/api/v1/revenue/owners/listings",
            params={"owner_email": owner_user.email},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["owner_email"] == owner_user.email
        assert data["hotel_id"] == hotel_listing.hotel_id
    
    def test_update_listing(self, client, owner_user, hotel_listing, auth_headers):
        """Test updating listing details."""
        response = client.patch(
            f"/api/v1/revenue/listings/{hotel_listing.id}",
            json={
                "owner_name": "Updated Owner Name",
                "owner_phone": "+1234567890",
                "website": "https://testhotel.com"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["owner_name"] == "Updated Owner Name"
        assert data["owner_phone"] == "+1234567890"

class TestOwnerLeads:
    """Test owner lead endpoints."""
    
    def test_get_owner_leads(self, client, owner_user, test_hotel, hotel_listing, auth_headers, db_session):
        """Test getting leads for owner's hotel."""
        # Create a lead
        lead = LeadModel(
            id=str(uuid.uuid4()),
            hotel_id=test_hotel.id,
            name="Test Guest",
            email="guest@example.com",
            phone="+1234567890",
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=9),
            guests=2,
            rooms=1,
            status="new"
        )
        db_session.add(lead)
        db_session.commit()
        
        response = client.get(
            "/api/v1/revenue/owners/leads",
            params={"hotel_id": test_hotel.id, "limit": 50},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Guest"
        assert data[0]["hotel_id"] == test_hotel.id
    
    def test_get_lead_details(self, client, owner_user, test_hotel, hotel_listing, auth_headers, db_session):
        """Test getting specific lead details."""
        lead = LeadModel(
            id=str(uuid.uuid4()),
            hotel_id=test_hotel.id,
            name="Test Guest",
            email="guest@example.com",
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=9),
            guests=2,
            rooms=1,
            status="new"
        )
        db_session.add(lead)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/revenue/owners/leads/{lead.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lead.id
        assert data["name"] == "Test Guest"

