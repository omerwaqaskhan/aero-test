"""Unit tests for user features: favorites, bookings, price alerts, saved searches, reviews."""

import pytest
from datetime import date, datetime, timedelta
import uuid

from auth_module.infrastructure.db.models import UserModel
from search_booking_module.infrastructure.db.models import HotelModel
from search_booking_module.infrastructure.db.user_models import (
    FavoriteModel, BookingModel, PriceAlertModel, SavedSearchModel, UserReviewModel
)
from auth_module.core.security import PasswordManager, JWTManager

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from auth_module.infrastructure.db.models import TenantModel
    import uuid as uuid_lib
    
    # Create a tenant first (required for UserModel)
    tenant = TenantModel(
        id=uuid_lib.uuid4(),
        slug="test-tenant",
        name="Test Tenant",
        status="active"
    )
    db_session.add(tenant)
    db_session.commit()
    
    # Create user with correct fields
    user = UserModel(
        id=uuid_lib.uuid4(),
        tenant_id=tenant.id,
        email="test@example.com",
        password_hash=PasswordManager.hash_password("testpassword123"),
        first_name="Test",
        last_name="User",
        role="user",
        status="active",
        email_verified=True
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
def auth_headers(test_user):
    """Get authentication headers."""
    token = JWTManager.generate_access_token(
        user_id=str(test_user.id),
        tenant_id=str(test_user.tenant_id),
        email=test_user.email,
        role=test_user.role,
        permissions=[]
    )
    return {"Authorization": f"Bearer {token}"}

class TestFavorites:
    """Test favorites endpoints."""
    
    def test_create_favorite(self, client, test_user, test_hotel, auth_headers, setup_database):
        """Test creating a favorite."""
        response = client.post(
            f"/api/v1/user/favorites",
            json={"hotel_id": str(test_hotel.id)},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hotel_id"] == str(test_hotel.id)
        assert data["user_id"] == str(test_user.id)
    
    def test_get_favorites(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test getting all favorites."""
        # Create a favorite first
        favorite = FavoriteModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id)
        )
        db_session.add(favorite)
        db_session.commit()
        
        response = client.get("/api/v1/user/favorites", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["hotel_id"] == str(test_hotel.id)
    
    def test_check_favorite(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test checking if hotel is favorited."""
        # Create a favorite
        favorite = FavoriteModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id)
        )
        db_session.add(favorite)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/user/favorites/check/{str(test_hotel.id)}",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["is_favorite"] is True
    
    def test_delete_favorite(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test deleting a favorite."""
        # Create a favorite
        favorite = FavoriteModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id)
        )
        db_session.add(favorite)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/user/favorites/{str(test_hotel.id)}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify it's deleted
        check_response = client.get(
            f"/api/v1/user/favorites/check/{str(test_hotel.id)}",
            headers=auth_headers
        )
        assert check_response.json()["is_favorite"] is False

class TestBookings:
    """Test bookings endpoints."""
    
    def test_create_booking(self, client, test_user, test_hotel, auth_headers, setup_database):
        """Test creating a booking."""
        check_in = date.today() + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
        
        response = client.post(
            "/api/v1/user/bookings",
            json={
                "hotel_id": str(test_hotel.id),
                "check_in": str(check_in),
                "check_out": str(check_out),
                "guests": 2,
                "rooms": 1,
                "guest_name": "Test Guest",
                "guest_email": "guest@example.com",
                "total_price": 200.00,
                "currency": "USD"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hotel_id"] == test_hotel.id
        assert data["guests"] == 2
        assert data["rooms"] == 1
    
    def test_get_bookings(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test getting all bookings."""
        check_in = date.today() + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
        
        booking = BookingModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id),
            check_in=check_in,
            check_out=check_out,
            guests=2,
            rooms=1,
            guest_name="Test Guest",
            guest_email="guest@example.com",
            total_price=200.00,
            currency="USD",
            status="pending"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.get("/api/v1/user/bookings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["hotel_id"] == str(test_hotel.id)
    
    def test_update_booking_status(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test updating booking status."""
        check_in = date.today() + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
        
        booking = BookingModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id),
            check_in=check_in,
            check_out=check_out,
            guests=2,
            rooms=1,
            guest_name="Test Guest",
            guest_email="guest@example.com",
            total_price=200.00,
            currency="USD",
            status="pending"
        )
        db_session.add(booking)
        db_session.commit()
        
        response = client.patch(
            f"/api/v1/user/bookings/{booking.id}/status",
            json={"status": "confirmed"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

class TestPriceAlerts:
    """Test price alerts endpoints."""
    
    def test_create_price_alert(self, client, test_user, test_hotel, auth_headers, setup_database):
        """Test creating a price alert."""
        response = client.post(
            "/api/v1/user/price-alerts",
            json={
                "hotel_id": str(test_hotel.id),
                "target_price": 150.00,
                "currency": "USD"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hotel_id"] == test_hotel.id
        assert float(data["target_price"]) == 150.00
    
    def test_get_price_alerts(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test getting all price alerts."""
        alert = PriceAlertModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id),
            target_price=150.00,
            currency="USD",
            status="active"
        )
        db_session.add(alert)
        db_session.commit()
        
        response = client.get("/api/v1/user/price-alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["hotel_id"] == str(test_hotel.id)
    
    def test_delete_price_alert(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test deleting a price alert."""
        alert = PriceAlertModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id),
            target_price=150.00,
            currency="USD",
            status="active"
        )
        db_session.add(alert)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/user/price-alerts/{alert.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get("/api/v1/user/price-alerts", headers=auth_headers)
        assert len(get_response.json()) == 0

class TestSavedSearches:
    """Test saved searches endpoints."""
    
    def test_create_saved_search(self, client, test_user, auth_headers, setup_database):
        """Test creating a saved search."""
        response = client.post(
            "/api/v1/user/saved-searches",
            json={
                "search_query": {
                    "destination": "Paris",
                    "check_in": "2025-12-01",
                    "check_out": "2025-12-05",
                    "guests": 2
                },
                "name": "Paris December Trip"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Paris December Trip"
        assert data["search_query"]["destination"] == "Paris"
    
    def test_get_saved_searches(self, client, test_user, auth_headers, db_session):
        """Test getting all saved searches."""
        search = SavedSearchModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            search_query={"destination": "Paris", "guests": 2},
            name="Paris Trip"
        )
        db_session.add(search)
        db_session.commit()
        
        response = client.get("/api/v1/user/saved-searches", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Paris Trip"
    
    def test_delete_saved_search(self, client, test_user, auth_headers, db_session):
        """Test deleting a saved search."""
        search = SavedSearchModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            search_query={"destination": "Paris"},
            name="Paris Trip"
        )
        db_session.add(search)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/user/saved-searches/{search.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get("/api/v1/user/saved-searches", headers=auth_headers)
        assert len(get_response.json()) == 0

class TestUserReviews:
    """Test user reviews endpoints."""
    
    def test_create_review(self, client, test_user, test_hotel, auth_headers, setup_database):
        """Test creating a review."""
        response = client.post(
            "/api/v1/user/reviews",
            json={
                "hotel_id": str(test_hotel.id),
                "rating": 5,
                "title": "Great hotel!",
                "text": "Had a wonderful stay."
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hotel_id"] == test_hotel.id
        assert data["rating"] == 5
        assert data["title"] == "Great hotel!"
    
    def test_get_reviews(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test getting reviews for a hotel."""
        review = UserReviewModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id),
            rating=5,
            title="Great hotel!",
            text="Had a wonderful stay.",
            published=True
        )
        db_session.add(review)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/user/reviews?hotel_id={str(test_hotel.id)}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["rating"] == 5
    
    def test_update_review(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test updating a review."""
        review = UserReviewModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id),
            rating=4,
            title="Good hotel",
            text="Nice stay.",
            published=False
        )
        db_session.add(review)
        db_session.commit()
        
        response = client.patch(
            f"/api/v1/user/reviews/{review.id}",
            json={
                "rating": 5,
                "title": "Excellent hotel!"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["rating"] == 5
        assert response.json()["title"] == "Excellent hotel!"
    
    def test_delete_review(self, client, test_user, test_hotel, auth_headers, db_session):
        """Test deleting a review."""
        review = UserReviewModel(
            id=str(uuid.uuid4()),
            user_id=str(test_user.id),
            hotel_id=str(test_hotel.id),
            rating=5,
            title="Great hotel!",
            text="Had a wonderful stay.",
            published=False
        )
        db_session.add(review)
        db_session.commit()
        
        response = client.delete(
            f"/api/v1/user/reviews/{review.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/user/reviews?hotel_id={str(test_hotel.id)}",
            headers=auth_headers
        )
        assert len(get_response.json()) == 0

