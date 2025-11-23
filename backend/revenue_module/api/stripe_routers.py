"""Stripe webhook router."""

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import Response
import os
import logging
from datetime import datetime, timedelta

from revenue_module.infrastructure.stripe_service import StripeService
from revenue_module.domain.services import (
    SubscriptionService, HotelListingService
)
from revenue_module.infrastructure.db.models import SubscriptionModel
from auth_module.infrastructure.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/revenue/stripe", tags=["stripe"])
logger = logging.getLogger(__name__)

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    
    try:
        event = StripeService.handle_webhook(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    # Handle subscription events
    if event_type == "customer.subscription.created":
        subscription_id = event_data["id"]
        customer_id = event_data["customer"]
        # Subscription creation handled by create_subscription endpoint
        pass
    
    elif event_type == "customer.subscription.updated":
        subscription_id = event_data["id"]
        status = event_data["status"]
        # Update subscription status in database
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.stripe_subscription_id == subscription_id
        ).first()
        if subscription:
            subscription.status = status
            db.commit()
    
    elif event_type == "invoice.payment_succeeded":
        subscription_id = event_data.get("subscription")
        amount = event_data["amount_paid"] / 100  # Convert from cents
        payment_intent_id = event_data.get("payment_intent")
        
        if subscription_id:
            subscription_service = SubscriptionService(db)
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.stripe_subscription_id == subscription_id
            ).first()
            if subscription:
                subscription_service.record_payment(
                    subscription_id=subscription.id,
                    stripe_payment_intent_id=payment_intent_id,
                    amount=amount,
                    currency="USD",
                    status="succeeded"
                )
    
    elif event_type == "payment_intent.succeeded":
        payment_intent_id = event_data["id"]
        amount = event_data["amount"] / 100
        metadata = event_data.get("metadata", {})
        
        # Handle listing payment
        if metadata.get("type") == "listing":
            listing_id = metadata.get("listing_id")
            if listing_id:
                listing_service = HotelListingService(db)
                listing_service.record_listing_payment(
                    listing_id=listing_id,
                    stripe_payment_intent_id=payment_intent_id,
                    amount=amount,
                    currency="USD",
                    status="succeeded",
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow() + timedelta(days=30)
                )
    
    return Response(status_code=200)

