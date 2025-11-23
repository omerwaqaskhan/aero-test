"""Unit tests for RevenueAnalyticsService."""

import pytest
from unittest.mock import Mock
from datetime import date, timedelta
from decimal import Decimal

from revenue_module.domain.services import RevenueAnalyticsService
from revenue_module.infrastructure.db.models import RevenueTransactionModel


class TestRevenueAnalyticsService:
    """Test cases for RevenueAnalyticsService."""
    
    @pytest.fixture
    def service(self, mock_db_session):
        """Create RevenueAnalyticsService instance."""
        return RevenueAnalyticsService(mock_db_session)
    
    def test_get_total_revenue(self, service, mock_db_session):
        """Test getting total revenue by type."""
        # Setup
        from sqlalchemy import func
        
        # Mock query result
        mock_result1 = Mock()
        mock_result1.revenue_type = "subscription"
        mock_result1.total = Decimal("100.00")
        
        mock_result2 = Mock()
        mock_result2.revenue_type = "lead"
        mock_result2.total = Decimal("50.00")
        
        query_mock = Mock()
        query_mock.filter.return_value.group_by.return_value.all.return_value = [
            mock_result1, mock_result2
        ]
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.get_total_revenue()
        
        # Assert
        assert result["total_revenue"] == 150.0
        assert result["by_type"]["subscription"] == 100.0
        assert result["by_type"]["lead"] == 50.0
    
    def test_get_total_revenue_with_dates(self, service, mock_db_session):
        """Test getting total revenue with date range."""
        # Setup
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        mock_result = Mock()
        mock_result.revenue_type = "subscription"
        mock_result.total = Decimal("200.00")
        
        query_mock = Mock()
        filter_mock = Mock()
        filter_mock.filter.return_value.group_by.return_value.all.return_value = [mock_result]
        query_mock.filter.return_value = filter_mock
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.get_total_revenue(start_date=start_date, end_date=end_date)
        
        # Assert
        assert result["total_revenue"] == 200.0
        assert result["period"]["start"] == start_date.isoformat()
        assert result["period"]["end"] == end_date.isoformat()
    
    def test_get_monthly_revenue(self, service, mock_db_session):
        """Test getting monthly revenue breakdown."""
        # Setup
        from datetime import datetime
        
        mock_result1 = Mock()
        mock_result1.month = datetime(2024, 1, 1)
        mock_result1.revenue_type = "subscription"
        mock_result1.total = Decimal("100.00")
        
        mock_result2 = Mock()
        mock_result2.month = datetime(2024, 1, 1)
        mock_result2.revenue_type = "lead"
        mock_result2.total = Decimal("50.00")
        
        query_mock = Mock()
        query_mock.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            mock_result1, mock_result2
        ]
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.get_monthly_revenue(months=12)
        
        # Assert
        assert len(result) > 0
        assert "2024-01" in [item["month"] for item in result]

