"""Scraper for hotel official websites."""

from typing import List, Dict, Any, Optional
from datetime import date
from bs4 import BeautifulSoup
import re
import logging
import aiohttp
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class HotelWebsiteScraper:
    """Scraper for hotel official websites."""
    
    def __init__(self, use_browser: bool = True):
        """Initialize hotel website scraper."""
        self.base_url = ""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.use_browser = use_browser
        self.browser = None
        self.playwright = None
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page using aiohttp."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
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
                logger.info("Browser launched successfully for hotel website scraper")
            except Exception as e:
                logger.warning(f"Could not launch browser for hotel website scraper: {e}")
                self.use_browser = False
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
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
    
    async def scrape_hotel_website(self, website_url: str) -> Optional[Dict[str, Any]]:
        """Scrape hotel's official website for comprehensive information.
        
        Args:
            website_url: Official website URL of the hotel
            
        Returns:
            Dictionary with hotel information from official website
        """
        if not website_url:
            return None
        
        try:
            logger.info(f"Scraping hotel website: {website_url}")
            
            # Fetch page
            if self.use_browser:
                html = await self._fetch_with_browser(website_url)
            else:
                html = await self.fetch_page(website_url)
            
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract information
            details = {
                'description': self._extract_description(soup),
                'property_overview': self._extract_property_overview(soup),
                'images': self._extract_all_images(soup),
                'amenities': self._extract_amenities(soup),
                'policies': self._extract_policies(soup),
                'rooms': await self._extract_rooms(soup, website_url),
                'reviews': self._extract_reviews(soup),
                'location_details': self._extract_location_details(soup),
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error scraping hotel website {website_url}: {e}")
            return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract hotel description from official website."""
        try:
            # Try multiple selectors for description
            desc_selectors = [
                ('div', {'class': re.compile(r'description|about|overview', re.I)}),
                ('section', {'class': re.compile(r'description|about|overview', re.I)}),
                ('div', {'id': re.compile(r'description|about|overview', re.I)}),
                ('article', {'class': re.compile(r'description|about', re.I)}),
            ]
            
            for tag, attrs in desc_selectors:
                desc_elem = soup.find(tag, attrs)
                if desc_elem:
                    # Remove scripts and styles
                    for script in desc_elem(["script", "style"]):
                        script.decompose()
                    text = desc_elem.get_text(separator='\n', strip=True)
                    if text and len(text) > 100:
                        return text
            
            return ""
        except Exception as e:
            logger.debug(f"Error extracting description: {e}")
            return ""
    
    def _extract_property_overview(self, soup: BeautifulSoup) -> str:
        """Extract property overview from official website."""
        try:
            # Look for property overview section
            overview_selectors = [
                ('div', {'class': re.compile(r'property|overview|features', re.I)}),
                ('section', {'class': re.compile(r'property|overview', re.I)}),
            ]
            
            for tag, attrs in overview_selectors:
                overview_elem = soup.find(tag, attrs)
                if overview_elem:
                    for script in overview_elem(["script", "style"]):
                        script.decompose()
                    text = overview_elem.get_text(separator='\n', strip=True)
                    if text and len(text) > 50:
                        return text
            
            return ""
        except Exception as e:
            logger.debug(f"Error extracting property overview: {e}")
            return ""
    
    def _extract_all_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract all images from hotel website."""
        images = []
        try:
            # Find all images
            img_elements = soup.find_all('img')
            
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy') or img.get('data-original')
                if src:
                    # Clean up image URL
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        # Try to construct full URL from base
                        base_url = self.base_url or ''
                        if base_url:
                            src = base_url + src
                    
                    if src.startswith(('http://', 'https://')):
                        # Filter out small icons and logos
                        if not any(skip in src.lower() for skip in ['icon', 'logo', 'sprite', 'pixel', 'tracking']):
                            if src not in images:
                                images.append(src)
            
            return images[:50]  # Limit to 50 images
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract amenities from hotel website."""
        amenities = []
        try:
            # Look for amenities section
            amenities_section = soup.find('div', class_=re.compile(r'amenities|facilities|features|services', re.I))
            if not amenities_section:
                amenities_section = soup.find('section', class_=re.compile(r'amenities|facilities', re.I))
            
            if amenities_section:
                # Find all amenity items
                amenity_items = amenities_section.find_all(['li', 'div', 'span'], class_=re.compile(r'amenity|facility|feature', re.I))
                
                for item in amenity_items:
                    text = item.get_text(strip=True)
                    if text and len(text) < 100:
                        amenities.append(text)
            
            return list(set(amenities))  # Remove duplicates
        except Exception as e:
            logger.debug(f"Error extracting amenities: {e}")
            return []
    
    def _extract_policies(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract policies from hotel website."""
        policies = {}
        try:
            # Look for policies section
            policies_section = soup.find('div', class_=re.compile(r'policies|terms|conditions|house-rules', re.I))
            
            if policies_section:
                # Extract check-in/check-out
                check_in_elem = policies_section.find(string=re.compile(r'check-in|checkin', re.I))
                check_out_elem = policies_section.find(string=re.compile(r'check-out|checkout', re.I))
                
                if check_in_elem:
                    check_in_text = check_in_elem.find_next(string=True)
                    if check_in_text:
                        policies['check_in'] = check_in_text.strip()
                
                if check_out_elem:
                    check_out_text = check_out_elem.find_next(string=True)
                    if check_out_text:
                        policies['check_out'] = check_out_text.strip()
            
            return policies
        except Exception as e:
            logger.debug(f"Error extracting policies: {e}")
            return {}
    
    async def _extract_rooms(self, soup: BeautifulSoup, website_url: str) -> List[Dict[str, Any]]:
        """Extract room information from hotel website."""
        rooms = []
        try:
            # Look for rooms section
            rooms_section = soup.find('div', class_=re.compile(r'rooms|accommodations|suites', re.I))
            if not rooms_section:
                rooms_section = soup.find('section', class_=re.compile(r'rooms|accommodations', re.I))
            
            if rooms_section:
                # Find room cards/items
                room_elements = rooms_section.find_all(['div', 'article'], class_=re.compile(r'room|accommodation|suite', re.I))
                
                for room_elem in room_elements:
                    room_name = self._extract_room_name(room_elem)
                    if room_name:
                        rooms.append({
                            'room_type_name': room_name,
                            'description': self._extract_room_description(room_elem),
                            'images': self._extract_room_images(room_elem),
                            'occupancy': self._extract_room_occupancy(room_elem),
                            'amenities': self._extract_room_amenities(room_elem),
                        })
            
            return rooms
        except Exception as e:
            logger.debug(f"Error extracting rooms: {e}")
            return []
    
    def _extract_room_name(self, room_elem) -> str:
        """Extract room name."""
        try:
            name_elem = room_elem.find(['h2', 'h3', 'h4', 'h5'], class_=re.compile(r'room|title|name', re.I))
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
                if src and src.startswith(('http://', 'https://')):
                    images.append(src)
            return images[:10]
        except:
            return []
    
    def _extract_room_occupancy(self, room_elem) -> Dict[str, Any]:
        """Extract room occupancy."""
        occupancy = {}
        try:
            # Look for size, guests, bed info
            text = room_elem.get_text()
            size_match = re.search(r'(\d+)\s*(sqm|sq\s*ft|m²)', text, re.I)
            if size_match:
                occupancy['size'] = int(size_match.group(1))
            
            guests_match = re.search(r'(\d+)\s*(guest|person|people)', text, re.I)
            if guests_match:
                occupancy['max_guests'] = int(guests_match.group(1))
            
            return occupancy
        except:
            return {}
    
    def _extract_room_amenities(self, room_elem) -> List[str]:
        """Extract room amenities."""
        amenities = []
        try:
            amenity_items = room_elem.find_all('li', class_=re.compile(r'amenity|feature', re.I))
            for item in amenity_items:
                text = item.get_text(strip=True)
                if text:
                    amenities.append(text)
            return amenities
        except:
            return []
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract reviews from hotel website."""
        # Hotel websites usually don't have reviews
        return []
    
    def _extract_location_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract location details."""
        return {}

