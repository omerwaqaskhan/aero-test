"""Unit tests for LeadService."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, timedelta
from decimal import Decimal
import uuid

from revenue_module.domain.services import LeadService
from revenue_module.infrastructure.db.models import LeadModel, LeadStatus


class TestLeadService:
    """Test cases for LeadService."""
    
    @pytest.fixture
    def service(self, mock_db_session):
        """Create LeadService instance."""
        return LeadService(mock_db_session)
    
    def test_create_lead(self, service, mock_db_session):
        """Test creating new lead."""
        # Setup
        hotel_id = str(uuid.uuid4())
        email = "guest@example.com"
        check_in = date.today() + timedelta(days=7)
        check_out = date.today() + timedelta(days=10)
        name = "Guest User"
        phone = "+1234567890"
        guests = 2
        rooms = 1
        
        # Mock query for revenue transaction
        query_mock = Mock()
        mock_db_session.query.return_value = query_mock
        
        # Execute
        lead = service.create_lead(
            hotel_id=hotel_id,
            email=email,
            check_in=check_in,
            check_out=check_out,
            name=name,
            phone=phone,
            guests=guests,
            rooms=rooms
        )
        
        # Assert
        assert lead is not None
        assert lead.hotel_id == hotel_id
        assert lead.email == email
        assert lead.check_in == check_in
        assert lead.check_out == check_out
        assert lead.name == name
        assert lead.phone == phone
        assert lead.guests == guests
        assert lead.rooms == rooms
        assert lead.status == LeadStatus.NEW
        assert lead.lead_fee == Decimal("15.00")
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()
    
    @pytest.mark.asyncio
    async def test_mark_lead_sent(self, service, mock_db_session, mock_lead):
        """Test marking lead as sent."""
        # Setup
        lead_id = mock_lead.id
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = mock_lead
        mock_db_session.query.return_value = query_mock
        
        # Mock email service
        with patch('revenue_module.domain.services.EmailService') as mock_email_service:
            mock_email = Mock()
            mock_email.send_email = AsyncMock(return_value=True)
            mock_email_service.return_value = mock_email
            
            # Execute
            result = await service.mark_lead_sent(lead_id)
            
            # Assert
            assert result is not None
            assert result.status == LeadStatus.SENT
            assert result.sent_to_hotel_at is not None
            mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_mark_lead_sent_not_found(self, service, mock_db_session):
        """Test marking non-existent lead as sent."""
        # Setup
        lead_id = str(uuid.uuid4())
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = await service.mark_lead_sent(lead_id)
        
        # Assert
        assert result is None
    
    def test_mark_lead_converted(self, service, mock_db_session, mock_lead):
        """Test marking lead as converted."""
        # Setup
        lead_id = mock_lead.id
        booking_value = Decimal("500.00")
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = mock_lead
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.mark_lead_converted(lead_id, booking_value)
        
        # Assert
        assert result is not None
        assert result.status == LeadStatus.BOOKED
        assert result.booking_value == booking_value
        assert result.commission == booking_value * Decimal("0.10")  # 10% commission
        assert result.converted_at is not None
        mock_db_session.commit.assert_called()
    
    def test_mark_lead_converted_not_found(self, service, mock_db_session):
        """Test converting non-existent lead."""
        # Setup
        lead_id = str(uuid.uuid4())
        booking_value = Decimal("500.00")
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.mark_lead_converted(lead_id, booking_value)
        
        # Assert
        assert result is None

