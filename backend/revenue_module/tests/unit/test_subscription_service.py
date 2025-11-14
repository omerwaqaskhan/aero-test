"""Unit tests for SubscriptionService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from revenue_module.domain.services import SubscriptionService
from revenue_module.infrastructure.db.models import (
    SubscriptionModel, SubscriptionTier, SubscriptionPaymentModel
)


class TestSubscriptionService:
    """Test cases for SubscriptionService."""
    
    @pytest.fixture
    def service(self, mock_db_session):
        """Create SubscriptionService instance."""
        return SubscriptionService(mock_db_session)
    
    def test_get_user_subscription_active(self, service, mock_db_session, mock_subscription):
        """Test getting active subscription for user."""
        # Setup
        user_id = mock_subscription.user_id
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = mock_subscription
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.get_user_subscription(user_id)
        
        # Assert
        assert result is not None
        assert result.id == mock_subscription.id
        assert result.user_id == user_id
        assert result.tier == SubscriptionTier.PREMIUM
        mock_db_session.query.assert_called_once_with(SubscriptionModel)
    
    def test_get_user_subscription_none(self, service, mock_db_session):
        """Test getting subscription when user has none."""
        # Setup
        user_id = str(uuid.uuid4())
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.get_user_subscription(user_id)
        
        # Assert
        assert result is None
    
    def test_create_subscription(self, service, mock_db_session):
        """Test creating new subscription."""
        # Setup
        user_id = str(uuid.uuid4())
        tier = SubscriptionTier.PREMIUM
        stripe_sub_id = "sub_123"
        stripe_customer_id = "cus_123"
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)
        
        # Mock the query for revenue transaction
        query_mock = Mock()
        mock_db_session.query.return_value = query_mock
        
        # Execute
        subscription = service.create_subscription(
            user_id=user_id,
            tier=tier,
            stripe_subscription_id=stripe_sub_id,
            stripe_customer_id=stripe_customer_id,
            period_start=period_start,
            period_end=period_end
        )
        
        # Assert
        assert subscription is not None
        assert subscription.user_id == user_id
        assert subscription.tier == tier
        assert subscription.stripe_subscription_id == stripe_sub_id
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()
    
    def test_cancel_subscription(self, service, mock_db_session, mock_subscription):
        """Test canceling subscription."""
        # Setup
        subscription_id = mock_subscription.id
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = mock_subscription
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.cancel_subscription(subscription_id)
        
        # Assert
        assert result is not None
        assert result.cancel_at_period_end is True
        assert result.canceled_at is not None
        mock_db_session.commit.assert_called()
    
    def test_cancel_subscription_not_found(self, service, mock_db_session):
        """Test canceling non-existent subscription."""
        # Setup
        subscription_id = str(uuid.uuid4())
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = query_mock
        
        # Execute
        result = service.cancel_subscription(subscription_id)
        
        # Assert
        assert result is None
    
    def test_record_payment(self, service, mock_db_session):
        """Test recording subscription payment."""
        # Setup
        subscription_id = str(uuid.uuid4())
        payment_intent_id = "pi_123"
        amount = Decimal("9.99")
        currency = "USD"
        status = "succeeded"
        
        # Execute
        payment = service.record_payment(
            subscription_id=subscription_id,
            stripe_payment_intent_id=payment_intent_id,
            amount=amount,
            currency=currency,
            status=status
        )
        
        # Assert
        assert payment is not None
        assert payment.subscription_id == subscription_id
        assert payment.amount == amount
        assert payment.status == status
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()
    
    def test_record_payment_pending(self, service, mock_db_session):
        """Test recording pending payment."""
        # Setup
        subscription_id = str(uuid.uuid4())
        payment_intent_id = "pi_123"
        amount = Decimal("9.99")
        status = "pending"
        
        # Execute
        payment = service.record_payment(
            subscription_id=subscription_id,
            stripe_payment_intent_id=payment_intent_id,
            amount=amount,
            currency="USD",
            status=status
        )
        
        # Assert
        assert payment is not None
        assert payment.paid_at is None  # Should be None for pending

