"""TripAdvisor scraper for hotel data."""

from typing import List, Dict, Any, Optional
from datetime import date
from bs4 import BeautifulSoup
import re
import logging
import aiohttp
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TripAdvisorScraper(BaseScraper):
    """Scraper for TripAdvisor hotel listings."""
    
    def __init__(self, use_browser: bool = False):
        """Initialize TripAdvisor scraper."""
        super().__init__(
            base_url="https://www.tripadvisor.com",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        self.use_browser = use_browser
        self.browser = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.use_browser:
            try:
                from playwright.async_api import async_playwright
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
                logger.info("Browser launched successfully for TripAdvisor scraper")
            except Exception as e:
                logger.warning(f"Could not launch browser for TripAdvisor scraper: {e}")
                self.use_browser = False
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def search_hotels(
        self,
        destination: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for hotels on TripAdvisor."""
        hotels = []
        
        try:
            # Search URL for hotels in destination
            search_url = f"{self.base_url}/Search"
            params = {
                'q': f'hotels in {destination}',
                'geo': '1',
            }
            
            html = await self.fetch_page(search_url, params)
            if not html:
                return hotels
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find hotel listings (adjust selectors based on actual page structure)
            hotel_elements = soup.find_all('div', class_=re.compile(r'hotel|listing|property', re.I))
            
            for element in hotel_elements[:20]:  # Limit to 20 hotels per search
                hotel_data = self._extract_hotel_info(element, destination)
                if hotel_data:
                    hotels.append(hotel_data)
                
                await self.delay(0.5)  # Be respectful with requests
            
        except Exception as e:
            logger.error(f"Error scraping TripAdvisor for {destination}: {e}")
        
        return hotels
    
    def _extract_hotel_info(self, element, destination: str) -> Optional[Dict[str, Any]]:
        """Extract hotel information from HTML element."""
        try:
            # Extract hotel name
            name_elem = element.find(['h2', 'h3', 'a'], class_=re.compile(r'name|title', re.I))
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            # Extract rating
            rating_elem = element.find('span', class_=re.compile(r'rating|score', re.I))
            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Extract price (if available)
            price_elem = element.find('span', class_=re.compile(r'price|cost', re.I))
            price = None
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\$€£¥]?(\d+)', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group(1))
            
            # Extract address
            address_elem = element.find('span', class_=re.compile(r'address|location', re.I))
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Extract image
            img_elem = element.find('img')
            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
            
            # Extract link
            link_elem = element.find('a', href=True)
            hotel_url = None
            if link_elem:
                href = link_elem.get('href')
                if href:
                    hotel_url = f"{self.base_url}{href}" if href.startswith('/') else href
            
            return {
                'name': name,
                'city': destination,
                'address': address or f"{destination}",
                'rating': rating,
                'price_per_night': price,
                'image_url': image_url,
                'source_url': hotel_url,
                'source': 'tripadvisor',
                'amenities': [],  # Would need to scrape details page
            }
        except Exception as e:
            logger.error(f"Error extracting hotel info: {e}")
            return None
    
    async def get_hotel_details(self, hotel_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed hotel information from TripAdvisor hotel page.
        
        Args:
            hotel_url: URL of the TripAdvisor hotel page
            
        Returns:
            Dictionary with hotel details including amenities
        """
        if not hotel_url:
            return None
        
        try:
            logger.info(f"Scraping TripAdvisor hotel page: {hotel_url}")
            
            # Fetch page
            if self.use_browser:
                html = await self._fetch_with_browser(hotel_url)
            else:
                html = await self.fetch_page(hotel_url)
            
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract amenities
            amenities = self._extract_amenities(soup)
            
            # Extract reviews (for amenities extraction)
            reviews = self._extract_reviews(soup)
            
            # Extract amenities from reviews
            review_amenities = self._extract_amenities_from_reviews(reviews)
            if review_amenities:
                # Merge amenities
                existing_amenities_lower = {a.lower() for a in amenities}
                for review_amenity in review_amenities:
                    if review_amenity.lower() not in existing_amenities_lower:
                        amenities.append(review_amenity)
                        existing_amenities_lower.add(review_amenity.lower())
            
            return {
                'amenities': amenities,
                'reviews': reviews,
            }
        except Exception as e:
            logger.error(f"Error scraping TripAdvisor hotel page {hotel_url}: {e}")
            return None
    
    async def _fetch_with_browser(self, url: str) -> Optional[str]:
        """Fetch page using headless browser."""
        if not self.browser:
            return None
        
        try:
            page = await self.browser.new_page()
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(3000)  # Wait for dynamic content
                
                # Scroll to trigger lazy loading
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                await page.wait_for_timeout(2000)
                
                html = await page.content()
                await page.close()
                
                if html and len(html) > 1000:
                    return html
            except Exception as e:
                logger.warning(f"Error fetching {url} with browser: {e}")
                await page.close()
                return None
        except Exception as e:
            logger.error(f"Error in browser fetch: {e}")
            return None
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract amenities from TripAdvisor page."""
        amenities = []
        try:
            # Strategy 1: Look for amenities section
            amenities_section = soup.find('div', class_=re.compile(r'amenities|facilities|features', re.I))
            if not amenities_section:
                amenities_section = soup.find('section', class_=re.compile(r'amenities|facilities', re.I))
            
            if amenities_section:
                # Find all amenity items
                amenity_items = amenities_section.find_all(['li', 'div', 'span'], class_=re.compile(r'amenity|facility|feature', re.I))
                
                for item in amenity_items:
                    text = item.get_text(strip=True)
                    if text and len(text) < 100 and len(text) > 2:
                        amenities.append(text)
            
            # Strategy 2: Look for structured data
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'amenityFeature' in data:
                        for amenity in data['amenityFeature']:
                            if isinstance(amenity, dict) and 'name' in amenity:
                                amenities.append(amenity['name'])
                except:
                    pass
            
            return list(set(amenities))  # Remove duplicates
        except Exception as e:
            logger.debug(f"Error extracting amenities from TripAdvisor: {e}")
            return []
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract reviews from TripAdvisor page."""
        reviews = []
        try:
            # Find reviews section
            reviews_section = soup.find('div', class_=re.compile(r'reviews|review', re.I))
            if reviews_section:
                review_elements = reviews_section.find_all('div', class_=re.compile(r'review|comment', re.I))
                
                for review_elem in review_elements[:10]:  # Limit to 10 reviews
                    text = review_elem.get_text(strip=True)
                    if text and len(text) > 20:
                        reviews.append({
                            'text': text,
                            'title': '',
                            'author': '',
                            'rating': None,
                        })
            
            return reviews
        except Exception as e:
            logger.debug(f"Error extracting reviews from TripAdvisor: {e}")
            return []
    
    def _extract_amenities_from_reviews(self, reviews: List[Dict[str, Any]]) -> List[str]:
        """Extract amenities mentioned in reviews."""
        amenities = []
        try:
            # Common amenities to look for
            common_amenities = {
                'wifi': ['wifi', 'wi-fi', 'wireless', 'internet'],
                'parking': ['parking', 'valet', 'garage'],
                'pool': ['pool', 'swimming pool'],
                'gym': ['gym', 'fitness', 'fitness center'],
                'spa': ['spa', 'massage', 'sauna'],
                'restaurant': ['restaurant', 'dining', 'breakfast'],
                'bar': ['bar', 'lounge'],
                'room service': ['room service'],
                'air conditioning': ['air conditioning', 'ac'],
                'breakfast': ['breakfast', 'continental breakfast'],
            }
            
            # Extract text from all reviews
            review_texts = []
            for review in reviews:
                text = review.get('text', '') or review.get('title', '')
                if text:
                    review_texts.append(text.lower())
            
            # Combine all review text
            all_review_text = ' '.join(review_texts)
            
            # Look for amenities
            found_amenities = set()
            for amenity_name, keywords in common_amenities.items():
                for keyword in keywords:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, all_review_text, re.IGNORECASE):
                        found_amenities.add(amenity_name.title())
                        break
            
            return list(found_amenities)
        except Exception as e:
            logger.debug(f"Error extracting amenities from reviews: {e}")
            return []

