"""Pydantic schemas for search and booking API."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class ProviderEnum(str, Enum):
    """Provider enum for API."""
    BOOKING_COM = "booking_com"
    EXPEDIA = "expedia"
    DIRECT = "direct"
    AGODA = "agoda"


class SortByEnum(str, Enum):
    """Sort options for search."""
    PRICE = "price"
    RATING = "rating"
    STARS = "stars"
    DISTANCE = "distance"


class SortOrderEnum(str, Enum):
    """Sort order."""
    ASC = "asc"
    DESC = "desc"


# Request Schemas
class SearchRequest(BaseModel):
    """Search request schema."""
    destination: str = Field(..., description="Destination city or location")
    check_in: date = Field(..., description="Check-in date")
    check_out: date = Field(..., description="Check-out date")
    guests: int = Field(1, ge=1, le=10, description="Number of guests")
    rooms: int = Field(1, ge=1, le=5, description="Number of rooms")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price per night")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price per night")
    stars: Optional[List[int]] = Field(None, description="Filter by star rating")
    amenities: Optional[List[str]] = Field(None, description="Filter by amenities")
    rating_min: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for location search")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for location search")
    radius: Optional[float] = Field(None, ge=0, description="Search radius in kilometers")
    sort_by: SortByEnum = Field(SortByEnum.PRICE, description="Sort field")
    sort_order: SortOrderEnum = Field(SortOrderEnum.ASC, description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Results per page")
    
    @validator('check_out')
    def check_out_after_check_in(cls, v, values):
        """Validate check-out is after check-in."""
        if 'check_in' in values and v <= values['check_in']:
            raise ValueError('check_out must be after check_in')
        return v
    
    @validator('max_price')
    def max_price_greater_than_min(cls, v, values):
        """Validate max_price is greater than min_price."""
        if v and 'min_price' in values and values['min_price']:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v


class HotelDetailsRequest(BaseModel):
    """Hotel details request schema."""
    hotel_id: str = Field(..., description="Hotel ID")
    check_in: Optional[date] = Field(None, description="Check-in date")
    check_out: Optional[date] = Field(None, description="Check-out date")


class BookingClickRequest(BaseModel):
    """Booking click request schema."""
    offer_id: str = Field(..., description="Offer ID")
    provider: ProviderEnum = Field(..., description="Provider")
    affiliate_link: str = Field(..., description="Affiliate link")


# Response Schemas
class AddressResponse(BaseModel):
    """Address response schema."""
    street: Optional[str] = None
    city: str
    country: str
    postal_code: Optional[str] = None


class HotelResponse(BaseModel):
    """Hotel response schema."""
    id: str
    provider_hotel_id: str
    provider: ProviderEnum
    name: str
    address: Dict[str, Any]
    city: str
    country: str
    latitude: float
    longitude: float
    stars: int
    rating: Optional[float] = None
    description: Optional[str] = None
    property_overview: Optional[str] = None
    images: List[str] = []
    amenities: List[str] = []
    policies: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoomResponse(BaseModel):
    """Room response schema."""
    id: str
    hotel_id: str
    room_type_name: str
    description: Optional[str] = None
    images: List[str] = []
    occupancy: Dict[str, Any] = {}
    amenities: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OfferResponse(BaseModel):
    """Offer response schema."""
    id: str
    hotel_id: str
    room_id: Optional[str] = None
    provider: ProviderEnum
    provider_rate_id: str
    currency: str
    price: float
    taxes_included: bool
    check_in: date
    check_out: date
    availability_count: int
    cancellation_policy: Dict[str, Any] = {}
    total_nights: int
    total_price: float
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Review response schema."""
    id: str
    hotel_id: str
    provider: ProviderEnum
    rating: float
    title: Optional[str] = None
    text: Optional[str] = None
    author: Optional[str] = None
    pros: List[str] = []
    cons: List[str] = []
    category_ratings: Dict[str, float] = {}
    fetched_at: datetime
    
    class Config:
        from_attributes = True


class SearchResultResponse(BaseModel):
    """Search result response schema."""
    hotel: HotelResponse
    offers: List[OfferResponse] = []
    best_price: Optional[float] = None
    average_rating: Optional[float] = None
    review_count: int = 0
    is_sponsored: bool = False
    sponsor_priority: int = 0


class SearchResponse(BaseModel):
    """Search response schema."""
    results: List[SearchResultResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class BookingClickResponse(BaseModel):
    """Booking click response schema."""
    id: str
    offer_id: str
    provider: ProviderEnum
    affiliate_link: str
    clicked_at: datetime
    
    class Config:
        from_attributes = True


class HotelDetailsResponse(BaseModel):
    """Hotel details response schema."""
    hotel: HotelResponse
    rooms: List[RoomResponse] = []
    offers: List[OfferResponse] = []
    reviews: List[ReviewResponse] = []


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

