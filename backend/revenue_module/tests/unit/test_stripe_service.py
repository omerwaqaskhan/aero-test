"""Unit tests for StripeService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import os

from revenue_module.infrastructure.stripe_service import StripeService


class TestStripeService:
    """Test cases for StripeService."""
    
    @pytest.fixture
    def service(self):
        """Create StripeService instance."""
        return StripeService()
    
    @patch('revenue_module.infrastructure.stripe_service.stripe.Customer')
    def test_create_customer(self, mock_customer_class, service):
        """Test creating Stripe customer."""
        # Setup
        email = "test@example.com"
        name = "Test User"
        mock_customer = Mock()
        mock_customer.id = "cus_123"
        mock_customer.email = email
        mock_customer_class.create.return_value = mock_customer
        
        # Execute
        result = service.create_customer(email, name)
        
        # Assert
        assert result["customer_id"] == "cus_123"
        assert result["email"] == email
        mock_customer_class.create.assert_called_once_with(email=email, name=name)
    
    @patch('revenue_module.infrastructure.stripe_service.stripe.Subscription')
    def test_create_subscription(self, mock_subscription_class, service):
        """Test creating Stripe subscription."""
        # Setup
        customer_id = "cus_123"
        price_id = "price_123"
        metadata = {"user_id": "user_123"}
        
        mock_subscription = Mock()
        mock_subscription.id = "sub_123"
        mock_subscription.customer = customer_id
        mock_subscription.status = "active"
        mock_subscription.current_period_start = 1640995200
        mock_subscription.current_period_end = 1643587200
        mock_subscription_class.create.return_value = mock_subscription
        
        # Execute
        result = service.create_subscription(customer_id, price_id, metadata)
        
        # Assert
        assert result["subscription_id"] == "sub_123"
        assert result["customer_id"] == customer_id
        assert result["status"] == "active"
        mock_subscription_class.create.assert_called_once()
    
    @patch('revenue_module.infrastructure.stripe_service.stripe.Subscription')
    def test_cancel_subscription(self, mock_subscription_class, service):
        """Test canceling Stripe subscription."""
        # Setup
        subscription_id = "sub_123"
        mock_subscription = Mock()
        mock_subscription.id = subscription_id
        mock_subscription.cancel_at_period_end = True
        mock_subscription_class.modify.return_value = mock_subscription
        
        # Execute
        result = service.cancel_subscription(subscription_id)
        
        # Assert
        assert result["subscription_id"] == subscription_id
        assert result["cancel_at_period_end"] is True
        mock_subscription_class.modify.assert_called_once_with(
            subscription_id, cancel_at_period_end=True
        )
    
    @patch('revenue_module.infrastructure.stripe_service.stripe.PaymentIntent')
    def test_create_payment_intent(self, mock_payment_intent_class, service):
        """Test creating payment intent."""
        # Setup
        amount = Decimal("99.99")
        currency = "usd"
        customer_id = "cus_123"
        
        mock_intent = Mock()
        mock_intent.id = "pi_123"
        mock_intent.client_secret = "pi_123_secret"
        mock_intent.status = "requires_payment_method"
        mock_payment_intent_class.create.return_value = mock_intent
        
        # Execute
        result = service.create_payment_intent(amount, currency, customer_id)
        
        # Assert
        assert result["payment_intent_id"] == "pi_123"
        assert result["client_secret"] == "pi_123_secret"
        assert result["amount"] == amount
        mock_payment_intent_class.create.assert_called_once()
    
    @patch('revenue_module.infrastructure.stripe_service.stripe.Subscription')
    def test_get_subscription(self, mock_subscription_class, service):
        """Test getting Stripe subscription."""
        # Setup
        subscription_id = "sub_123"
        mock_subscription = Mock()
        mock_subscription.id = subscription_id
        mock_subscription.status = "active"
        mock_subscription.current_period_start = 1640995200
        mock_subscription.current_period_end = 1643587200
        mock_subscription_class.retrieve.return_value = mock_subscription
        
        # Execute
        result = service.get_subscription(subscription_id)
        
        # Assert
        assert result["subscription_id"] == subscription_id
        assert result["status"] == "active"
        mock_subscription_class.retrieve.assert_called_once_with(subscription_id)
    
    @patch('revenue_module.infrastructure.stripe_service.stripe.Webhook')
    def test_handle_webhook(self, mock_webhook_class, service):
        """Test handling Stripe webhook."""
        # Setup
        payload = b'{"type": "customer.subscription.created"}'
        signature = "test_signature"
        webhook_secret = "whsec_test"
        
        mock_event = {
            "type": "customer.subscription.created",
            "data": {"object": {"id": "sub_123"}}
        }
        mock_webhook_class.construct_event.return_value = mock_event
        
        # Execute
        result = service.handle_webhook(payload, signature, webhook_secret)
        
        # Assert
        assert result["type"] == "customer.subscription.created"
        assert result["data"]["object"]["id"] == "sub_123"
        mock_webhook_class.construct_event.assert_called_once()

