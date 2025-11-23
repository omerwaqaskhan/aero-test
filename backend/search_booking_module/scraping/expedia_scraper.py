"""Enhanced Expedia scraper with headless browser support for detailed hotel information."""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from bs4 import BeautifulSoup
import re
import logging
import json
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. Install with: pip install playwright && playwright install")


class ExpediaScraper(BaseScraper):
    """Enhanced scraper for Expedia with headless browser support."""
    
    def __init__(self, use_browser: bool = True):
        """Initialize enhanced Expedia scraper.
        
        Args:
            use_browser: Whether to use headless browser for JavaScript-rendered content
        """
        super().__init__(
            base_url="https://www.expedia.com",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        self.use_browser = use_browser and PLAYWRIGHT_AVAILABLE
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await super().__aenter__()
        if self.use_browser:
            try:
                import os
                playwright_cache = os.path.expanduser('~/.cache/ms-playwright')
                if os.path.exists(playwright_cache):
                    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', playwright_cache)
                
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
                logger.info("Expedia scraper: Browser launched successfully")
            except Exception as e:
                logger.warning(f"Failed to start browser: {e}. Falling back to basic scraping.")
                self.use_browser = False
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await super().__aexit__(exc_type, exc_val, exc_tb)
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _fetch_with_browser(self, url: str, wait_selector: Optional[str] = None) -> Optional[str]:
        """Fetch page using headless browser."""
        if not self.browser:
            return None
        
        try:
            clean_url = url.split('?')[0] if '?' in url else url
            page = await self.browser.new_page()
            
            try:
                await page.goto(clean_url, wait_until='domcontentloaded', timeout=60000)
            except Exception as e:
                logger.warning(f"Timeout loading {clean_url}, trying with load event: {e}")
                try:
                    await page.goto(clean_url, wait_until='load', timeout=60000)
                except Exception as e2:
                    logger.error(f"Failed to load {clean_url}: {e2}")
                    await page.close()
                    return None
            
            await page.wait_for_timeout(2000)
            await self._interact_with_page(page)
            await page.wait_for_timeout(3000)
            
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=5000)
                except:
                    pass
            
            html = await page.content()
            await page.close()
            
            if html and len(html) > 1000:
                return html
            else:
                logger.warning(f"Received empty or too short HTML from {clean_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching with browser {url}: {e}")
            return None
    
    async def _interact_with_page(self, page) -> None:
        """Interact with page to trigger dynamic content loading."""
        try:
            viewport_height = await page.evaluate('window.innerHeight')
            total_height = await page.evaluate('document.body.scrollHeight')
            
            scroll_steps = 3
            scroll_distance = total_height // scroll_steps
            
            for i in range(scroll_steps):
                scroll_position = scroll_distance * (i + 1)
                await page.evaluate(f'window.scrollTo(0, {scroll_position})')
                await page.wait_for_timeout(1000)
            
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(1000)
                    
        except Exception as e:
            logger.debug(f"Error interacting with page: {e}")
            pass
    
    async def search_hotels(
        self,
        destination: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for hotels on Expedia."""
        hotels = []
        
        try:
            # Expedia search URL - correct format
            from urllib.parse import quote_plus
            from datetime import timedelta
            
            # Default dates if not provided
            if not check_in:
                check_in = date.today() + timedelta(days=1)
            if not check_out:
                check_out = check_in + timedelta(days=2)
            
            search_url = f"{self.base_url}/Hotel-Search"
            params = []
            
            # URL encode destination
            params.append(f"destination={quote_plus(destination)}")
            params.append(f"startDate={check_in.strftime('%Y-%m-%d')}")
            params.append(f"endDate={check_out.strftime('%Y-%m-%d')}")
            
            # Add default room and guest parameters
            params.append("rooms=1")
            params.append("adults=2")
            
            # Build URL with parameters
            url = f"{search_url}?" + "&".join(params)
            
            # Fetch search results
            if self.use_browser:
                html = await self._fetch_with_browser(url)
            else:
                html = await self.fetch_page(url)
            
            if not html:
                return hotels
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract hotel listings - try multiple selectors for Expedia
            hotel_elements = []
            
            # Try data-testid attributes
            hotel_elements = soup.find_all('div', {'data-testid': re.compile(r'hotel|property|listing', re.I)})
            
            # Try class-based selectors
            if not hotel_elements:
                hotel_elements = soup.find_all('div', class_=re.compile(r'hotel|property|listing|result', re.I))
            
            # Try article tags
            if not hotel_elements:
                hotel_elements = soup.find_all('article', class_=re.compile(r'hotel|property', re.I))
            
            # Try section tags
            if not hotel_elements:
                hotel_elements = soup.find_all('section', class_=re.compile(r'hotel|property', re.I))
            
            for element in hotel_elements[:50]:  # Limit to 50
                hotel_info = self._extract_hotel_info(element, destination)
                if hotel_info:
                    hotel_info['source'] = 'expedia'
                    hotels.append(hotel_info)
            
            logger.info(f"Found {len(hotels)} hotels on Expedia for {destination}")
            
        except Exception as e:
            logger.error(f"Error searching Expedia for {destination}: {e}")
        
        return hotels
    
    def _extract_hotel_info(self, element, destination: str) -> Optional[Dict[str, Any]]:
        """Extract hotel information from Expedia element."""
        try:
            # Extract hotel name
            name_elem = element.find(['h3', 'h4', 'a'], class_=re.compile(r'hotel|property|name', re.I))
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            # Extract rating
            rating_elem = element.find('span', class_=re.compile(r'rating|score|review', re.I))
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
            
            # Extract stars
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
                'source': 'expedia',
                'stars': stars,
                'amenities': [],
            }
        except Exception as e:
            logger.error(f"Error extracting hotel info from Expedia: {e}")
            return None
    
    async def get_hotel_details(self, hotel_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed hotel information from Expedia hotel detail page."""
        if not hotel_url:
            return None
        
        try:
            if self.use_browser:
                html = await self._fetch_with_browser(hotel_url, wait_selector=None)
            else:
                html = await self.fetch_page(hotel_url)
            
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            details = {
                'description': self._extract_description(soup),
                'property_overview': self._extract_property_overview(soup),
                'images': self._extract_all_images(soup),
                'amenities': self._extract_amenities(soup),
                'policies': self._extract_policies(soup),
                'rooms': await self._extract_rooms(soup, hotel_url),
                'reviews': self._extract_reviews(soup),
                'location_details': self._extract_location_details(soup),
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting hotel details from Expedia {hotel_url}: {e}")
            return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract hotel description."""
        try:
            desc_elem = soup.find('div', class_=re.compile(r'description|property-description', re.I))
            if not desc_elem:
                desc_elem = soup.find('div', id=re.compile(r'description', re.I))
            
            if desc_elem:
                for script in desc_elem(["script", "style"]):
                    script.decompose()
                return desc_elem.get_text(separator='\n', strip=True)
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting description: {e}")
            return ""
    
    def _extract_property_overview(self, soup: BeautifulSoup) -> str:
        """Extract property overview."""
        try:
            overview_elem = soup.find('div', class_=re.compile(r'overview|property-overview|summary', re.I))
            if overview_elem:
                for script in overview_elem(["script", "style"]):
                    script.decompose()
                return overview_elem.get_text(separator='\n', strip=True)
            return ""
        except:
            return ""
    
    def _extract_all_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract all hotel images."""
        images = []
        try:
            img_elements = soup.find_all('img', class_=re.compile(r'hotel|property|gallery', re.I))
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src and src not in images:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    images.append(src)
            return images[:50]  # Limit to 50 images
        except:
            return []
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract hotel amenities."""
        amenities = []
        try:
            amenities_section = soup.find('div', class_=re.compile(r'amenities|facilities|features', re.I))
            if amenities_section:
                amenity_items = amenities_section.find_all(['li', 'span', 'div'], class_=re.compile(r'amenity|facility|feature', re.I))
                for item in amenity_items:
                    text = item.get_text(strip=True)
                    if text and text not in amenities:
                        amenities.append(text)
            return amenities
        except:
            return []
    
    def _extract_policies(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract hotel policies."""
        policies = {}
        try:
            policies_section = soup.find('div', class_=re.compile(r'policies|policy|rules', re.I))
            if policies_section:
                # Extract check-in/out times
                check_in_elem = policies_section.find(string=re.compile(r'check-in|check in', re.I))
                check_out_elem = policies_section.find(string=re.compile(r'check-out|check out', re.I))
                
                if check_in_elem:
                    check_in_text = check_in_elem.find_next(string=True)
                    if check_in_text:
                        policies['check_in'] = check_in_text.strip()
                
                if check_out_elem:
                    check_out_text = check_out_elem.find_next(string=True)
                    if check_out_text:
                        policies['check_out'] = check_out_text.strip()
            
            return policies
        except:
            return {}
    
    async def _extract_rooms(self, soup: BeautifulSoup, hotel_url: str) -> List[Dict[str, Any]]:
        """Extract room information."""
        rooms = []
        try:
            # Try multiple strategies to find rooms
            room_elements = soup.find_all('div', class_=re.compile(r'room|accommodation|suite', re.I))
            
            for room_elem in room_elements[:20]:
                room_name = self._extract_room_name(room_elem)
                if not room_name:
                    continue
                
                room_data = {
                    'room_type_name': room_name,
                    'description': self._extract_room_description(room_elem),
                    'images': self._extract_room_images(room_elem),
                    'occupancy': self._extract_room_occupancy(room_elem),
                    'amenities': self._extract_room_amenities(room_elem),
                }
                
                rooms.append(room_data)
            
            return rooms
        except Exception as e:
            logger.error(f"Error extracting rooms: {e}")
            return []
    
    def _extract_room_name(self, room_elem) -> str:
        """Extract room name."""
        try:
            name_elem = room_elem.find(['h3', 'h4', 'h5'], class_=re.compile(r'room|title|name', re.I))
            if not name_elem:
                name_elem = room_elem.find('div', class_=re.compile(r'room.*name|room.*title', re.I))
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name and len(name) > 3:
                    return name
            return ""
        except:
            return ""
    
    def _extract_room_description(self, room_elem) -> str:
        """Extract room description."""
        try:
            desc_elem = room_elem.find('div', class_=re.compile(r'description|details', re.I))
            if desc_elem:
                return desc_elem.get_text(separator='\n', strip=True)
            return ""
        except:
            return ""
    
    def _extract_room_images(self, room_elem) -> List[str]:
        """Extract room images."""
        images = []
        try:
            img_elements = room_elem.find_all('img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src and src not in images:
                    if src.startswith('//'):
                        src = 'https:' + src
                    images.append(src)
            return images[:5]
        except:
            return []
    
    def _extract_room_occupancy(self, room_elem) -> Dict[str, Any]:
        """Extract room occupancy details."""
        occupancy = {}
        try:
            size_elem = room_elem.find(string=re.compile(r'(\d+)\s*(sqm|sq\s*ft|m²)', re.I))
            if size_elem:
                size_match = re.search(r'(\d+)', size_elem)
                if size_match:
                    occupancy['size'] = int(size_match.group(1))
            
            guests_elem = room_elem.find(string=re.compile(r'(\d+)\s*(guest|person|people)', re.I))
            if guests_elem:
                guests_match = re.search(r'(\d+)', guests_elem)
                if guests_match:
                    occupancy['max_guests'] = int(guests_match.group(1))
            
            return occupancy
        except:
            return {}
    
    def _extract_room_amenities(self, room_elem) -> List[str]:
        """Extract room amenities."""
        amenities = []
        try:
            amenity_items = room_elem.find_all(['li', 'span'], class_=re.compile(r'amenity|feature', re.I))
            for item in amenity_items:
                text = item.get_text(strip=True)
                if text:
                    amenities.append(text)
            return amenities
        except:
            return []
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract hotel reviews."""
        reviews = []
        try:
            reviews_section = soup.find('div', class_=re.compile(r'reviews|testimonials', re.I))
            if reviews_section:
                review_elements = reviews_section.find_all('div', class_=re.compile(r'review|testimonial|comment', re.I))
                
                for review_elem in review_elements[:20]:
                    review_data = {
                        'title': self._extract_review_title(review_elem),
                        'text': self._extract_review_text(review_elem),
                        'author': self._extract_review_author(review_elem),
                        'rating': self._extract_review_rating(review_elem),
                        'pros': [],
                        'cons': [],
                        'category_ratings': {},
                    }
                    
                    if review_data['text'] or review_data['title']:
                        reviews.append(review_data)
            
            return reviews
        except Exception as e:
            logger.error(f"Error extracting reviews: {e}")
            return []
    
    def _extract_review_title(self, review_elem) -> str:
        """Extract review title."""
        try:
            title_elem = review_elem.find(['h3', 'h4', 'h5'], class_=re.compile(r'title|heading', re.I))
            if title_elem:
                return title_elem.get_text(strip=True)
            return ""
        except:
            return ""
    
    def _extract_review_text(self, review_elem) -> str:
        """Extract review text."""
        try:
            text_elem = review_elem.find('div', class_=re.compile(r'text|content|comment', re.I))
            if text_elem:
                return text_elem.get_text(strip=True)
            return ""
        except:
            return ""
    
    def _extract_review_author(self, review_elem) -> str:
        """Extract review author."""
        try:
            author_elem = review_elem.find('span', class_=re.compile(r'author|name|user', re.I))
            if author_elem:
                return author_elem.get_text(strip=True)
            return ""
        except:
            return ""
    
    def _extract_review_rating(self, review_elem) -> float:
        """Extract review rating."""
        try:
            rating_elem = review_elem.find('span', class_=re.compile(r'rating|score', re.I))
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    return float(rating_match.group(1))
            return 0.0
        except:
            return 0.0
    
    def _extract_location_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract location details."""
        return {}

