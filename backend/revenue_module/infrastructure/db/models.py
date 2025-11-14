"""Database models for revenue tracking."""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, Date, DateTime, ForeignKey, JSON, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from auth_module.infrastructure.db.database import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tier enum."""
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"


class LeadStatus(str, enum.Enum):
    """Lead status enum."""
    NEW = "new"
    SENT = "sent"
    RESPONDED = "responded"
    BOOKED = "booked"
    LOST = "lost"


class ListingPackage(str, enum.Enum):
    """Hotel listing package enum."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    PREMIUM = "premium"


class SponsorshipStatus(str, enum.Enum):
    """Sponsorship status enum."""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"


class SubscriptionModel(Base):
    """User subscription model."""
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tier = Column(SQLEnum(SubscriptionTier), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)  # active, canceled, past_due
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = relationship("SubscriptionPaymentModel", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SubscriptionModel(id={self.id}, user_id={self.user_id}, tier={self.tier})>"


class SubscriptionPaymentModel(Base):
    """Subscription payment tracking."""
    __tablename__ = "subscription_payments"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(UUID(as_uuid=False), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(20), nullable=False, index=True)  # succeeded, pending, failed
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    subscription = relationship("SubscriptionModel", back_populates="payments")
    
    def __repr__(self):
        return f"<SubscriptionPaymentModel(id={self.id}, subscription_id={self.subscription_id}, amount={self.amount})>"


class LeadModel(Base):
    """Lead generation model."""
    __tablename__ = "leads"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Contact info
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)
    
    # Booking details
    check_in = Column(Date, nullable=False, index=True)
    check_out = Column(Date, nullable=False, index=True)
    guests = Column(Integer, nullable=True)
    rooms = Column(Integer, nullable=True)
    budget_range = Column(String(50), nullable=True)
    special_requests = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True)
    sent_to_hotel_at = Column(DateTime, nullable=True)
    hotel_responded_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)
    
    # Revenue
    lead_fee = Column(Numeric(10, 2), nullable=True)
    booking_value = Column(Numeric(10, 2), nullable=True)
    commission = Column(Numeric(10, 2), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<LeadModel(id={self.id}, hotel_id={self.hotel_id}, status={self.status})>"


class HotelListingModel(Base):
    """Hotel listing package model."""
    __tablename__ = "hotel_listings"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    package = Column(SQLEnum(ListingPackage), nullable=False, index=True)
    owner_email = Column(String(255), nullable=False, index=True)
    owner_name = Column(String(255), nullable=True)
    owner_phone = Column(String(50), nullable=True)
    verified = Column(Boolean, nullable=False, default=False, index=True)
    verification_token = Column(String(255), nullable=True, unique=True, index=True)
    
    # Payment
    stripe_customer_id = Column(String(255), nullable=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, active, suspended, canceled
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = relationship("ListingPaymentModel", back_populates="listing", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HotelListingModel(id={self.id}, hotel_id={self.hotel_id}, package={self.package})>"


class ListingPaymentModel(Base):
    """Hotel listing payment tracking."""
    __tablename__ = "listing_payments"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    listing_id = Column(UUID(as_uuid=False), ForeignKey("hotel_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(20), nullable=False, index=True)  # succeeded, pending, failed
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    listing = relationship("HotelListingModel", back_populates="payments")
    
    def __repr__(self):
        return f"<ListingPaymentModel(id={self.id}, listing_id={self.listing_id}, amount={self.amount})>"


class SponsoredPlacementModel(Base):
    """Sponsored hotel placement model."""
    __tablename__ = "sponsored_placements"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    listing_id = Column(UUID(as_uuid=False), ForeignKey("hotel_listings.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Placement details
    priority = Column(Integer, nullable=False, default=0, index=True)  # Higher = more priority
    placement_type = Column(String(50), nullable=False, index=True)  # search_results, featured, homepage
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    status = Column(SQLEnum(SponsorshipStatus), nullable=False, default=SponsorshipStatus.ACTIVE, index=True)
    
    # Payment
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    stripe_payment_intent_id = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SponsoredPlacementModel(id={self.id}, hotel_id={self.hotel_id}, priority={self.priority})>"


class AdRevenueModel(Base):
    """Ad revenue tracking model."""
    __tablename__ = "ad_revenue"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_slot = Column(String(100), nullable=False, index=True)  # search_results, hotel_details, sidebar
    page_type = Column(String(50), nullable=False, index=True)  # search, hotel_details, landing
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    revenue = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AdRevenueModel(id={self.id}, date={self.date}, revenue={self.revenue})>"


class RevenueTransactionModel(Base):
    """Unified revenue transaction tracking."""
    __tablename__ = "revenue_transactions"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    revenue_type = Column(String(50), nullable=False, index=True)  # subscription, lead, listing, sponsorship, ads
    reference_id = Column(UUID(as_uuid=False), nullable=True, index=True)  # ID of related record
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(String(20), nullable=False, index=True)  # completed, pending, failed, refunded
    transaction_metadata = Column(JSON, nullable=False, default=dict)  # Renamed from 'metadata' (SQLAlchemy reserved)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RevenueTransactionModel(id={self.id}, type={self.revenue_type}, amount={self.amount})>"

