"""SQLAlchemy models for search and booking module."""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, Date, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid

from auth_module.infrastructure.db.database import Base
from search_booking_module.domain.models import Provider


class HotelModel(Base):
    """Hotel database model."""
    __tablename__ = "hotels"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_hotel_id = Column(String(255), nullable=False, index=True)
    provider = Column(SQLEnum(Provider), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    address = Column(JSON, nullable=False, default=dict)
    city = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    stars = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=True)  # Average rating
    description = Column(Text, nullable=True)
    property_overview = Column(Text, nullable=True)  # Detailed property overview
    images = Column(JSON, nullable=False, default=list)
    amenities = Column(JSON, nullable=False, default=list)
    policies = Column(JSON, nullable=False, default=dict)  # Check-in, check-out, cancellation, etc.
    source_url = Column(Text, nullable=True)  # URL where hotel was scraped from
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rooms = relationship("RoomModel", back_populates="hotel", cascade="all, delete-orphan")
    offers = relationship("OfferModel", back_populates="hotel", cascade="all, delete-orphan")
    reviews = relationship("ReviewModel", back_populates="hotel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HotelModel(id={self.id}, name={self.name}, provider={self.provider})>"


class RoomModel(Base):
    """Room database model."""
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    room_type_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)  # Room description
    images = Column(JSON, nullable=False, default=list)  # Room images
    occupancy = Column(JSON, nullable=False, default=dict)  # {size: int, max_guests: int, bed_type: str}
    amenities = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hotel = relationship("HotelModel", back_populates="rooms")
    offers = relationship("OfferModel", back_populates="room")
    
    def __repr__(self):
        return f"<RoomModel(id={self.id}, hotel_id={self.hotel_id}, type={self.room_type_name})>"


class OfferModel(Base):
    """Offer/Rate database model."""
    __tablename__ = "offers"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=False), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True)
    provider = Column(SQLEnum(Provider), nullable=False, index=True)
    provider_rate_id = Column(String(255), nullable=False, index=True)
    currency = Column(String(10), nullable=False, default="USD")
    price = Column(Float, nullable=False)
    taxes_included = Column(Boolean, nullable=False, default=False)
    check_in = Column(Date, nullable=False, index=True)
    check_out = Column(Date, nullable=False, index=True)
    availability_count = Column(Integer, nullable=False, default=0)
    cancellation_policy = Column(JSON, nullable=False, default=dict)
    raw_response = Column(JSON, nullable=False, default=dict)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Relationships
    hotel = relationship("HotelModel", back_populates="offers")
    room = relationship("RoomModel", back_populates="offers")
    booking_clicks = relationship("BookingClickModel", back_populates="offer")
    
    def __repr__(self):
        return f"<OfferModel(id={self.id}, hotel_id={self.hotel_id}, price={self.price}, provider={self.provider})>"


class BookingClickModel(Base):
    """Booking click tracking database model."""
    __tablename__ = "bookings_clicks"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(as_uuid=False), nullable=True, index=True)  # No FK constraint - references users table in auth_module
    offer_id = Column(UUID(as_uuid=False), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(SQLEnum(Provider), nullable=False, index=True)
    affiliate_link = Column(Text, nullable=False)
    clicked_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    converted = Column(Boolean, nullable=False, default=False, index=True)
    converted_at = Column(DateTime, nullable=True)
    
    # Relationships
    offer = relationship("OfferModel", back_populates="booking_clicks")
    
    def __repr__(self):
        return f"<BookingClickModel(id={self.id}, offer_id={self.offer_id}, converted={self.converted})>"


class ReviewModel(Base):
    """Hotel review database model."""
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    hotel_id = Column(UUID(as_uuid=False), ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(SQLEnum(Provider), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    title = Column(String(500), nullable=True)  # Review title
    text = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    pros = Column(JSON, nullable=False, default=list)  # List of positive points
    cons = Column(JSON, nullable=False, default=list)  # List of negative points
    category_ratings = Column(JSON, nullable=False, default=dict)  # {cleanliness: float, amenities: float, etc.}
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    hotel = relationship("HotelModel", back_populates="reviews")
    
    def __repr__(self):
        return f"<ReviewModel(id={self.id}, hotel_id={self.hotel_id}, rating={self.rating})>"

