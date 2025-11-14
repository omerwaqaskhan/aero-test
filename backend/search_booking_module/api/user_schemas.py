"""Pydantic schemas for user features."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class BookingStatusEnum(str, Enum):
    """Booking status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUNDED = "refunded"


class PriceAlertStatusEnum(str, Enum):
    """Price alert status enum."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Favorites Schemas
class FavoriteResponse(BaseModel):
    """Favorite response schema."""
    id: str
    user_id: str
    hotel_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateFavoriteRequest(BaseModel):
    """Create favorite request schema."""
    hotel_id: str = Field(..., description="Hotel ID to add to favorites")


# Booking Schemas
class CreateBookingRequest(BaseModel):
    """Create booking request schema."""
    hotel_id: str = Field(..., description="Hotel ID")
    offer_id: Optional[str] = Field(None, description="Offer ID if booking specific offer")
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    guests: int = Field(1, ge=1, le=10, description="Number of guests")
    rooms: int = Field(1, ge=1, le=5, description="Number of rooms")
    guest_name: str = Field(..., description="Guest name")
    guest_email: EmailStr = Field(..., description="Guest email")
    guest_phone: Optional[str] = Field(None, description="Guest phone")
    special_requests: Optional[str] = Field(None, description="Special requests")
    affiliate_link: Optional[str] = Field(None, description="Affiliate link for booking")


class BookingResponse(BaseModel):
    """Booking response schema."""
    id: str
    user_id: Optional[str]
    hotel_id: str
    offer_id: Optional[str]
    booking_reference: Optional[str]
    check_in: date
    check_out: date
    guests: int
    rooms: int
    guest_name: str
    guest_email: str
    guest_phone: Optional[str]
    total_price: Decimal
    currency: str
    taxes_included: bool
    status: BookingStatusEnum
    provider: Optional[str]
    provider_booking_id: Optional[str]
    booked_at: datetime
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    special_requests: Optional[str]
    cancellation_policy: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UpdateBookingStatusRequest(BaseModel):
    """Update booking status request schema."""
    status: BookingStatusEnum = Field(..., description="New booking status")


# Price Alert Schemas
class CreatePriceAlertRequest(BaseModel):
    """Create price alert request schema."""
    hotel_id: str = Field(..., description="Hotel ID")
    target_price: Decimal = Field(..., description="Target price to alert on")
    currency: str = Field("USD", description="Currency")
    check_in: Optional[date] = Field(None, description="Check-in date")
    check_out: Optional[date] = Field(None, description="Check-out date")
    guests: Optional[int] = Field(1, ge=1, le=10, description="Number of guests")
    rooms: Optional[int] = Field(1, ge=1, le=5, description="Number of rooms")
    notify_email: bool = Field(True, description="Send email notifications")
    notify_sms: bool = Field(False, description="Send SMS notifications")
    expires_at: Optional[datetime] = Field(None, description="Alert expiration date")


class PriceAlertResponse(BaseModel):
    """Price alert response schema."""
    id: str
    user_id: str
    hotel_id: str
    target_price: Decimal
    currency: str
    check_in: Optional[date]
    check_out: Optional[date]
    guests: Optional[int]
    rooms: Optional[int]
    status: PriceAlertStatusEnum
    triggered_at: Optional[datetime]
    triggered_price: Optional[Decimal]
    notify_email: bool
    notify_sms: bool
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Saved Search Schemas
class CreateSavedSearchRequest(BaseModel):
    """Create saved search request schema."""
    destination: str = Field(..., description="Destination")
    check_in: Optional[date] = Field(None, description="Check-in date")
    check_out: Optional[date] = Field(None, description="Check-out date")
    guests: Optional[int] = Field(1, ge=1, le=10, description="Number of guests")
    rooms: Optional[int] = Field(1, ge=1, le=5, description="Number of rooms")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    name: Optional[str] = Field(None, description="Name for the saved search")
    notification_enabled: bool = Field(False, description="Enable notifications")


class SavedSearchResponse(BaseModel):
    """Saved search response schema."""
    id: str
    user_id: str
    destination: str
    check_in: Optional[date]
    check_out: Optional[date]
    guests: Optional[int]
    rooms: Optional[int]
    filters: Dict[str, Any]
    name: Optional[str]
    notification_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_searched_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# User Review Schemas
class CreateUserReviewRequest(BaseModel):
    """Create user review request schema."""
    hotel_id: str = Field(..., description="Hotel ID")
    booking_id: Optional[str] = Field(None, description="Booking ID if review is from a booking")
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating (1-5)")
    title: Optional[str] = Field(None, description="Review title")
    text: Optional[str] = Field(None, description="Review text")
    category_ratings: Dict[str, float] = Field(default_factory=dict, description="Category ratings")
    pros: List[str] = Field(default_factory=list, description="Pros")
    cons: List[str] = Field(default_factory=list, description="Cons")


class UserReviewResponse(BaseModel):
    """User review response schema."""
    id: str
    user_id: Optional[str]
    hotel_id: str
    booking_id: Optional[str]
    rating: float
    title: Optional[str]
    text: Optional[str]
    category_ratings: Dict[str, float]
    pros: List[str]
    cons: List[str]
    verified_booking: bool
    published: bool
    helpful_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MarkReviewHelpfulRequest(BaseModel):
    """Mark review helpful request schema."""
    helpful: bool = Field(True, description="Mark as helpful or not")

