"""Base provider interface for hotel booking providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from search_booking_module.domain.models import Hotel, Offer, Review, Provider


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class ProviderTimeoutError(ProviderError):
    """Provider request timeout."""
    pass


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Provider authentication failed."""
    pass


class BaseProvider(ABC):
    """Base interface for hotel booking providers."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """Initialize provider with credentials."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.provider_name = self.__class__.__name__
    
    @property
    @abstractmethod
    def provider(self) -> Provider:
        """Get provider enum value."""
        pass
    
    @abstractmethod
    async def search_hotels(
        self,
        destination: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        rooms: int = 1,
        **kwargs
    ) -> List[Hotel]:
        """Search for hotels by destination and dates.
        
        Args:
            destination: City name or location
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            **kwargs: Additional search parameters
            
        Returns:
            List of Hotel domain models
            
        Raises:
            ProviderError: If search fails
            ProviderTimeoutError: If request times out
            ProviderRateLimitError: If rate limit exceeded
        """
        pass
    
    @abstractmethod
    async def get_hotel_details(
        self,
        provider_hotel_id: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        **kwargs
    ) -> Optional[Hotel]:
        """Get detailed information about a specific hotel.
        
        Args:
            provider_hotel_id: Hotel ID from provider
            check_in: Optional check-in date
            check_out: Optional check-out date
            **kwargs: Additional parameters
            
        Returns:
            Hotel domain model or None if not found
            
        Raises:
            ProviderError: If request fails
        """
        pass
    
    @abstractmethod
    async def get_offers(
        self,
        provider_hotel_id: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        rooms: int = 1,
        **kwargs
    ) -> List[Offer]:
        """Get available offers/rates for a hotel.
        
        Args:
            provider_hotel_id: Hotel ID from provider
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            **kwargs: Additional parameters
            
        Returns:
            List of Offer domain models
            
        Raises:
            ProviderError: If request fails
        """
        pass
    
    @abstractmethod
    async def get_reviews(
        self,
        provider_hotel_id: str,
        limit: int = 10,
        **kwargs
    ) -> List[Review]:
        """Get reviews for a hotel.
        
        Args:
            provider_hotel_id: Hotel ID from provider
            limit: Maximum number of reviews to return
            **kwargs: Additional parameters
            
        Returns:
            List of Review domain models
            
        Raises:
            ProviderError: If request fails
        """
        pass
    
    @abstractmethod
    def generate_affiliate_link(
        self,
        provider_hotel_id: str,
        check_in: date,
        check_out: date,
        guests: int = 1,
        rooms: int = 1,
        **kwargs
    ) -> str:
        """Generate affiliate booking link.
        
        Args:
            provider_hotel_id: Hotel ID from provider
            check_in: Check-in date
            check_out: Check-out date
            guests: Number of guests
            rooms: Number of rooms
            **kwargs: Additional parameters
            
        Returns:
            Affiliate URL string
        """
        pass
    
    def validate_credentials(self) -> bool:
        """Validate provider credentials.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        return bool(self.api_key)
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information.
        
        Returns:
            Dictionary with rate limit details (requests_per_minute, etc.)
        """
        return {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }
    
    async def health_check(self) -> bool:
        """Check if provider API is healthy.
        
        Returns:
            True if provider is available, False otherwise
        """
        try:
            # Simple health check - can be overridden by providers
            return self.validate_credentials()
        except Exception:
            return False

