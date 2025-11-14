"""User-related database models for search and booking module."""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, Date, DateTime, ForeignKey, JSON, Enum as SQLEnum, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid
import enum

from auth_module.infrastructure.db.database import Base


class BookingStatus(str, enum.Enum):
    """Booking status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUNDED = "refunded"


class PriceAlertStatus(str, enum.Enum):
    """Price alert status enum."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class FavoriteModel(Base):
    """User favorites/wishlist database model."""
    __tablename__ = "favorites"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    # Note: User relationship would be in auth_module, hotel relationship in models.py
    
    # Constraints
    __table_args__ = (
        Index("ix_favorites_user_hotel", "user_id", "hotel_id", unique=True),
    )
    
    def __repr__(self):
        return f"<FavoriteModel(id={self.id}, user_id={self.user_id}, hotel_id={self.hotel_id})>"


class BookingModel(Base):
    """Booking database model."""
    __tablename__ = "bookings"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    offer_id = Column(UUID(as_uuid=False), ForeignKey("offers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Booking details
    booking_reference = Column(String(100), nullable=True, unique=True, index=True)  # External booking reference
    check_in = Column(Date, nullable=False, index=True)
    check_out = Column(Date, nullable=False, index=True)
    guests = Column(Integer, nullable=False, default=1)
    rooms = Column(Integer, nullable=False, default=1)
    
    # Guest information
    guest_name = Column(String(255), nullable=False)
    guest_email = Column(String(255), nullable=False, index=True)
    guest_phone = Column(String(50), nullable=True)
    
    # Pricing
    total_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    taxes_included = Column(Boolean, nullable=False, default=False)
    
    # Status and tracking
    status = Column(SQLEnum(BookingStatus), nullable=False, default=BookingStatus.PENDING, index=True)
    provider = Column(String(50), nullable=True)  # booking.com, expedia, etc.
    provider_booking_id = Column(String(255), nullable=True, index=True)
    affiliate_link = Column(Text, nullable=True)
    
    # Timestamps
    booked_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional data
    special_requests = Column(Text, nullable=True)
    cancellation_policy = Column(JSON, nullable=False, default=dict)
    booking_metadata = Column(JSON, nullable=False, default=dict)
    
    def __repr__(self):
        return f"<BookingModel(id={self.id}, booking_reference={self.booking_reference}, status={self.status})>"


class PriceAlertModel(Base):
    """Price alert database model."""
    __tablename__ = "price_alerts"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert criteria
    target_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    check_in = Column(Date, nullable=True, index=True)
    check_out = Column(Date, nullable=True, index=True)
    guests = Column(Integer, nullable=True, default=1)
    rooms = Column(Integer, nullable=True, default=1)
    
    # Status
    status = Column(SQLEnum(PriceAlertStatus), nullable=False, default=PriceAlertStatus.ACTIVE, index=True)
    triggered_at = Column(DateTime, nullable=True)
    triggered_price = Column(Numeric(10, 2), nullable=True)
    
    # Notification settings
    notify_email = Column(Boolean, nullable=False, default=True)
    notify_sms = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    def __repr__(self):
        return f"<PriceAlertModel(id={self.id}, hotel_id={self.hotel_id}, target_price={self.target_price})>"


class SavedSearchModel(Base):
    """Saved search database model."""
    __tablename__ = "saved_searches"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Search parameters
    destination = Column(String(255), nullable=False)
    check_in = Column(Date, nullable=True)
    check_out = Column(Date, nullable=True)
    guests = Column(Integer, nullable=True, default=1)
    rooms = Column(Integer, nullable=True, default=1)
    filters = Column(JSON, nullable=False, default=dict)  # min_price, max_price, stars, amenities, etc.
    
    # Metadata
    name = Column(String(255), nullable=True)  # User-given name for the search
    notification_enabled = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_searched_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<SavedSearchModel(id={self.id}, user_id={self.user_id}, destination={self.destination})>"


class UserReviewModel(Base):
    """User-submitted review database model."""
    __tablename__ = "user_reviews"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=False), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Review content
    rating = Column(Float, nullable=False)  # 1-5 stars
    title = Column(String(500), nullable=True)
    text = Column(Text, nullable=True)
    
    # Category ratings
    category_ratings = Column(JSON, nullable=False, default=dict)  # {cleanliness: float, service: float, value: float, location: float}
    
    # Pros and cons
    pros = Column(JSON, nullable=False, default=list)
    cons = Column(JSON, nullable=False, default=list)
    
    # Status
    verified_booking = Column(Boolean, nullable=False, default=False)  # True if review is from a verified booking
    published = Column(Boolean, nullable=False, default=True)
    helpful_count = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        Index("ix_user_reviews_user_hotel", "user_id", "hotel_id"),
    )
    
    def __repr__(self):
        return f"<UserReviewModel(id={self.id}, hotel_id={self.hotel_id}, rating={self.rating})>"

