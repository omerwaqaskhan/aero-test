"""FastAPI routers for revenue module."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from auth_module.infrastructure.db.database import get_db
from revenue_module.api.schemas import (
    CreateSubscriptionRequest, SubscriptionResponse,
    CreateLeadRequest, LeadResponse,
    CreateListingRequest, ListingResponse,
    CreateSponsorshipRequest, SponsorshipResponse,
    AdImpressionRequest, AdClickRequest,
    RevenueAnalyticsResponse, MonthlyRevenueResponse,
    OwnerListingResponse, OwnerLeadResponse
)
from revenue_module.domain.services import (
    SubscriptionService, LeadService, HotelListingService,
    SponsoredPlacementService, AdRevenueService, RevenueAnalyticsService
)
from revenue_module.infrastructure.db.models import (
    SubscriptionTier, ListingPackage
)
from revenue_module.api.stripe_routers import router as stripe_router
from revenue_module.infrastructure.stripe_service import StripeService
from auth_module.core.rate_limiter import rate_limit

router = APIRouter(prefix="/api/v1/revenue", tags=["revenue"])

# Include Stripe router
router.include_router(stripe_router)


# Subscription endpoints
@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Create user subscription."""
    service = SubscriptionService(db)
    
    from datetime import timedelta
    period_start = datetime.utcnow()
    period_end = period_start + timedelta(days=30)
    
    subscription = service.create_subscription(
        user_id=user_id,
        tier=SubscriptionTier(request.tier.value),
        stripe_subscription_id=request.stripe_subscription_id,
        stripe_customer_id=request.stripe_customer_id,
        period_start=period_start,
        period_end=period_end
    )
    
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        tier=subscription.tier.value,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end
    )


