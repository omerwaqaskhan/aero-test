"""Booking.com provider adapter (mock implementation)."""

from typing import List, Optional
from datetime import date, datetime, timedelta
import uuid

from search_booking_module.domain.models import Hotel, Offer, Review, Provider
from search_booking_module.infrastructure.providers.base import (
    BaseProvider,
    ProviderError,
    ProviderTimeoutError
)


class BookingComProvider(BaseProvider):
    """Booking.com provider adapter."""
    
    @property
    def provider(self) -> Provider:
        """Get provider enum value."""
        return Provider.BOOKING_COM
    
    async def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        rooms: int = 1,
        **kwargs
    ) -> List[Hotel]:
        """Search for hotels (mock implementation)."""
        # Mock implementation - returns sample hotels
        # In production, this would call Booking.com API
        
        if not self.validate_credentials():
            raise ProviderError("Invalid API credentials")
        
        # Simulate API delay
        import asyncio
        await asyncio.sleep(0.1)
        
        # Return mock hotels
        hotels = []
        for i in range(5):  # Return 5 mock hotels
            hotel = Hotel(
                id=str(uuid.uuid4()),
                provider_hotel_id=f"booking_{i+1}",
                provider=Provider.BOOKING_COM,
                name=f"Sample Hotel {i+1} - {destination}",
                address={
                    "street": f"{i+1} Main Street",
                    "city": destination,
                    "postal_code": "12345"
                },
                city=destination,
                country="USA",
                latitude=40.7128 + (i * 0.01),
                longitude=-74.0060 + (i * 0.01),
                stars=3 + (i % 3),
                description=f"Beautiful hotel in {destination}",
                images=[
                    f"https://example.com/hotel{i+1}_1.jpg",
                    f"https://example.com/hotel{i+1}_2.jpg"
                ],
                amenities=["WiFi", "Parking", "Breakfast", "Pool"] if i % 2 == 0 else ["WiFi", "Parking"]
            )
            hotels.append(hotel)
        
        return hotels
    
    async def get_hotel_details(
        self,
        provider_hotel_id: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        **kwargs
    ) -> Optional[Hotel]:
        """Get hotel details (mock implementation)."""
        if not self.validate_credentials():
            raise ProviderError("Invalid API credentials")
        
        # Mock implementation
        hotel = Hotel(
            id=str(uuid.uuid4()),
            provider_hotel_id=provider_hotel_id,
            provider=Provider.BOOKING_COM,
            name=f"Hotel {provider_hotel_id}",
            address={
                "street": "123 Main Street",
                "city": "New York",
                "postal_code": "10001"
            },
            city="New York",
            country="USA",
            latitude=40.7128,
            longitude=-74.0060,
            stars=4,
            description="A beautiful hotel in the heart of the city",
            images=[
                "https://example.com/hotel1.jpg",
                "https://example.com/hotel2.jpg"
            ],
            amenities=["WiFi", "Parking", "Breakfast", "Pool", "Gym"]
        )
        
        return hotel
    
    async def get_offers(
        self,
        provider_hotel_id: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        rooms: int = 1,
        **kwargs
    ) -> List[Offer]:
        """Get offers for a hotel (mock implementation)."""
        if not self.validate_credentials():
            raise ProviderError("Invalid API credentials")
        
        # Calculate nights
        nights = (check_out - check_in).days
        
        # Mock offers
        offers = []
        for i in range(3):  # Return 3 mock offers
            base_price = 100.0 + (i * 20)
            offer = Offer(
                id=str(uuid.uuid4()),
                hotel_id=str(uuid.uuid4()),  # Would be actual hotel ID
                provider=Provider.BOOKING_COM,
                provider_rate_id=f"rate_{provider_hotel_id}_{i}",
                currency="USD",
                price=base_price,
                taxes_included=False,
                check_in=check_in,
                check_out=check_out,
                availability_count=5 - i,
                cancellation_policy={
                    "type": "free_cancellation" if i == 0 else "non_refundable",
                    "deadline": (check_in - timedelta(days=1)).isoformat() if i == 0 else None
                },
                raw_response={},
                fetched_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            offers.append(offer)
        
        return offers
    
    async def get_reviews(
        self,
        provider_hotel_id: str,
        limit: int = 10,
        **kwargs
    ) -> List[Review]:
        """Get reviews for a hotel (mock implementation)."""
        if not self.validate_credentials():
            raise ProviderError("Invalid API credentials")
        
        # Mock reviews
        reviews = []
        ratings = [4.5, 4.0, 5.0, 3.5, 4.8]
        for i in range(min(limit, 5)):
            review = Review(
                id=str(uuid.uuid4()),
                hotel_id=str(uuid.uuid4()),  # Would be actual hotel ID
                provider=Provider.BOOKING_COM,
                rating=ratings[i],
                text=f"Great hotel! Review {i+1}",
                author=f"Guest{i+1}",
                fetched_at=datetime.utcnow()
            )
            reviews.append(review)
        
        return reviews
    
    def generate_affiliate_link(
        self,
        provider_hotel_id: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        rooms: int = 1,
        **kwargs
    ) -> str:
        """Generate affiliate booking link."""
        # Mock affiliate link generation
        # In production, this would use Booking.com affiliate API
        base_url = "https://www.booking.com/hotel"
        params = {
            "hotel_id": provider_hotel_id,
            "checkin": check_in.isoformat(),
            "checkout": check_out.isoformat(),
            "group_adults": guests,
            "no_rooms": rooms,
            "affiliate_id": self.api_key or "default"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def get_rate_limit_info(self) -> dict:
        """Get Booking.com rate limit information."""
        return {
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "requests_per_day": 5000
        }

