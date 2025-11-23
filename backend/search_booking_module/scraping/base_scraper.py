"""Base scraper class for hotel data collection."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for hotel data scrapers."""
    
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize scraper with base URL and headers."""
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Fetch a web page and return HTML content."""
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
    
    async def fetch_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
        """Fetch JSON data from an API endpoint."""
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to fetch JSON from {url}: Status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching JSON from {url}: {e}")
            return None
    
    @abstractmethod
    async def search_hotels(
        self,
        destination: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for hotels in a destination.
        
        Returns:
            List of hotel data dictionaries
        """
        pass
    
    @abstractmethod
    async def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific hotel."""
        pass
    
    def parse_hotel_data(self, raw_data: Any) -> Dict[str, Any]:
        """Parse raw scraped data into standardized hotel format."""
        # Override in subclasses for specific parsing logic
        return {}
    
    async def delay(self, seconds: float = 1.0):
        """Add delay between requests to be respectful."""
        await asyncio.sleep(seconds)

