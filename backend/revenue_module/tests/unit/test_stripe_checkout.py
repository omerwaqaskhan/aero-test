"""Unit tests for Stripe checkout functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from revenue_module.api.routers import router
from revenue_module.infrastructure.stripe_service import StripeService


class TestStripeCheckout:
    """Test cases for Stripe checkout endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from auth_module.main import app
        return TestClient(app)
    
    @patch('revenue_module.api.routers.stripe')
    @patch('revenue_module.api.routers.StripeService')
    def test_create_checkout_session_success(self, mock_stripe_service, mock_stripe, client):
        """Test successful checkout session creation."""
        # Setup
        mock_stripe.checkout.Session.create.return_value = MagicMock(
            id="cs_test_123",
            url="https://checkout.stripe.com/test",
            customer="cus_test_123"
        )
        
        mock_stripe_service.SUBSCRIPTION_PRICES = {
            "premium": "price_premium_123",
            "pro": "price_pro_123"
        }
        
        mock_stripe_service.create_customer.return_value = {
            "customer_id": "cus_test_123",
            "email": "test@example.com"
        }
        
        # Execute
        response = client.post(
            "/api/v1/revenue/checkout/create-session",
            params={
                "tier": "premium",
                "user_id": "user_123",
                "user_email": "test@example.com",
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "url" in data
        assert "customer_id" in data
        assert data["session_id"] == "cs_test_123"
        assert data["url"] == "https://checkout.stripe.com/test"
    
    @patch('revenue_module.api.routers.stripe')
    @patch('revenue_module.api.routers.StripeService')
    def test_create_checkout_session_invalid_tier(self, mock_stripe_service, mock_stripe, client):
        """Test checkout session with invalid tier."""
        # Setup
        mock_stripe_service.SUBSCRIPTION_PRICES = {
            "premium": "price_premium_123",
            "pro": "price_pro_123"
        }
        
        # Execute
        response = client.post(
            "/api/v1/revenue/checkout/create-session",
            params={
                "tier": "invalid_tier",
                "user_id": "user_123",
                "user_email": "test@example.com",
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel"
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert "Invalid tier" in response.json()["detail"]
    
    @patch('revenue_module.api.routers.stripe')
    @patch('revenue_module.api.routers.StripeService')
    def test_create_checkout_session_stripe_error(self, mock_stripe_service, mock_stripe, client):
        """Test checkout session when Stripe API fails."""
        # Setup
        mock_stripe_service.SUBSCRIPTION_PRICES = {
            "premium": "price_premium_123"
        }
        mock_stripe_service.create_customer.return_value = {
            "customer_id": "cus_test_123",
            "email": "test@example.com"
        }
        mock_stripe.checkout.Session.create.side_effect = Exception("Stripe API error")
        
        # Execute
        response = client.post(
            "/api/v1/revenue/checkout/create-session",
            params={
                "tier": "premium",
                "user_id": "user_123",
                "user_email": "test@example.com",
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel"
            }
        )
        
        # Assert
        assert response.status_code == 500
        assert "Failed to create checkout session" in response.json()["detail"]
    
    @patch('revenue_module.api.routers.stripe')
    @patch('revenue_module.api.routers.StripeService')
    def test_create_checkout_session_metadata(self, mock_stripe_service, mock_stripe, client):
        """Test checkout session includes correct metadata."""
        # Setup
        mock_session = MagicMock(
            id="cs_test_123",
            url="https://checkout.stripe.com/test",
            customer="cus_test_123"
        )
        mock_stripe.checkout.Session.create.return_value = mock_session
        
        mock_stripe_service.SUBSCRIPTION_PRICES = {
            "premium": "price_premium_123"
        }
        mock_stripe_service.create_customer.return_value = {
            "customer_id": "cus_test_123",
            "email": "test@example.com"
        }
        
        # Execute
        response = client.post(
            "/api/v1/revenue/checkout/create-session",
            params={
                "tier": "premium",
                "user_id": "user_123",
                "user_email": "test@example.com",
                "success_url": "http://localhost:3000/success",
                "cancel_url": "http://localhost:3000/cancel"
            }
        )
        
        # Assert
        assert response.status_code == 200
        # Verify metadata was passed to Stripe
        call_args = mock_stripe.checkout.Session.create.call_args
        assert call_args[1]["metadata"]["user_id"] == "user_123"
        assert call_args[1]["metadata"]["tier"] == "premium"

