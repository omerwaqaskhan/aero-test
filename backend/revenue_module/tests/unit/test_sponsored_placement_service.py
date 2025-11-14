"""Unit tests for SponsoredPlacementService."""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from revenue_module.domain.services import SponsoredPlacementService
from revenue_module.infrastructure.db.models import (
    SponsoredPlacementModel, SponsorshipStatus
)


class TestSponsoredPlacementService:
    """Test cases for SponsoredPlacementService."""
    
    @pytest.fixture
    def service(self, mock_db_session):
        """Create SponsoredPlacementService instance."""
        return SponsoredPlacementService(mock_db_session)
    
    def test_create_sponsorship(self, service, mock_db_session):
        """Test creating sponsored placement."""
        # Setup
        hotel_id = str(uuid.uuid4())
        listing_id = str(uuid.uuid4())
        priority = 10
        placement_type = "search_results"
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        amount = Decimal("100.00")
        
        # Mock query for revenue transaction
        query_mock = Mock()
        mock_db_session.query.return_value = query_mock
        
        # Execute
        sponsorship = service.create_sponsorship(
            hotel_id=hotel_id,
            listing_id=listing_id,
            priority=priority,
            placement_type=placement_type,
            start_date=start_date,
            end_date=end_date,
            amount=amount
        )
        
        # Assert
        assert sponsorship is not None
        assert sponsorship.hotel_id == hotel_id
        assert sponsorship.listing_id == listing_id
        assert sponsorship.priority == priority
        assert sponsorship.placement_type == placement_type
        assert sponsorship.status == SponsorshipStatus.ACTIVE
        assert sponsorship.amount == amount
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()
    
    def test_get_active_sponsorships(self, service, mock_db_session):
        """Test getting active sponsorships."""
        # Setup
        sponsorship1 = SponsoredPlacementModel(
            id=str(uuid.uuid4()),
            hotel_id=str(uuid.uuid4()),
            priority=10,
            placement_type="search_results",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=29),
            status=SponsorshipStatus.ACTIVE,
            amount=Decimal("100.00")
        )
        
        sponsorship2 = SponsoredPlacementModel(
            id=str(uuid.uuid4()),
            hotel_id=str(uuid.uuid4()),
            priority=5,
            placement_type="search_results",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=29),
            status=SponsorshipStatus.ACTIVE,
            amount=Decimal("50.00")
        )
        
        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.filter.return_value.order_by.return_value.all.return_value = [sponsorship1, sponsorship2]
        query_mock.filter.return_value = filter_mock
        mock_db_session.query.return_value = query_mock
        
        # Execute
        results = service.get_active_sponsorships()
        
        # Assert
        assert len(results) == 2
        assert results[0].priority == 10  # Should be sorted by priority desc
    
    def test_get_active_sponsorships_by_type(self, service, mock_db_session):
        """Test getting active sponsorships filtered by type."""
        # Setup
        sponsorship = SponsoredPlacementModel(
            id=str(uuid.uuid4()),
            hotel_id=str(uuid.uuid4()),
            priority=10,
            placement_type="featured",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=29),
            status=SponsorshipStatus.ACTIVE,
            amount=Decimal("100.00")
        )
        
        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.filter.return_value.order_by.return_value.all.return_value = [sponsorship]
        query_mock.filter.return_value = filter_mock
        mock_db_session.query.return_value = query_mock
        
        # Execute
        results = service.get_active_sponsorships(placement_type="featured")
        
        # Assert
        assert len(results) == 1
        assert results[0].placement_type == "featured"

