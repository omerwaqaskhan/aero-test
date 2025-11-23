"""Unit tests for HotelListingService."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from revenue_module.domain.services import HotelListingService
from revenue_module.infrastructure.db.models import (
    HotelListingModel, ListingPackage, ListingPaymentModel
)


class TestHotelListingService:
    """Test cases for HotelListingService."""
    
    @pytest.fixture
    def service(self, mock_db_session):
        """Create HotelListingService instance."""
        return HotelListingService(mock_db_session)
    
    def test_create_listing(self, service, mock_db_session):
        """Test creating hotel listing."""
        # Setup
        hotel_id = str(uuid.uuid4())
        package = ListingPackage.ENHANCED
        owner_email = "owner@hotel.com"
        owner_name = "Hotel Owner"
        owner_phone = "+1234567890"
        
        # Mock query for revenue transaction
        query_mock = Mock()
        mock_db_session.query.return_value = query_mock
        
        # Execute
        listing = service.create_listing(
            hotel_id=hotel_id,
            package=package,
            owner_email=owner_email,
            owner_name=owner_name,
            owner_phone=owner_phone
        )
        
        # Assert
        assert listing is not None
        assert listing.hotel_id == hotel_id
        assert listing.package == package
        assert listing.owner_email == owner_email
        assert listing.owner_name == owner_name
        assert listing.owner_phone == owner_phone
        assert listing.verified is False
        assert listing.verification_token is not None
        assert listing.status == "pending"
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()
    
    def test_verify_listing(self, service, mock_db_session, mock_listing):
        """Test verifying hotel listing."""
        # Setup
        verification_token = "test_token_123"
        mock_listing.verification_token = verification_token
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = mock_listing
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.verify_listing(verification_token)
        
        # Assert
        assert result is not None
        assert result.verified is True
        assert result.status == "active"
        assert result.verification_token is None
        mock_db_session.commit.assert_called()
    
    def test_verify_listing_invalid_token(self, service, mock_db_session):
        """Test verifying with invalid token."""
        # Setup
        verification_token = "invalid_token"
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.verify_listing(verification_token)
        
        # Assert
        assert result is None
    
    def test_upgrade_listing(self, service, mock_db_session, mock_listing):
        """Test upgrading listing package."""
        # Setup
        listing_id = mock_listing.id
        new_package = ListingPackage.PREMIUM
        stripe_customer_id = "cus_123"
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = mock_listing
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.upgrade_listing(
            listing_id=listing_id,
            new_package=new_package,
            stripe_customer_id=stripe_customer_id,
            period_start=period_start,
            period_end=period_end
        )
        
        # Assert
        assert result is not None
        assert result.package == new_package
        assert result.stripe_customer_id == stripe_customer_id
        assert result.status == "active"
        mock_db_session.commit.assert_called()
    
    def test_record_listing_payment(self, service, mock_db_session):
        """Test recording listing payment."""
        # Setup
        listing_id = str(uuid.uuid4())
        payment_intent_id = "pi_123"
        amount = Decimal("99.00")
        currency = "USD"
        status = "succeeded"
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        # Execute
        payment = service.record_listing_payment(
            listing_id=listing_id,
            stripe_payment_intent_id=payment_intent_id,
            amount=amount,
            currency=currency,
            status=status,
            period_start=period_start,
            period_end=period_end
        )
        
        # Assert
        assert payment is not None
        assert payment.listing_id == listing_id
        assert payment.amount == amount
        assert payment.status == status
        assert payment.period_start == period_start
        assert payment.period_end == period_end
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()

