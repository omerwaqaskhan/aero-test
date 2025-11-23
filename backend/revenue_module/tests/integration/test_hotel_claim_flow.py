"""Integration tests for hotel claim flow."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from auth_module.main import app
from revenue_module.infrastructure.db.models import (
    HotelListingModel, ListingPackage, ListingPaymentModel
)
from search_booking_module.infrastructure.db.models import HotelModel


class TestHotelClaimFlow:
    """Test hotel claim flow end-to-end."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_hotel(self):
        """Create mock hotel."""
        return HotelModel(
            id=str(uuid.uuid4()),
            provider_hotel_id="hotel_123",
            name="Test Hotel",
            city="New York",
            country="USA",
            latitude=40.7580,
            longitude=-73.9855,
            stars=4,
            rating=4.5
        )
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.HotelListingService')
    def test_create_listing_claim(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test creating hotel listing claim."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        
        mock_listing = HotelListingModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            package=ListingPackage.ENHANCED,
            owner_email="owner@hotel.com",
            owner_name="Hotel Owner",
            verified=False,
            status="pending",
            verification_token="test_token_123"
        )
        
        mock_service.create_listing.return_value = mock_listing
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/revenue/listings",
            json={
                "hotel_id": "hotel_123",
                "package": "enhanced",
                "owner_email": "owner@hotel.com",
                "owner_name": "Hotel Owner",
                "owner_phone": "+1234567890"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["hotel_id"] == "hotel_123"
        assert data["package"] == "enhanced"
        assert data["owner_email"] == "owner@hotel.com"
        assert data["verified"] is False
        assert data["status"] == "pending"
        assert "verification_token" in data or data.get("verification_token") is not None
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.HotelListingService')
    def test_verify_listing(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test verifying hotel listing."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        
        mock_listing = HotelListingModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            package=ListingPackage.ENHANCED,
            owner_email="owner@hotel.com",
            verified=True,
            status="active",
            verification_token=None
        )
        
        mock_service.verify_listing.return_value = mock_listing
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/revenue/listings/verify/test_token_123"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "listing_id" in data
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.HotelListingService')
    def test_verify_listing_invalid_token(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test verifying with invalid token."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        mock_service.verify_listing.return_value = None
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/revenue/listings/verify",
            params={"token": "invalid_token"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.HotelListingService')
    def test_listing_creation_with_package(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test creating listing with different packages."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        
        mock_listing = HotelListingModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            package=ListingPackage.PREMIUM,
            owner_email="owner@hotel.com",
            verified=False,
            status="pending"
        )
        
        mock_service.create_listing.return_value = mock_listing
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/revenue/listings",
            json={
                "hotel_id": "hotel_123",
                "package": "premium",
                "owner_email": "owner@hotel.com",
                "owner_name": "Hotel Owner"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["package"] == "premium"

