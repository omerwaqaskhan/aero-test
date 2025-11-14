"""Integration tests for complete revenue flows."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from auth_module.main import app
from revenue_module.infrastructure.db.models import (
    SubscriptionModel, LeadModel, HotelListingModel,
    SubscriptionTier, LeadStatus, ListingPackage
)


class TestCompleteFlows:
    """Test complete end-to-end revenue flows."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.SubscriptionService')
    @patch('revenue_module.domain.services.LeadService')
    def test_subscription_to_lead_flow(self, mock_lead_service, mock_sub_service, mock_get_db, client, mock_db_session):
        """Test complete flow: user subscribes, then creates lead."""
        # Setup
        mock_get_db.return_value = mock_db_session
        
        # Mock subscription
        mock_sub = Mock()
        mock_subscription = SubscriptionModel(
            id=str(uuid.uuid4()),
            user_id="user_123",
            tier=SubscriptionTier.PREMIUM,
            status="active"
        )
        mock_sub.get_user_subscription.return_value = mock_subscription
        mock_sub_service.return_value = mock_sub
        
        # Mock lead service
        mock_lead = Mock()
        mock_lead_obj = LeadModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            email="user@example.com",
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=10),
            status=LeadStatus.SENT,
            lead_fee=Decimal("15.00")
        )
        mock_lead.create_lead.return_value = mock_lead_obj
        mock_lead.mark_lead_sent = AsyncMock(return_value=mock_lead_obj)
        mock_lead_service.return_value = mock_lead
        
        # Execute: Get subscription
        sub_response = client.get("/api/v1/revenue/subscriptions/user_123")
        assert sub_response.status_code == 200
        
        # Execute: Create lead
        lead_response = client.post(
            "/api/v1/revenue/leads",
            json={
                "hotel_id": "hotel_123",
                "email": "user@example.com",
                "check_in": str(date.today() + timedelta(days=7)),
                "check_out": str(date.today() + timedelta(days=10)),
                "name": "Test User",
                "guests": 2,
                "rooms": 1
            }
        )
        
        # Assert
        assert lead_response.status_code == 200
        data = lead_response.json()
        assert data["email"] == "user@example.com"
        assert data["status"] == "sent"
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.LeadService')
    def test_lead_conversion_flow(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test lead creation to conversion flow."""
        # Setup
        mock_get_db.return_value = mock_db_session
        mock_service = Mock()
        
        # Create lead
        mock_lead_new = LeadModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            email="guest@example.com",
            check_in=date.today(),
            check_out=date.today() + timedelta(days=1),
            status=LeadStatus.SENT
        )
        mock_service.create_lead.return_value = mock_lead_new
        mock_service.mark_lead_sent = AsyncMock(return_value=mock_lead_new)
        
        # Convert lead
        mock_lead_converted = LeadModel(
            id=mock_lead_new.id,
            hotel_id="hotel_123",
            email="guest@example.com",
            status=LeadStatus.BOOKED,
            booking_value=Decimal("500.00"),
            commission=Decimal("50.00")
        )
        mock_service.mark_lead_converted.return_value = mock_lead_converted
        mock_service_class.return_value = mock_service
        
        # Execute: Create lead
        create_response = client.post(
            "/api/v1/revenue/leads",
            json={
                "hotel_id": "hotel_123",
                "email": "guest@example.com",
                "check_in": str(date.today()),
                "check_out": str(date.today() + timedelta(days=1))
            }
        )
        assert create_response.status_code == 200
        lead_id = create_response.json()["id"]
        
        # Execute: Convert lead
        convert_response = client.post(
            f"/api/v1/revenue/leads/{lead_id}/convert",
            params={"booking_value": 500.00}
        )
        
        # Assert
        assert convert_response.status_code == 200
        data = convert_response.json()
        assert data["commission"] == 50.0
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.RevenueAnalyticsService')
    def test_analytics_flow(self, mock_service_class, mock_get_db, client, mock_db_session):
        """Test revenue analytics flow."""
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
        
        mock_service.get_monthly_revenue.return_value = [
            {
                "month": "2024-01",
                "revenue": {"subscription": 100.0},
                "total": 100.0
            }
        ]
        
        mock_service_class.return_value = mock_service
        
        # Execute: Get total revenue
        total_response = client.get("/api/v1/revenue/analytics")
        assert total_response.status_code == 200
        total_data = total_response.json()
        assert total_data["total_revenue"] == 150.0
        
        # Execute: Get monthly revenue
        monthly_response = client.get("/api/v1/revenue/analytics/monthly?months=12")
        assert monthly_response.status_code == 200
        monthly_data = monthly_response.json()
        assert len(monthly_data) > 0

