"""Domain models for search and booking module."""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from dataclasses import dataclass, field


class Provider(str, Enum):
    """Hotel booking providers."""
    BOOKING_COM = "booking_com"
    EXPEDIA = "expedia"
    DIRECT = "direct"
    AGODA = "agoda"


class BookingStatus(str, Enum):
    """Booking status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class Hotel:
    """Hotel domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_hotel_id: str = ""
    provider: Provider = Provider.BOOKING_COM
    name: str = ""
    address: Dict[str, Any] = field(default_factory=dict)
    city: str = ""
    country: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    stars: int = 0
    rating: Optional[float] = None  # Average rating
    description: str = ""
    property_overview: str = ""  # Detailed property overview
    images: List[str] = field(default_factory=list)
    amenities: List[str] = field(default_factory=list)
    policies: Dict[str, Any] = field(default_factory=dict)  # Check-in, check-out, cancellation, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_full_address(self) -> str:
        """Get full address string."""
        parts = []
        if self.address.get("street"):
            parts.append(self.address["street"])
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts) if parts else ""


@dataclass
class Room:
    """Room domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hotel_id: str = ""
    room_type_name: str = ""
    description: str = ""  # Room description
    images: List[str] = field(default_factory=list)  # Room images
    occupancy: Dict[str, Any] = field(default_factory=dict)  # {size: int, max_guests: int, bed_type: str}
    amenities: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_max_guests(self) -> int:
        """Get maximum number of guests."""
        return self.occupancy.get("max_guests", 0)


@dataclass
class Offer:
    """Hotel offer/rate domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hotel_id: str = ""
    room_id: Optional[str] = None
    provider: Provider = Provider.BOOKING_COM
    provider_rate_id: str = ""
    currency: str = "USD"
    price: float = 0.0
    taxes_included: bool = False
    check_in: date = field(default_factory=date.today)
    check_out: date = field(default_factory=date.today)
    availability_count: int = 0
    cancellation_policy: Dict[str, Any] = field(default_factory=dict)
    raw_response: Dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def get_total_nights(self) -> int:
        """Get total number of nights."""
        return (self.check_out - self.check_in).days
    
    def get_total_price(self) -> float:
        """Get total price for the stay."""
        return self.price * self.get_total_nights()
    
    def is_expired(self) -> bool:
        """Check if offer has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class BookingClick:
    """Booking click tracking domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    offer_id: str = ""
    provider: Provider = Provider.BOOKING_COM
    affiliate_link: str = ""
    clicked_at: datetime = field(default_factory=datetime.utcnow)
    ip_address: str = ""
    user_agent: str = ""
    converted: bool = False
    converted_at: Optional[datetime] = None
    
    def mark_converted(self) -> None:
        """Mark click as converted."""
        self.converted = True
        self.converted_at = datetime.utcnow()


@dataclass
class Review:
    """Hotel review domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hotel_id: str = ""
    provider: Provider = Provider.BOOKING_COM
    rating: float = 0.0
    title: str = ""  # Review title
    text: str = ""
    author: str = ""
    pros: List[str] = field(default_factory=list)  # List of positive points
    cons: List[str] = field(default_factory=list)  # List of negative points
    category_ratings: Dict[str, float] = field(default_factory=dict)  # {cleanliness: float, amenities: float, etc.}
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_positive(self) -> bool:
        """Check if review is positive (rating >= 4.0)."""
        return self.rating >= 4.0


@dataclass
class SearchFilters:
    """Search filters domain model."""
    destination: str = ""
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    guests: int = 1
    rooms: int = 1
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    stars: Optional[List[int]] = None
    amenities: Optional[List[str]] = None
    rating_min: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[float] = None  # in kilometers
    
    def is_valid(self) -> bool:
        """Check if filters are valid."""
        if not self.destination and not (self.latitude and self.longitude):
            return False
        if self.check_in and self.check_out:
            if self.check_out <= self.check_in:
                return False
        if self.min_price and self.max_price:
            if self.min_price > self.max_price:
                return False
        return True


@dataclass
class SearchResult:
    """Search result domain model."""
    hotel: Hotel
    offers: List[Offer] = field(default_factory=list)
    best_price: Optional[float] = None
    best_offer: Optional[Offer] = None
    average_rating: Optional[float] = None
    review_count: int = 0
    
    def get_lowest_price(self) -> Optional[float]:
        """Get lowest price from all offers."""
        if not self.offers:
            return None
        return min(offer.price for offer in self.offers if offer.price > 0)

