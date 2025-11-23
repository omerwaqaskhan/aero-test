"""Integration tests for revenue API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from auth_module.main import app
from revenue_module.infrastructure.db.models import (
    SubscriptionModel, LeadModel, HotelListingModel,
    SubscriptionTier, LeadStatus, ListingPackage
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    return session


class TestSubscriptionAPI:
    """Test subscription API endpoints."""
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.SubscriptionService')
    def test_create_subscription(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test creating subscription via API."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        mock_subscription = SubscriptionModel(
            id=str(uuid.uuid4()),
            user_id="user_123",
            tier=SubscriptionTier.PREMIUM,
            stripe_subscription_id="sub_123",
            stripe_customer_id="cus_123",
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            cancel_at_period_end=False
        )
        mock_service.create_subscription.return_value = mock_subscription
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/revenue/subscriptions?user_id=user_123",
            json={
                "tier": "premium",
                "stripe_subscription_id": "sub_123",
                "stripe_customer_id": "cus_123"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "premium"
        assert data["user_id"] == "user_123"
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.SubscriptionService')
    def test_get_user_subscription(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test getting user subscription via API."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        mock_subscription = SubscriptionModel(
            id=str(uuid.uuid4()),
            user_id="user_123",
            tier=SubscriptionTier.PREMIUM,
            status="active"
        )
        mock_service.get_user_subscription.return_value = mock_subscription
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/revenue/subscriptions/user_123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "premium"


class TestLeadAPI:
    """Test lead API endpoints."""
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.LeadService')
    def test_create_lead(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test creating lead via API."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        mock_lead = LeadModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            email="guest@example.com",
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=10),
            status=LeadStatus.SENT,
            lead_fee=Decimal("15.00")
        )
        mock_service.create_lead.return_value = mock_lead
        mock_service.mark_lead_sent = AsyncMock(return_value=mock_lead)
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/revenue/leads",
            json={
                "hotel_id": "hotel_123",
                "email": "guest@example.com",
                "check_in": str(date.today() + timedelta(days=7)),
                "check_out": str(date.today() + timedelta(days=10)),
                "name": "Guest User",
                "guests": 2,
                "rooms": 1
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "guest@example.com"
        assert data["status"] == "sent"
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.LeadService')
    def test_convert_lead(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test converting lead via API."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        mock_lead = LeadModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            email="guest@example.com",
            status=LeadStatus.BOOKED,
            booking_value=Decimal("500.00"),
            commission=Decimal("50.00")
        )
        mock_service.mark_lead_converted.return_value = mock_lead
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.post(
            "/api/v1/revenue/leads/lead_123/convert?booking_value=500.00"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["commission"] == 50.0


class TestAnalyticsAPI:
    """Test analytics API endpoints."""
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.RevenueAnalyticsService')
    def test_get_revenue_analytics(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test getting revenue analytics via API."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        mock_service.get_total_revenue.return_value = {
            "total_revenue": 150.0,
            "by_type": {
                "subscription": 100.0,
                "lead": 50.0
            },
            "period": {
                "start": None,
                "end": None
            }
        }
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/revenue/analytics")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_revenue"] == 150.0
        assert "subscription" in data["by_type"]
        assert "lead" in data["by_type"]
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.RevenueAnalyticsService')
    def test_get_monthly_revenue(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test getting monthly revenue via API."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        mock_service.get_monthly_revenue.return_value = [
            {
                "month": "2024-01",
                "revenue": {"subscription": 100.0},
                "total": 100.0
            }
        ]
        mock_service_class.return_value = mock_service
        
        # Execute
        response = client.get("/api/v1/revenue/analytics/monthly?months=12")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["month"] == "2024-01"

