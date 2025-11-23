"""Pydantic schemas for revenue API."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class SubscriptionTierEnum(str, Enum):
    """Subscription tier enum."""
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"


class ListingPackageEnum(str, Enum):
    """Listing package enum."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    PREMIUM = "premium"


class CreateSubscriptionRequest(BaseModel):
    """Request to create subscription."""
    tier: SubscriptionTierEnum
    stripe_subscription_id: str
    stripe_customer_id: str


class SubscriptionResponse(BaseModel):
    """Subscription response."""
    id: str
    user_id: str
    tier: str
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    
    class Config:
        from_attributes = True


class CreateLeadRequest(BaseModel):
    """Request to create lead."""
    hotel_id: str
    email: EmailStr
    check_in: date
    check_out: date
    name: Optional[str] = None
    phone: Optional[str] = None
    guests: Optional[int] = None
    rooms: Optional[int] = None
    budget_range: Optional[str] = None
    special_requests: Optional[str] = None


class LeadResponse(BaseModel):
    """Lead response."""
    id: str
    hotel_id: str
    email: str
    name: Optional[str]
    phone: Optional[str]
    check_in: date
    check_out: date
    guests: Optional[int]
    rooms: Optional[int]
    status: str
    lead_fee: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateListingRequest(BaseModel):
    """Request to create hotel listing."""
    hotel_id: str
    package: ListingPackageEnum
    owner_email: EmailStr
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None


class ListingResponse(BaseModel):
    """Listing response."""
    id: str
    hotel_id: str
    package: str
    owner_email: str
    verified: bool
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateSponsorshipRequest(BaseModel):
    """Request to create sponsorship."""
    hotel_id: str
    listing_id: Optional[str] = None
    priority: int = Field(ge=0, le=100)
    placement_type: str
    start_date: datetime
    end_date: datetime
    amount: Decimal


class SponsorshipResponse(BaseModel):
    """Sponsorship response."""
    id: str
    hotel_id: str
    priority: int
    placement_type: str
    start_date: datetime
    end_date: datetime
    status: str
    
    class Config:
        from_attributes = True


class AdImpressionRequest(BaseModel):
    """Request to record ad impression."""
    ad_slot: str
    page_type: str
    revenue: Decimal = Field(ge=0)


class AdClickRequest(BaseModel):
    """Request to record ad click."""
    ad_slot: str
    page_type: str
    revenue: Decimal = Field(ge=0)


class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics response."""
    total_revenue: float
    by_type: Dict[str, float]
    period: Dict[str, Optional[str]]


class MonthlyRevenueResponse(BaseModel):
    """Monthly revenue response."""
    month: str
    revenue: Dict[str, float]
    total: float


class OwnerListingResponse(BaseModel):
    """Owner listing response with full details."""
    id: str
    hotel_id: str
    package: str
    owner_email: str
    owner_name: Optional[str]
    owner_phone: Optional[str]
    verified: bool
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OwnerLeadResponse(BaseModel):
    """Owner lead response."""
    id: str
    hotel_id: str
    email: str
    name: Optional[str]
    phone: Optional[str]
    check_in: date
    check_out: date
    guests: Optional[int]
    rooms: Optional[int]
    budget_range: Optional[str]
    special_requests: Optional[str]
    status: str
    created_at: datetime
    sent_to_hotel_at: Optional[datetime]
    
    class Config:
        from_attributes = True

