"""Expedia provider adapter (mock implementation)."""

from typing import List, Optional
from datetime import date, datetime, timedelta
import uuid

from search_booking_module.domain.models import Hotel, Offer, Review, Provider
from search_booking_module.infrastructure.providers.base import (
    BaseProvider,
    ProviderError
)


class ExpediaProvider(BaseProvider):
    """Expedia provider adapter."""
    
    @property
    def provider(self) -> Provider:
        """Get provider enum value."""
        return Provider.EXPEDIA
    
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
        if not self.validate_credentials():
            raise ProviderError("Invalid API credentials")
        
        # Simulate API delay
        import asyncio
        await asyncio.sleep(0.1)
        
        # Return mock hotels
        hotels = []
        for i in range(5):
            hotel = Hotel(
                id=str(uuid.uuid4()),
                provider_hotel_id=f"expedia_{i+1}",
                provider=Provider.EXPEDIA,
                name=f"Expedia Hotel {i+1} - {destination}",
                address={
                    "street": f"{i+1} Broadway",
                    "city": destination,
                    "postal_code": "54321"
                },
                city=destination,
                country="USA",
                latitude=40.7580 + (i * 0.01),
                longitude=-73.9855 + (i * 0.01),
                stars=2 + (i % 4),
                description=f"Comfortable hotel in {destination}",
                images=[
                    f"https://example.com/expedia_hotel{i+1}_1.jpg",
                    f"https://example.com/expedia_hotel{i+1}_2.jpg"
                ],
                amenities=["WiFi", "Parking", "Breakfast"] if i % 2 == 0 else ["WiFi"]
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
        
        hotel = Hotel(
            id=str(uuid.uuid4()),
            provider_hotel_id=provider_hotel_id,
            provider=Provider.EXPEDIA,
            name=f"Expedia Hotel {provider_hotel_id}",
            address={
                "street": "456 Broadway",
                "city": "New York",
                "postal_code": "10013"
            },
            city="New York",
            country="USA",
            latitude=40.7580,
            longitude=-73.9855,
            stars=3,
            description="A comfortable hotel with great amenities",
            images=[
                "https://example.com/expedia_hotel1.jpg",
                "https://example.com/expedia_hotel2.jpg"
            ],
            amenities=["WiFi", "Parking", "Breakfast", "Gym"]
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
        
        nights = (check_out - check_in).days
        
        offers = []
        for i in range(3):
            base_price = 90.0 + (i * 15)
            offer = Offer(
                id=str(uuid.uuid4()),
                hotel_id=str(uuid.uuid4()),
                provider=Provider.EXPEDIA,
                provider_rate_id=f"expedia_rate_{provider_hotel_id}_{i}",
                currency="USD",
                price=base_price,
                taxes_included=True,  # Expedia includes taxes
                check_in=check_in,
                check_out=check_out,
                availability_count=3 - i,
                cancellation_policy={
                    "type": "flexible" if i == 0 else "moderate",
                    "deadline": (check_in - timedelta(days=2)).isoformat() if i == 0 else None
                },
                raw_response={},
                fetched_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=2)
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
        
        reviews = []
        ratings = [4.2, 4.7, 3.8, 5.0, 4.3]
        for i in range(min(limit, 5)):
            review = Review(
                id=str(uuid.uuid4()),
                hotel_id=str(uuid.uuid4()),
                provider=Provider.EXPEDIA,
                rating=ratings[i],
                text=f"Nice stay! Review {i+1}",
                author=f"Traveler{i+1}",
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
        base_url = "https://www.expedia.com/hotel"
        params = {
            "hotel_id": provider_hotel_id,
            "checkIn": check_in.isoformat(),
            "checkOut": check_out.isoformat(),
            "adults": guests,
            "rooms": rooms,
            "affiliate_id": self.api_key or "default"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    def get_rate_limit_info(self) -> dict:
        """Get Expedia rate limit information."""
        return {
            "requests_per_minute": 40,
            "requests_per_hour": 600,
            "requests_per_day": 6000
        }

