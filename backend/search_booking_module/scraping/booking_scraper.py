"""Booking.com scraper for hotel data."""

from typing import List, Dict, Any, Optional
from datetime import date
from bs4 import BeautifulSoup
import re
import logging
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BookingScraper(BaseScraper):
    """Scraper for Booking.com hotel listings."""
    
    def __init__(self):
        """Initialize Booking.com scraper."""
        super().__init__(
            base_url="https://www.booking.com",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
        )
    
    async def search_hotels(
        self,
        destination: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for hotels on Booking.com."""
        hotels = []
        
        try:
            # Booking.com search URL
            search_url = f"{self.base_url}/searchresults.html"
            params = {
                'ss': destination,
                'checkin_month': check_in.month if check_in else None,
                'checkin_monthday': check_in.day if check_in else None,
                'checkin_year': check_in.year if check_in else None,
                'checkout_month': check_out.month if check_out else None,
                'checkout_monthday': check_out.day if check_out else None,
                'checkout_year': check_out.year if check_out else None,
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            html = await self.fetch_page(search_url, params)
            if not html:
                return hotels
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find hotel listings (Booking.com structure)
            hotel_elements = soup.find_all('div', {'data-testid': 'property-card'})
            
            if not hotel_elements:
                # Try alternative selectors
                hotel_elements = soup.find_all('div', class_=re.compile(r'property|hotel|sr_item', re.I))
            
            for element in hotel_elements[:25]:  # Limit to 25 hotels
                hotel_data = self._extract_hotel_info(element, destination)
                if hotel_data:
                    hotels.append(hotel_data)
                
                await self.delay(0.5)
            
        except Exception as e:
            logger.error(f"Error scraping Booking.com for {destination}: {e}")
        
        return hotels
    
    def _extract_hotel_info(self, element, destination: str) -> Optional[Dict[str, Any]]:
        """Extract hotel information from Booking.com element."""
        try:
            # Extract hotel name
            name_elem = element.find(['h3', 'a'], class_=re.compile(r'property|hotel|name', re.I))
            if not name_elem:
                name_elem = element.find('a', {'data-testid': 'title-link'})
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            # Extract rating/score
            rating_elem = element.find('div', class_=re.compile(r'score|rating|review', re.I))
            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Extract price
            price_elem = element.find('span', class_=re.compile(r'price|cost|amount', re.I))
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\$€£¥]?(\d+)', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group(1))
            
            # Extract address
            address_elem = element.find('span', class_=re.compile(r'address|location|area', re.I))
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Extract image
            img_elem = element.find('img')
            image_url = None
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy')
            
            # Extract link
            link_elem = element.find('a', href=True)
            hotel_url = None
            if link_elem:
                href = link_elem.get('href')
                if href:
                    hotel_url = f"{self.base_url}{href}" if href.startswith('/') else href
            
            # Extract stars (if available)
            stars_elem = element.find('span', class_=re.compile(r'star|rating', re.I))
            stars = None
            if stars_elem:
                stars_text = stars_elem.get_text(strip=True)
                stars_match = re.search(r'(\d+)', stars_text)
                if stars_match:
                    stars = int(stars_match.group(1))
            
            return {
                'name': name,
                'city': destination,
                'address': address or destination,
                'rating': rating,
                'price_per_night': price,
                'image_url': image_url,
                'source_url': hotel_url,
                'source': 'booking.com',
                'stars': stars,
                'amenities': [],
            }
        except Exception as e:
            logger.error(f"Error extracting hotel info from Booking.com: {e}")
            return None
    
    async def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed hotel information."""
        return None

