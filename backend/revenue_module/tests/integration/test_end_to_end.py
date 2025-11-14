"""End-to-end tests for complete revenue system."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from auth_module.main import app


class TestEndToEndFlows:
    """Complete end-to-end tests for all revenue features."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        return session
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.SubscriptionService')
    @patch('revenue_module.domain.services.LeadService')
    @patch('revenue_module.domain.services.AdRevenueService')
    def test_complete_user_journey(
        self, mock_ad_service, mock_lead_service, mock_sub_service, 
        mock_get_db, client, mock_db_session
    ):
        """Test complete user journey: subscribe -> search -> create lead -> view ads."""
        # Setup mocks
        mock_get_db.return_value = mock_db_session
        
        # Mock subscription
        mock_sub = Mock()
        from revenue_module.infrastructure.db.models import SubscriptionModel, SubscriptionTier
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
        from revenue_module.infrastructure.db.models import LeadModel, LeadStatus
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
        
        # Mock ad service
        mock_ad = Mock()
        mock_ad_service.return_value = mock_ad
        
        # Execute: Get subscription
        sub_response = client.get("/api/v1/revenue/subscriptions/user_123")
        assert sub_response.status_code == 200
        assert sub_response.json()["tier"] == "premium"
        
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
        assert lead_response.status_code == 200
        assert lead_response.json()["status"] == "sent"
        
        # Execute: Record ad impression
        ad_response = client.post(
            "/api/v1/revenue/ads/impression",
            json={
                "ad_slot": "search_sidebar",
                "page_type": "search",
                "revenue": 0.01
            }
        )
        assert ad_response.status_code == 200
    
    @patch('revenue_module.api.routers.get_db')
    @patch('revenue_module.domain.services.HotelListingService')
    @patch('revenue_module.domain.services.SponsoredPlacementService')
    def test_hotel_owner_journey(
        self, mock_sponsor_service, mock_listing_service, 
        mock_get_db, client, mock_db_session
    ):
        """Test hotel owner journey: claim -> verify -> sponsor."""
        # Setup
        mock_get_db.return_value = mock_db_session
        
        # Mock listing service
        mock_listing = Mock()
        from revenue_module.infrastructure.db.models import HotelListingModel, ListingPackage
        mock_listing_obj = HotelListingModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            package=ListingPackage.ENHANCED,
            owner_email="owner@hotel.com",
            verified=False,
            status="pending",
            verification_token="test_token"
        )
        mock_listing.create_listing.return_value = mock_listing_obj
        mock_listing.verify_listing.return_value = mock_listing_obj
        mock_listing_service.return_value = mock_listing
        
        # Mock sponsorship service
        mock_sponsor = Mock()
        from revenue_module.infrastructure.db.models import SponsoredPlacementModel, SponsorshipStatus
        mock_sponsorship = SponsoredPlacementModel(
            id=str(uuid.uuid4()),
            hotel_id="hotel_123",
            priority=10,
            status=SponsorshipStatus.ACTIVE
        )
        mock_sponsor.create_sponsorship.return_value = mock_sponsorship
        mock_sponsor_service.return_value = mock_sponsor
        
        # Execute: Create listing
        listing_response = client.post(
            "/api/v1/revenue/listings",
            json={
                "hotel_id": "hotel_123",
                "package": "enhanced",
                "owner_email": "owner@hotel.com",
                "owner_name": "Hotel Owner"
            }
        )
        assert listing_response.status_code == 200
        
        # Execute: Verify listing
        verify_response = client.post(
            "/api/v1/revenue/listings/verify/test_token"
        )
        assert verify_response.status_code == 200
        
        # Execute: Create sponsorship
        sponsor_response = client.post(
            "/api/v1/revenue/sponsorships",
            json={
                "hotel_id": "hotel_123",
                "listing_id": mock_listing_obj.id,
                "priority": 10,
                "placement_type": "search_results",
                "start_date": str(datetime.utcnow()),
                "end_date": str(datetime.utcnow() + timedelta(days=30)),
                "amount": 100.0
            }
        )
        assert sponsor_response.status_code == 200
        assert sponsor_response.json()["priority"] == 10

