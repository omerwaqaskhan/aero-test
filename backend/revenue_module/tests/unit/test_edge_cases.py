"""Unit tests for edge cases and error handling."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from revenue_module.domain.services import (
    SubscriptionService, LeadService, HotelListingService,
    SponsoredPlacementService, AdRevenueService, RevenueAnalyticsService
)
from revenue_module.infrastructure.db.models import (
    SubscriptionModel, LeadModel, HotelListingModel,
    SubscriptionTier, LeadStatus, ListingPackage
)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        return session
    
    def test_subscription_service_empty_revenue_transaction(self, mock_db_session):
        """Test subscription creation with empty revenue transaction."""
        service = SubscriptionService(mock_db_session)
        
        # Mock query to return None (no existing transactions)
        query_mock = Mock()
        mock_db_session.query.return_value = query_mock
        
        # Should not fail even if revenue transaction query fails
        subscription = service.create_subscription(
            user_id=str(uuid.uuid4()),
            tier=SubscriptionTier.FREE,
            stripe_subscription_id="sub_123",
            stripe_customer_id="cus_123",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        assert subscription is not None
    
    @pytest.mark.asyncio
    async def test_lead_service_email_failure_doesnt_break(self, mock_db_session):
        """Test that email failure doesn't break lead creation."""
        service = LeadService(mock_db_session)
        
        # Create lead
        lead = service.create_lead(
            hotel_id=str(uuid.uuid4()),
            email="test@example.com",
            check_in=date.today() + timedelta(days=7),
            check_out=date.today() + timedelta(days=10)
        )
        
        # Mock email service to raise exception
        with patch('revenue_module.domain.services.EmailService') as mock_email:
            mock_email.return_value.send_email = AsyncMock(side_effect=Exception("Email failed"))
            
            # Should not raise exception
            result = await service.mark_lead_sent(lead.id)
            
            # Lead should still be marked as sent
            assert result.status == LeadStatus.SENT
    
    def test_listing_service_invalid_verification_token(self, mock_db_session):
        """Test listing verification with invalid token."""
        service = HotelListingService(mock_db_session)
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        result = service.verify_listing("invalid_token")
        assert result is None
    
    def test_sponsored_placement_service_no_active_sponsorships(self, mock_db_session):
        """Test getting active sponsorships when none exist."""
        service = SponsoredPlacementService(mock_db_session)
        
        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.filter.return_value.order_by.return_value.all.return_value = []
        query_mock.filter.return_value = filter_mock
        mock_db_session.query.return_value = query_mock
        
        results = service.get_active_sponsorships()
        assert len(results) == 0
    
    def test_ad_revenue_service_zero_revenue(self, mock_db_session):
        """Test recording ad with zero revenue."""
        service = AdRevenueService(mock_db_session)
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        # Should handle zero revenue gracefully
        service.record_impression("test_slot", "test_page", Decimal("0.00"))
        mock_db_session.add.assert_called()
    
    def test_analytics_service_no_data(self, mock_db_session):
        """Test analytics with no revenue data."""
        service = RevenueAnalyticsService(mock_db_session)
        
        query_mock = Mock()
        query_mock.filter.return_value.group_by.return_value.all.return_value = []
        mock_db_session.query.return_value = query_mock
        
        result = service.get_total_revenue()
        assert result["total_revenue"] == 0.0
        assert result["by_type"] == {}
    
    def test_subscription_service_cancel_already_canceled(self, mock_db_session):
        """Test canceling already canceled subscription."""
        service = SubscriptionService(mock_db_session)
        
        subscription = SubscriptionModel(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            tier=SubscriptionTier.PREMIUM,
            cancel_at_period_end=True,
            canceled_at=datetime.utcnow() - timedelta(days=1)
        )
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = subscription
        mock_db_session.query.return_value = query_mock
        
        result = service.cancel_subscription(subscription.id)
        assert result.cancel_at_period_end is True
    
    def test_lead_service_convert_with_zero_booking_value(self, mock_db_session):
        """Test converting lead with zero booking value."""
        service = LeadService(mock_db_session)
        
        lead = LeadModel(
            id=str(uuid.uuid4()),
            hotel_id=str(uuid.uuid4()),
            email="test@example.com",
            check_in=date.today(),
            check_out=date.today() + timedelta(days=1),
            status=LeadStatus.SENT
        )
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = lead
        mock_db_session.query.return_value = query_mock
        
        result = service.mark_lead_converted(lead.id, Decimal("0.00"))
        assert result.commission == Decimal("0.00")

