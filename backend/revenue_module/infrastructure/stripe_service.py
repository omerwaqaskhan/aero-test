"""Stripe integration service."""

import stripe
from typing import Optional, Dict, Any
from decimal import Decimal
import os

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class StripeService:
    """Service for Stripe payment processing."""
    
    SUBSCRIPTION_PRICES = {
        "premium": os.getenv("STRIPE_PREMIUM_PRICE_ID", "price_premium"),
        "pro": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro")
    }
    
    LISTING_PRICES = {
        "enhanced": os.getenv("STRIPE_ENHANCED_PRICE_ID", "price_enhanced"),
        "premium": os.getenv("STRIPE_PREMIUM_LISTING_PRICE_ID", "price_premium_listing")
    }
    
    @staticmethod
    def create_customer(email: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Create Stripe customer."""
        customer = stripe.Customer.create(
            email=email,
            name=name
        )
        return {
            "customer_id": customer.id,
            "email": customer.email
        }
    
    @staticmethod
    def create_subscription(
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create Stripe subscription."""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata=metadata or {}
        )
        return {
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end
        }
    
    @staticmethod
    def cancel_subscription(subscription_id: str) -> Dict[str, Any]:
        """Cancel Stripe subscription."""
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return {
            "subscription_id": subscription.id,
            "cancel_at_period_end": subscription.cancel_at_period_end
        }
    
    @staticmethod
    def create_payment_intent(
        amount: Decimal,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create payment intent for one-time payment."""
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            customer=customer_id,
            metadata=metadata or {}
        )
        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "amount": amount,
            "currency": currency,
            "status": intent.status
        }
    
    @staticmethod
    def get_subscription(subscription_id: str) -> Dict[str, Any]:
        """Get Stripe subscription."""
        subscription = stripe.Subscription.retrieve(subscription_id)
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end
        }
    
    @staticmethod
    def handle_webhook(payload: bytes, signature: str, webhook_secret: str) -> Dict[str, Any]:
        """Handle Stripe webhook."""
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        return {
            "type": event["type"],
            "data": event["data"]
        }

