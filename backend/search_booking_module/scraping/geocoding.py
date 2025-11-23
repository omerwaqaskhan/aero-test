"""Geocoding service for getting coordinates from addresses."""

from typing import Optional, Tuple
import aiohttp
import logging

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for geocoding addresses to coordinates."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize geocoding service.
        
        Args:
            api_key: API key for geocoding service (optional, uses free service if not provided)
        """
        self.api_key = api_key
        self.base_url = "https://nominatim.openstreetmap.org"  # Free geocoding service
    
    async def geocode(
        self,
        address: str,
        city: Optional[str] = None,
        country: Optional[str] = None
    ) -> Optional[Tuple[float, float]]:
        """Geocode an address to latitude and longitude.
        
        Args:
            address: Street address
            city: City name
            country: Country name
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        try:
            # Build query
            query_parts = []
            if address:
                query_parts.append(address)
            if city:
                query_parts.append(city)
            if country:
                query_parts.append(country)
            
            query = ", ".join(query_parts)
            
            # Use OpenStreetMap Nominatim (free, no API key required)
            url = f"{self.base_url}/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
            }
            
            headers = {
                'User-Agent': 'HotelDataCollector/1.0'  # Required by Nominatim
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            result = data[0]
                            lat = float(result.get('lat', 0))
                            lon = float(result.get('lon', 0))
                            return (lat, lon)
            
            logger.warning(f"Could not geocode: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding {query}: {e}")
            return None
    
    async def geocode_city(self, city: str, country: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """Geocode a city to get default coordinates.
        
        Args:
            city: City name
            country: Country name (optional)
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        return await self.geocode(address="", city=city, country=country)