@router.get("/subscriptions/{user_id}", response_model=Optional[SubscriptionResponse])
async def get_user_subscription(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user subscription."""
    service = SubscriptionService(db)
    subscription = service.get_user_subscription(user_id)
    
    if not subscription:
        return None
    
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        tier=subscription.tier.value,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end
    )


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    """Cancel subscription."""
    service = SubscriptionService(db)
    subscription = service.cancel_subscription(subscription_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return {"message": "Subscription canceled", "subscription_id": subscription_id}


@router.post("/checkout/create-session")
async def create_checkout_session(
    tier: str = Query(..., description="Subscription tier (premium or pro)"),
    user_id: str = Query(..., description="User ID"),
    user_email: str = Query(..., description="User email"),
    success_url: str = Query(..., description="Success redirect URL"),
    cancel_url: str = Query(..., description="Cancel redirect URL")
):
    """Create Stripe checkout session for subscription."""
    import stripe
    import os
    
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    
    # Get price ID for tier
    price_id = StripeService.SUBSCRIPTION_PRICES.get(tier)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
    
    try:
        # Create or get customer
        customer = None
        existing_subscription = None
        subscription_service = SubscriptionService(None)  # Will be set by webhook
        
        # Try to get existing customer from subscription
        # For now, create new customer
        customer_data = StripeService.create_customer(
            email=user_email,
            name=user_email.split("@")[0]
        )
        customer_id = customer_data["customer_id"]
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                "user_id": user_id,
                "tier": tier
            },
            subscription_data={
                "metadata": {
                    "user_id": user_id,
                    "tier": tier
                }
            }
        )
        
        return {
            "session_id": session.id,
            "url": session.url,
            "customer_id": customer_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


# Lead endpoints
@router.post("/leads", response_model=LeadResponse)
async def create_lead(
    request: CreateLeadRequest,
    user_id: Optional[str] = Query(None, description="User ID (optional)"),
    db: Session = Depends(get_db)
):
    """Create booking lead."""
    service = LeadService(db)
    
    lead = service.create_lead(
        hotel_id=request.hotel_id,
        email=request.email,
        check_in=request.check_in,
        check_out=request.check_out,
        user_id=user_id,
        name=request.name,
        phone=request.phone,
        guests=request.guests,
        rooms=request.rooms,
        budget_range=request.budget_range,
        special_requests=request.special_requests
    )
    
    # Mark as sent and send email notifications
    await service.mark_lead_sent(lead.id)
    
    return LeadResponse(
        id=lead.id,
        hotel_id=lead.hotel_id,
        email=lead.email,
        name=lead.name,
        phone=lead.phone,
        check_in=lead.check_in,
        check_out=lead.check_out,
        guests=lead.guests,
        rooms=lead.rooms,
        status=lead.status.value,
        lead_fee=float(lead.lead_fee) if lead.lead_fee else None,
        created_at=lead.created_at
    )


@router.post("/leads/{lead_id}/convert")
async def convert_lead(
    lead_id: str,
    booking_value: float = Query(..., description="Booking value"),
    db: Session = Depends(get_db)
):
    """Mark lead as converted to booking."""
    service = LeadService(db)
    lead = service.mark_lead_converted(lead_id, Decimal(str(booking_value)))
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {"message": "Lead converted", "lead_id": lead_id, "commission": float(lead.commission)}


# Hotel listing endpoints
@router.post("/listings", response_model=ListingResponse)
async def create_listing(
    request: CreateListingRequest,
    db: Session = Depends(get_db)
):
    """Create hotel listing."""
    service = HotelListingService(db)
    
    listing = service.create_listing(
        hotel_id=request.hotel_id,
        package=ListingPackage(request.package.value),
        owner_email=request.owner_email,
        owner_name=request.owner_name,
        owner_phone=request.owner_phone
    )
    
    return ListingResponse(
        id=listing.id,
        hotel_id=listing.hotel_id,
        package=listing.package.value,
        owner_email=listing.owner_email,
        verified=listing.verified,
        status=listing.status,
        created_at=listing.created_at
    )


@router.post("/listings/verify/{verification_token}")
async def verify_listing(
    verification_token: str,
    db: Session = Depends(get_db)
):
    """Verify hotel listing ownership."""
    service = HotelListingService(db)
    listing = service.verify_listing(verification_token)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    return {"message": "Listing verified", "listing_id": listing.id}


# Sponsorship endpoints
@router.post("/sponsorships", response_model=SponsorshipResponse)
async def create_sponsorship(
    request: CreateSponsorshipRequest,
    db: Session = Depends(get_db)
):
    """Create sponsored placement."""
    service = SponsoredPlacementService(db)
    
    sponsorship = service.create_sponsorship(
        hotel_id=request.hotel_id,
        listing_id=request.listing_id,
        priority=request.priority,
        placement_type=request.placement_type,
        start_date=request.start_date,
        end_date=request.end_date,
        amount=request.amount
    )
    
    return SponsorshipResponse(
        id=sponsorship.id,
        hotel_id=sponsorship.hotel_id,
        priority=sponsorship.priority,
        placement_type=sponsorship.placement_type,
        start_date=sponsorship.start_date,
        end_date=sponsorship.end_date,
        status=sponsorship.status.value
    )


# Ad revenue endpoints
@router.post("/ads/impression")
@rate_limit("1000/hour")  # High limit for impressions (tracking)
async def record_ad_impression(
    http_request: Request,  # Required for rate_limit decorator
    request: AdImpressionRequest,
    db: Session = Depends(get_db)
):
    """Record ad impression."""
    service = AdRevenueService(db)
    service.record_impression(
        ad_slot=request.ad_slot,
        page_type=request.page_type,
        revenue=request.revenue
    )
    return {"message": "Impression recorded"}


@router.post("/ads/click")
@rate_limit("100/minute")  # Rate limit clicks to prevent fraud
async def record_ad_click(
    http_request: Request,  # Required for rate_limit decorator
    request: AdClickRequest,
    db: Session = Depends(get_db)
):
    """Record ad click."""
    service = AdRevenueService(db)
    service.record_click(
        ad_slot=request.ad_slot,
        page_type=request.page_type,
        revenue=request.revenue
    )
    return {"message": "Click recorded"}


# Analytics endpoints
@router.get("/analytics", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics(
    request: Request,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get revenue analytics (admin only)."""
    # Check admin role if request state available
    if hasattr(request.state, "user_role"):
        user_role = request.state.user_role
        if user_role not in ["super_admin", "tenant_admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
    
    service = RevenueAnalyticsService(db)
    analytics = service.get_total_revenue(start_date, end_date)
    
    return RevenueAnalyticsResponse(
        total_revenue=analytics["total_revenue"],
        by_type=analytics["by_type"],
        period=analytics["period"]
    )


@router.get("/analytics/monthly", response_model=List[MonthlyRevenueResponse])
async def get_monthly_revenue(
    months: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """Get monthly revenue breakdown."""
    service = RevenueAnalyticsService(db)
    monthly_data = service.get_monthly_revenue(months)
    
    return [
        MonthlyRevenueResponse(
            month=item["month"],
            revenue=item["revenue"],
            total=item["total"]
        )
        for item in monthly_data
    ]


# Owner endpoints
@router.get("/owners/listings", response_model=Optional[OwnerListingResponse])
async def get_owner_listing(
    owner_email: str = Query(..., description="Owner email"),
    db: Session = Depends(get_db)
):
    """Get listing by owner email."""
    service = HotelListingService(db)
    listing = service.get_listing_by_email(owner_email)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return OwnerListingResponse(
        id=listing.id,
        hotel_id=listing.hotel_id,
        package=listing.package.value,
        owner_email=listing.owner_email,
        owner_name=listing.owner_name,
        owner_phone=listing.owner_phone,
        verified=listing.verified,
        status=listing.status,
        current_period_start=listing.current_period_start,
        current_period_end=listing.current_period_end,
        created_at=listing.created_at,
        updated_at=listing.updated_at
    )


@router.get("/owners/leads", response_model=List[OwnerLeadResponse])
async def get_owner_leads(
    hotel_id: str = Query(..., description="Hotel ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get leads for a hotel."""
    service = LeadService(db)
    leads = service.get_leads_by_hotel_id(hotel_id, limit=limit)
    
    return [
        OwnerLeadResponse(
            id=lead.id,
            hotel_id=lead.hotel_id,
            email=lead.email,
            name=lead.name,
            phone=lead.phone,
            check_in=lead.check_in,
            check_out=lead.check_out,
            guests=lead.guests,
            rooms=lead.rooms,
            budget_range=lead.budget_range,
            special_requests=lead.special_requests,
            status=lead.status.value,
            created_at=lead.created_at,
            sent_to_hotel_at=lead.sent_to_hotel_at
        )
        for lead in leads
    ]

