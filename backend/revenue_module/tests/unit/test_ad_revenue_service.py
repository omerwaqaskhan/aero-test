"""Unit tests for AdRevenueService."""

import pytest
from unittest.mock import Mock
from datetime import date
from decimal import Decimal
import uuid

from revenue_module.domain.services import AdRevenueService
from revenue_module.infrastructure.db.models import AdRevenueModel


class TestAdRevenueService:
    """Test cases for AdRevenueService."""
    
    @pytest.fixture
    def service(self, mock_db_session):
        """Create AdRevenueService instance."""
        return AdRevenueService(mock_db_session)
    
    def test_record_impression_new(self, service, mock_db_session):
        """Test recording ad impression for new ad slot."""
        # Setup
        ad_slot = "search_sidebar"
        page_type = "search"
        revenue = Decimal("0.01")
        today = date.today()
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None  # No existing record
        mock_db_session.query.return_value = query_mock
        
        # Execute
        service.record_impression(ad_slot, page_type, revenue)
        
        # Assert
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_record_impression_existing(self, service, mock_db_session):
        """Test recording ad impression for existing ad slot."""
        # Setup
        ad_slot = "search_sidebar"
        page_type = "search"
        revenue = Decimal("0.01")
        today = date.today()
        
        existing_record = AdRevenueModel(
            id=str(uuid.uuid4()),
            ad_slot=ad_slot,
            page_type=page_type,
            impressions=10,
            clicks=2,
            revenue=Decimal("0.10"),
            date=today
        )
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = existing_record
        mock_db_session.query.return_value = query_mock
        
        # Execute
        service.record_impression(ad_slot, page_type, revenue)
        
        # Assert
        assert existing_record.impressions == 11
        assert existing_record.revenue == Decimal("0.11")
        mock_db_session.commit.assert_called()
    
    def test_record_click_new(self, service, mock_db_session):
        """Test recording ad click for new ad slot."""
        # Setup
        ad_slot = "hotel_details_sidebar"
        page_type = "hotel_details"
        revenue = Decimal("0.10")
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        # Execute
        service.record_click(ad_slot, page_type, revenue)
        
        # Assert
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_record_click_existing(self, service, mock_db_session):
        """Test recording ad click for existing ad slot."""
        # Setup
        ad_slot = "hotel_details_sidebar"
        page_type = "hotel_details"
        revenue = Decimal("0.10")
        today = date.today()
        
        existing_record = AdRevenueModel(
            id=str(uuid.uuid4()),
            ad_slot=ad_slot,
            page_type=page_type,
            impressions=50,
            clicks=5,
            revenue=Decimal("0.50"),
            date=today
        )
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = existing_record
        mock_db_session.query.return_value = query_mock
        
        # Execute
        service.record_click(ad_slot, page_type, revenue)
        
        # Assert
        assert existing_record.clicks == 6
        assert existing_record.revenue == Decimal("0.60")
        mock_db_session.commit.assert_called()

