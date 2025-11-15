"""Enhanced Booking.com scraper with headless browser support for detailed hotel information."""

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


class EnhancedBookingScraper(BaseScraper):
    """Enhanced scraper for Booking.com with headless browser support."""
    
    def __init__(self, use_browser: bool = True):
        """Initialize enhanced Booking.com scraper.
        
        Args:
            use_browser: Whether to use headless browser for JavaScript-rendered content
        """
        super().__init__(
            base_url="https://www.booking.com",
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
                # Set Playwright browser path if running as non-root user
                playwright_cache = os.path.expanduser('~/.cache/ms-playwright')
                if os.path.exists(playwright_cache):
                    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', playwright_cache)
                
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
                logger.info("Browser launched successfully")
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
    
    async def _fetch_with_browser_and_intercept(self, url: str, wait_selector: Optional[str] = None) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Fetch page using headless browser and intercept API responses."""
        return await self._fetch_with_browser(url, wait_selector)
    
    async def _fetch_with_browser(self, url: str, wait_selector: Optional[str] = None) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """Fetch page using headless browser."""
        if not self.browser:
            return None
        
        try:
            # Clean URL - remove query parameters that might cause issues
            # Keep only the base hotel URL
            clean_url = url.split('?')[0] if '?' in url else url
            
            page = await self.browser.new_page()
            
            # Intercept network requests to capture room data from API calls
            room_data_from_api = []
            
            async def handle_response(response):
                """Intercept API responses that might contain room data."""
                try:
                    url_lower = response.url.lower()
                    # Look for API calls that might contain room data
                    # Exclude chunk-metadata and other non-data endpoints
                    excluded_patterns = ['chunk-metadata', 'chunk', 'metadata', 'analytics', 'tracking', 'pixel', 'beacon']
                    if any(pattern in url_lower for pattern in excluded_patterns):
                        return
                    
                    # Look for actual data API endpoints (including GraphQL)
                    # GraphQL endpoints might contain room data even if URL doesn't say "room"
                    if any(keyword in url_lower for keyword in ['room', 'accommodation', 'rate', 'availability', 'api', 'hotel', 'property', 'booking', 'graphql']):
                        try:
                            # Try to get JSON response
                            content_type = response.headers.get('content-type', '')
                            if 'application/json' in content_type or 'text/json' in content_type:
                                try:
                                    data = await response.json()
                                    # Check if response contains room data
                                    if isinstance(data, (dict, list)):
                                        # Look for room-related keys in the data
                                        data_str = json.dumps(data) if isinstance(data, dict) else str(data)
                                        # More specific room data indicators
                                        room_indicators = ['roomtype', 'room_type', 'roomtypeid', 'roomtypename', 
                                                         'roomname', 'accommodation', 'roomrate', 'roomrateid',
                                                         'roomtypes', 'rooms', 'accommodations']
                                        if any(key in data_str.lower() for key in room_indicators):
                                            room_data_from_api.append(data)
                                            logger.info(f"✓ Intercepted room data from API: {response.url[:80]}...")
                                            # Log a sample of the data structure for debugging
                                            if isinstance(data, dict):
                                                sample_keys = list(data.keys())[:5]
                                                logger.debug(f"  Sample keys: {sample_keys}")
                                except Exception as json_error:
                                    # Not JSON or failed to parse
                                    pass
                        except Exception as e:
                            logger.debug(f"Error intercepting response: {e}")
                            pass
                except Exception as e:
                    logger.debug(f"Error in response handler: {e}")
                    pass
            
            # Set up response listener
            page.on("response", handle_response)
            
            # Set a longer timeout and use 'domcontentloaded' instead of 'networkidle'
            # 'networkidle' can timeout if there are continuous network requests
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
            
            # Wait for initial page load
            await page.wait_for_timeout(2000)
            
            # Scroll to trigger lazy loading and dynamic content
            await self._interact_with_page(page)
            
            # Wait for dynamic content to load after interaction
            await page.wait_for_timeout(3000)
            
            # Try to find and click "Show rooms" or "View rooms" button to trigger room API calls
            show_rooms_selectors = [
                'button:has-text("Show rooms")',
                'button:has-text("View rooms")',
                'button:has-text("See rooms")',
                'button:has-text("View all rooms")',
                'a:has-text("Show rooms")',
                'a:has-text("View rooms")',
                '[data-testid*="room"] button',
                '[data-testid*="show-rooms"]',
                'button[aria-label*="room" i]',
            ]
            
            for selector in show_rooms_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        if is_visible:
                            logger.info(f"Found and clicking room button: {selector}")
                            await button.click()
                            await page.wait_for_timeout(5000)  # Wait for room API calls
                            break
                except:
                    continue
            
            # Scroll to room section to trigger more API calls
            try:
                room_section = await page.query_selector('[data-testid*="room"], [id*="room"], section:has-text("room")')
                if room_section:
                    await room_section.scroll_into_view_if_needed()
                    await page.wait_for_timeout(3000)  # Wait for room data to load
            except:
                pass
            
            # Try to wait for selector if provided, but don't fail if not found
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=5000)
                except:
                    logger.debug(f"Selector {wait_selector} not found, continuing anyway")
                    pass
            
            html = await page.content()
            
            # Store intercepted room data for later use
            if room_data_from_api:
                # Store in page context for retrieval
                if not hasattr(page, 'room_data_from_api'):
                    page.room_data_from_api = []
                page.room_data_from_api.extend(room_data_from_api)
                logger.info(f"✓ Intercepted {len(room_data_from_api)} API responses with potential room data")
            
            await page.close()
            
            if html and len(html) > 1000:  # Basic validation
                # Return HTML and intercepted data
                return html, room_data_from_api if room_data_from_api else []
            else:
                logger.warning(f"Received empty or too short HTML from {clean_url}")
                return None, []
                
        except Exception as e:
            logger.error(f"Error fetching with browser {url}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    async def _interact_with_page(self, page) -> None:
        """Interact with page to trigger dynamic content loading."""
        try:
            # Scroll down gradually to trigger lazy loading
            viewport_height = await page.evaluate('window.innerHeight')
            total_height = await page.evaluate('document.body.scrollHeight')
            
            # Scroll in steps
            scroll_steps = 3
            scroll_distance = total_height // scroll_steps
            
            for i in range(scroll_steps):
                scroll_position = scroll_distance * (i + 1)
                await page.evaluate(f'window.scrollTo(0, {scroll_position})')
                await page.wait_for_timeout(1000)  # Wait after each scroll
            
            # Scroll back to top
            await page.evaluate('window.scrollTo(0, 0)')
            await page.wait_for_timeout(1000)
            
            # Try to find and click "Show rooms" or "View rooms" button
            show_rooms_selectors = [
                'button:has-text("Show rooms")',
                'button:has-text("View rooms")',
                'button:has-text("See rooms")',
                '[data-testid*="room"] button',
                'a:has-text("Show rooms")',
                'a:has-text("View rooms")',
            ]
            
            for selector in show_rooms_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        # Check if button is visible
                        is_visible = await button.is_visible()
                        if is_visible:
                            logger.info(f"Found and clicking room button: {selector}")
                            await button.click()
                            await page.wait_for_timeout(3000)  # Wait for rooms to load
                            break
                except:
                    continue
            
            # Try to find room section and scroll to it
            room_section_selectors = [
                '[data-testid*="room"]',
                '[id*="room"]',
                '[class*="room"]',
                'section:has-text("Room")',
            ]
            
            for selector in room_section_selectors:
                try:
                    room_section = await page.query_selector(selector)
                    if room_section:
                        # Scroll to room section
                        await room_section.scroll_into_view_if_needed()
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue
                    
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
        """Search for hotels on Booking.com."""
        hotels = []
        
        try:
            search_url = f"{self.base_url}/searchresults.html"
            params = {
                'ss': destination,
            }
            
            if check_in:
                params.update({
                    'checkin_month': check_in.month,
                    'checkin_monthday': check_in.day,
                    'checkin_year': check_in.year,
                })
            
            if check_out:
                params.update({
                    'checkout_month': check_out.month,
                    'checkout_monthday': check_out.day,
                    'checkout_year': check_out.year,
                })
            
            # Fetch page
            if self.use_browser:
                result = await self._fetch_with_browser(f"{search_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
                html = result[0] if result else None
            else:
                html = await self.fetch_page(search_url, params)
            
            if not html:
                return hotels
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find hotel listings
            hotel_elements = soup.find_all('div', {'data-testid': 'property-card'})
            
            if not hotel_elements:
                hotel_elements = soup.find_all('div', class_=re.compile(r'property|hotel|sr_item', re.I))
            
            for element in hotel_elements[:25]:
                hotel_data = self._extract_hotel_info(element, destination)
                if hotel_data:
                    hotels.append(hotel_data)
                
                await self.delay(0.5)
            
        except Exception as e:
            logger.error(f"Error scraping Booking.com for {destination}: {e}")
        
        return hotels
    
    def _extract_hotel_info(self, element, destination: str) -> Optional[Dict[str, Any]]:
        """Extract hotel information from search result element."""
        try:
            # Extract hotel name
            name_elem = element.find('a', {'data-testid': 'title-link'})
            if not name_elem:
                name_elem = element.find(['h3', 'a'], class_=re.compile(r'property|hotel|name', re.I))
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            # Extract rating
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
                'source': 'booking.com',
                'stars': stars,
                'amenities': [],
            }
        except Exception as e:
            logger.error(f"Error extracting hotel info: {e}")
            return None
    
    async def get_hotel_details(self, hotel_url: str) -> Optional[Dict[str, Any]]:
        """Get detailed hotel information from hotel detail page.
        
        Args:
            hotel_url: URL of the hotel detail page
            
        Returns:
            Dictionary with detailed hotel information
        """
        if not hotel_url:
            return None
        
        try:
            # Store intercepted API data
            intercepted_room_data = []
            
            # Fetch hotel detail page
            if self.use_browser:
                # Fetch with browser and interact to load dynamic content
                html, api_data = await self._fetch_with_browser_and_intercept(hotel_url, wait_selector=None)
                if api_data:
                    intercepted_room_data = api_data
            else:
                html = await self.fetch_page(hotel_url)
            
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract rooms - try intercepted API data first
            rooms = []
            if intercepted_room_data:
                logger.info(f"Processing {len(intercepted_room_data)} API responses for room extraction")
                for idx, api_response in enumerate(intercepted_room_data, 1):
                    # Log response structure for debugging
                    if isinstance(api_response, dict):
                        top_level_keys = list(api_response.keys())[:10]
                        logger.debug(f"API response {idx} top-level keys: {top_level_keys}")
                    
                    # Handle GraphQL response structure (data key)
                    if isinstance(api_response, dict) and 'data' in api_response:
                        # Extract from GraphQL data structure
                        graphql_data = api_response['data']
                        
                        # Log GraphQL data structure
                        if isinstance(graphql_data, dict):
                            graphql_keys = list(graphql_data.keys())[:10]
                            logger.debug(f"GraphQL data keys in response {idx}: {graphql_keys}")
                        
                        extracted = self._extract_rooms_from_dict(graphql_data, path=f"response_{idx}.data")
                        if extracted:
                            logger.info(f"Extracted {len(extracted)} rooms from API response {idx} (GraphQL data)")
                            rooms.extend(extracted)
                        else:
                            # Also try the whole response
                            extracted = self._extract_rooms_from_dict(api_response, path=f"response_{idx}")
                            if extracted:
                                logger.info(f"Extracted {len(extracted)} rooms from API response {idx} (full structure)")
                                rooms.extend(extracted)
                    else:
                        # Direct extraction
                        extracted = self._extract_rooms_from_dict(api_response, path=f"response_{idx}")
                        if extracted:
                            logger.info(f"Extracted {len(extracted)} rooms from API response {idx}")
                            rooms.extend(extracted)
                
                if rooms:
                    logger.info(f"Total: Extracted {len(rooms)} unique rooms from {len(intercepted_room_data)} API responses")
                else:
                    logger.warning(f"No rooms found in {len(intercepted_room_data)} API responses - may need to inspect response structure")
            
            # If we have some rooms from API but want to find more, also try HTML extraction
            # This helps when API only returns 1 room but HTML has more
            html_rooms = await self._extract_rooms(soup, hotel_url)
            if html_rooms:
                # Merge API rooms with HTML rooms (avoid duplicates)
                existing_room_names = {r['room_type_name'].lower() for r in rooms}
                for html_room in html_rooms:
                    html_room_name = html_room.get('room_type_name', '').lower()
                    if html_room_name and html_room_name not in existing_room_names:
                        rooms.append(html_room)
                        existing_room_names.add(html_room_name)
                        logger.info(f"Added room from HTML: {html_room.get('room_type_name')}")
                
                if len(html_rooms) > len(rooms):
                    logger.info(f"Found {len(html_rooms)} rooms in HTML, merged with {len(rooms)} from API")
            
            # Extract all information
            reviews = self._extract_reviews(soup)
            
            # Extract amenities from multiple sources
            amenities = self._extract_amenities(soup)
            
            # Also extract amenities from reviews
            review_amenities = self._extract_amenities_from_reviews(reviews)
            if review_amenities:
                # Merge amenities from reviews (avoid duplicates)
                existing_amenities_lower = {a.lower() for a in amenities}
                for review_amenity in review_amenities:
                    if review_amenity.lower() not in existing_amenities_lower:
                        amenities.append(review_amenity)
                        existing_amenities_lower.add(review_amenity.lower())
            
            details = {
                'description': self._extract_description(soup),
                'property_overview': self._extract_property_overview(soup),
                'images': self._extract_all_images(soup),
                'amenities': amenities,
                'policies': self._extract_policies(soup),
                'rooms': rooms,
                'reviews': reviews,
                'location_details': self._extract_location_details(soup),
                'hotel_website_url': hotel_website_url,
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting hotel details from {hotel_url}: {e}")
            return None
    
    def _extract_hotel_website(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hotel's official website URL from Booking.com page."""
        try:
            # Strategy 1: Look for official website link in contact section
            contact_section = soup.find('div', {'data-testid': 'contact'})
            if contact_section:
                website_link = contact_section.find('a', href=re.compile(r'http', re.I))
                if website_link:
                    href = website_link.get('href')
                    if href and not 'booking.com' in href.lower():
                        return href
            
            # Strategy 2: Look for website in property details or information section
            details_section = soup.find('div', class_=re.compile(r'property|details|information', re.I))
            if details_section:
                website_link = details_section.find('a', href=re.compile(r'http', re.I))
                if website_link:
                    href = website_link.get('href')
                    if href and not 'booking.com' in href.lower():
                        return href
            
            # Strategy 3: Look for links with "website" or "official" text (case-insensitive)
            website_links = soup.find_all('a', href=True)
            for link in website_links:
                link_text = link.get_text().lower()
                if any(term in link_text for term in ['website', 'official', 'visit', 'homepage', 'www']):
                    href = link.get('href')
                    if href and href.startswith('http') and not 'booking.com' in href.lower():
                        return href
            
            # Strategy 4: Look for external links in contact/info sections
            contact_sections = soup.find_all(['div', 'section'], class_=re.compile(r'contact|info|details', re.I))
            for section in contact_sections:
                links = section.find_all('a', href=re.compile(r'^https?://', re.I))
                for link in links:
                    href = link.get('href')
                    if href:
                        excluded_domains = ['booking.com', 'expedia.com', 'hotels.com', 'agoda.com', 
                                           'tripadvisor.com', 'trivago.com', 'kayak.com', 'priceline.com',
                                           'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com']
                        if not any(domain in href.lower() for domain in excluded_domains):
                            # Check if it looks like a hotel website (not social media)
                            if not any(social in href.lower() for social in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube']):
                                return href
            
            # Strategy 5: Look for any external link that's not a booking site
            all_links = soup.find_all('a', href=re.compile(r'^https?://', re.I))
            for link in all_links:
                href = link.get('href')
                if href:
                    excluded_domains = ['booking.com', 'expedia.com', 'hotels.com', 'agoda.com', 
                                       'tripadvisor.com', 'trivago.com', 'kayak.com', 'priceline.com',
                                       'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
                                       'youtube.com', 'google.com', 'maps.google.com']
                    if not any(domain in href.lower() for domain in excluded_domains):
                        # Check if it's likely a hotel website (contains hotel name or common hotel TLDs)
                        if any(tld in href.lower() for tld in ['.com', '.net', '.org', '.info']):
                            # Avoid social media and common non-hotel sites
                            if not any(social in href.lower() for social in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'pinterest']):
                                return href
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting hotel website: {e}")
            return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract hotel description."""
        try:
            # Try multiple selectors for description
            desc_elem = soup.find('div', {'data-testid': 'property-description'})
            if not desc_elem:
                desc_elem = soup.find('div', class_=re.compile(r'description|property-description', re.I))
            if not desc_elem:
                desc_elem = soup.find('div', id=re.compile(r'description', re.I))
            
            if desc_elem:
                # Get all text, removing script and style tags
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
        except Exception as e:
            logger.error(f"Error extracting property overview: {e}")
            return ""
    
    def _upgrade_image_quality(self, url: str) -> str:
        """Upgrade image URL to higher quality version."""
        try:
            # Booking.com image quality upgrades
            if 'bstatic.com' in url or 'booking.com' in url:
                # Replace size-limited URLs with highest quality
                # max300, max500 -> max1920x1080 (highest quality)
                # max1024x768 -> max1920x1080
                # square240, square64 -> max1920x1080
                url = re.sub(r'/max\d+x?\d*/', '/max1920x1080/', url)
                url = re.sub(r'/square\d+/', '/max1920x1080/', url)
                url = re.sub(r'/max\d+/', '/max1920x1080/', url)
            
            # Expedia image quality upgrades
            elif 'expedia.com' in url or 'media.expedia.com' in url:
                url = re.sub(r'[?&]w=\d+', '?w=1920', url)
                url = re.sub(r'[?&]h=\d+', '&h=1080', url)
                if '?' not in url:
                    url += '?w=1920&h=1080'
                elif 'w=' not in url:
                    url += '&w=1920&h=1080'
            
            # Hotels.com image quality upgrades
            elif 'hotels.com' in url or 'media.hotels.com' in url:
                url = re.sub(r'[?&]size=\w+', '?size=large', url)
                if '?' not in url:
                    url += '?size=large'
                elif 'size=' not in url:
                    url += '&size=large'
            
            # Agoda image quality upgrades
            elif 'agoda.net' in url or 'agoda.com' in url:
                url = re.sub(r'[?&]s=\w+', '?s=1920x1080', url)
                if '?' not in url:
                    url += '?s=1920x1080'
                elif 's=' not in url:
                    url += '&s=1920x1080'
            
            # Remove size parameters from query string if present (for Booking.com)
            # Keep the hash/security parameter but remove size limits
            if 'bstatic.com' in url and '?' in url:
                base_url, query = url.split('?', 1)
                # Keep only the hash parameter (k=...)
                params = query.split('&')
                hash_param = [p for p in params if p.startswith('k=')]
                if hash_param:
                    url = f"{base_url}?{hash_param[0]}"
            
            return url
        except Exception as e:
            logger.debug(f"Error upgrading image quality: {e}")
            return url
    
    def _is_high_quality_image(self, url: str) -> bool:
        """Check if image URL is high quality."""
        try:
            # Filter out low quality images
            low_quality_patterns = [
                r'/max\d{1,3}/',  # max300, max500 (too small)
                r'/square\d{1,3}/',  # square64, square240 (too small)
                r'/max\d{1,3}x\d{1,3}/',  # max300x200 (too small)
                r's96-c',  # Google profile images (96x96)
                r'height=64',  # Facebook profile images (64x64)
                r'width=64',
                r'type=square',
                r'avatar',
                r'profile',
                r'icon',
            ]
            
            for pattern in low_quality_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            # Check for high quality indicators
            high_quality_patterns = [
                r'/max1280x900/',
                r'/max1920x1080/',
                r'/original/',
                r'/large/',
                r'/full/',
                r'/high/',
            ]
            
            for pattern in high_quality_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return True
            
            # If it's a Booking.com image without size limit, it's probably OK
            if 'bstatic.com' in url and not re.search(r'/max\d+/', url):
                return True
            
            return True  # Default to accepting if we can't determine
        except:
            return True
    
    def _extract_all_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract all hotel images with high quality."""
        images = []
        try:
            # Strategy 1: Find image gallery
            gallery = soup.find('div', class_=re.compile(r'gallery|images|photos', re.I))
            if not gallery:
                gallery = soup
            
            # Find all image elements
            img_elements = gallery.find_all('img')
            
            for img in img_elements:
                # Try multiple sources for higher quality images
                src = (img.get('data-high-res-src') or 
                      img.get('data-original') or 
                      img.get('data-full-src') or
                      img.get('data-large-src') or
                      img.get('data-src') or 
                      img.get('src') or 
                      img.get('data-lazy-src'))
                
                if src:
                    # Clean up image URL
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    
                    # Filter out social media profile images and icons
                    if any(skip in src.lower() for skip in [
                        'icon', 'logo', 'avatar', 'placeholder', 
                        'googleusercontent.com/a/',  # Google profile
                        'graph.facebook.com',  # Facebook profile
                        's96-c',  # Google small images
                        'height=64', 'width=64',  # Small images
                        'type=square',  # Square profile images
                    ]):
                        continue
                    
                    # Upgrade image quality
                    src = self._upgrade_image_quality(src)
                    
                    # Only add if it's high quality
                    if self._is_high_quality_image(src):
                        if src not in images:
                            images.append(src)
            
            # Strategy 2: Find images in data attributes (often higher quality)
            for elem in soup.find_all(['div', 'a', 'figure'], {'data-src': True}):
                src = elem.get('data-src') or elem.get('data-high-res-src') or elem.get('data-original')
                if src and src not in images:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    
                    # Filter out low quality
                    if not self._is_high_quality_image(src):
                        continue
                    
                    # Upgrade quality
                    src = self._upgrade_image_quality(src)
                    images.append(src)
            
            # Strategy 3: Look for high-res images in background-image CSS
            for elem in soup.find_all(style=re.compile(r'background-image', re.I)):
                style = elem.get('style', '')
                match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                if match:
                    src = match.group(1)
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    
                    # Filter and upgrade
                    if self._is_high_quality_image(src):
                        src = self._upgrade_image_quality(src)
                        if src not in images:
                            images.append(src)
            
            # Sort by quality (prefer larger images first)
            def quality_score(url):
                if '/max1920x1080/' in url:
                    return 5  # Highest quality
                elif '/max1280x900/' in url:
                    return 4
                elif '/max1024x768/' in url:
                    return 3
                elif '/max500/' in url:
                    return 2
                elif '/max300/' in url:
                    return 1
                # Check for other high quality indicators
                if any(indicator in url.lower() for indicator in ['large', 'original', 'full', 'high']):
                    return 4
                return 2  # Default
            
            images.sort(key=quality_score, reverse=True)
            
            return images[:50]  # Limit to 50 images
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract hotel amenities from multiple sources."""
        amenities = []
        try:
            # Strategy 1: Find amenities section by data-testid (Booking.com specific)
            amenities_section = soup.find('div', {'data-testid': 'facilities'})
            if not amenities_section:
                amenities_section = soup.find('div', {'data-testid': 'facilities-highlights'})
            if not amenities_section:
                amenities_section = soup.find('div', {'data-testid': 'property-highlights'})
            
            # Strategy 2: Find by class name
            if not amenities_section:
                amenities_section = soup.find('div', class_=re.compile(r'amenities|facilities|features', re.I))
            if not amenities_section:
                amenities_section = soup.find('section', class_=re.compile(r'amenities|facilities|features', re.I))
            
            # Strategy 3: Find by ID
            if not amenities_section:
                amenities_section = soup.find('div', id=re.compile(r'amenities|facilities|features', re.I))
            
            if amenities_section:
                # Find all amenity items
                amenity_items = amenities_section.find_all(['li', 'div', 'span', 'p'], class_=re.compile(r'amenity|facility|feature', re.I))
                
                # If no items found by class, try to find all list items or divs
                if not amenity_items:
                    amenity_items = amenities_section.find_all(['li', 'div', 'span'])
                
                for item in amenity_items:
                    text = item.get_text(strip=True)
                    # Filter out long descriptions and empty text
                    if text and len(text) < 100 and len(text) > 2:
                        # Clean up text (remove extra whitespace, newlines)
                        text = ' '.join(text.split())
                        # Skip if it's just a number or single character
                        if not text.isdigit() and len(text) > 2:
                            amenities.append(text)
            
            # Strategy 4: Extract from structured data (JSON-LD)
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Check for amenityFeature
                        if 'amenityFeature' in data:
                            for amenity in data['amenityFeature']:
                                if isinstance(amenity, dict):
                                    if 'name' in amenity:
                                        amenities.append(amenity['name'])
                                    elif '@type' in amenity:
                                        # Sometimes amenities are just types
                                        amenity_type = amenity.get('@type', '').replace('https://schema.org/', '').replace('http://schema.org/', '')
                                        if amenity_type:
                                            amenities.append(amenity_type)
                        
                        # Check for offers/amenities in offers
                        if 'offers' in data:
                            offers = data['offers']
                            if isinstance(offers, list):
                                for offer in offers:
                                    if isinstance(offer, dict) and 'amenityFeature' in offer:
                                        for amenity in offer['amenityFeature']:
                                            if isinstance(amenity, dict) and 'name' in amenity:
                                                amenities.append(amenity['name'])
                except:
                    pass
            
            # Strategy 5: Extract from meta tags or data attributes
            meta_amenities = soup.find_all(['meta', 'div'], attrs={'property': re.compile(r'amenity|facility', re.I)})
            for meta in meta_amenities:
                content = meta.get('content') or meta.get('data-amenity')
                if content:
                    amenities.append(content)
            
            # Strategy 6: Look for common amenity patterns in text
            # This is a fallback - look for common amenities mentioned in descriptions
            common_amenities = ['WiFi', 'Wi-Fi', 'Free WiFi', 'Parking', 'Pool', 'Gym', 'Fitness Center', 
                              'Spa', 'Restaurant', 'Bar', 'Room Service', 'Air Conditioning', 'AC',
                              'Breakfast', 'Pet Friendly', 'Business Center', 'Conference Room',
                              'Laundry', 'Dry Cleaning', 'Concierge', '24-hour Front Desk',
                              'Airport Shuttle', 'Shuttle Service', 'Valet Parking', 'Free Parking']
            
            # Get all text from the page
            page_text = soup.get_text().lower()
            for amenity in common_amenities:
                if amenity.lower() in page_text and amenity not in amenities:
                    # Check if it's actually mentioned (not just part of another word)
                    pattern = r'\b' + re.escape(amenity.lower()) + r'\b'
                    if re.search(pattern, page_text):
                        amenities.append(amenity)
            
            # Strategy 7: Extract from intercepted API data (if available)
            # This will be handled in get_hotel_details method
            
            # Clean and deduplicate amenities
            cleaned_amenities = []
            seen = set()
            for amenity in amenities:
                # Normalize amenity names
                normalized = amenity.strip().title()
                # Skip duplicates (case-insensitive)
                if normalized.lower() not in seen:
                    seen.add(normalized.lower())
                    cleaned_amenities.append(normalized)
            
            logger.info(f"Extracted {len(cleaned_amenities)} amenities from page")
            return cleaned_amenities
            
        except Exception as e:
            logger.error(f"Error extracting amenities: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _extract_policies(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract hotel policies."""
        policies = {}
        try:
            # Find policies section
            policies_section = soup.find('div', class_=re.compile(r'policies|house-rules|check-in-out', re.I))
            
            if policies_section:
                # Extract check-in/check-out times
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
                
                # Extract cancellation policy
                cancellation_elem = policies_section.find(string=re.compile(r'cancellation|cancel', re.I))
                if cancellation_elem:
                    cancellation_text = cancellation_elem.find_next(string=True)
                    if cancellation_text:
                        policies['cancellation'] = cancellation_text.strip()
                
                # Extract pet policy
                pet_elem = policies_section.find(string=re.compile(r'pet|animal', re.I))
                if pet_elem:
                    pet_text = pet_elem.find_next(string=True)
                    if pet_text:
                        policies['pets'] = pet_text.strip()
            
            return policies
            
        except Exception as e:
            logger.error(f"Error extracting policies: {e}")
            return {}
    
    async def _extract_rooms(self, soup: BeautifulSoup, hotel_url: str) -> List[Dict[str, Any]]:
        """Extract room information."""
        rooms = []
        try:
            # First, try extracting from JavaScript data (most reliable)
            rooms = self._extract_rooms_from_json(soup)
            if rooms:
                logger.info(f"Extracted {len(rooms)} rooms from JSON data")
                return rooms
            
            # Try multiple strategies to find rooms in HTML
            # Strategy 1: Look for Booking.com's room type cards (most specific)
            # Try various data-testid patterns
            room_elements = soup.find_all('div', {'data-testid': re.compile(r'room|accommodation', re.I)})
            
            # Strategy 2: Look for room type sections with various IDs
            if not room_elements:
                for testid in ['room-types', 'rooms', 'accommodations', 'room-list']:
                    rooms_section = soup.find('div', {'data-testid': testid})
                    if rooms_section:
                        room_elements = rooms_section.find_all('div', recursive=False)
                        if room_elements:
                            break
            
            # Strategy 3: Look for accommodation cards with specific class patterns
            if not room_elements:
                room_elements = soup.find_all('div', class_=re.compile(r'room-card|accommodation-card|room-type|room-item', re.I))
            
            # Strategy 4: Look for sections with room-related IDs
            if not room_elements:
                room_sections = soup.find_all(['section', 'div'], id=re.compile(r'room|accommodation', re.I))
                for section in room_sections:
                    # Find room cards within the section
                    cards = section.find_all('div', class_=re.compile(r'card|item|type', re.I))
                    if cards:
                        room_elements.extend(cards)
            
            # Strategy 5: Look for any div with room-related classes, but exclude review sections
            if not room_elements:
                all_room_divs = soup.find_all('div', class_=re.compile(r'room|accommodation', re.I))
                # Filter out elements that are clearly not rooms (reviews, ratings, etc.)
                room_elements = []
                for elem in all_room_divs:
                    # Skip if it's in a reviews section
                    if elem.find_parent('div', class_=re.compile(r'review|rating|testimonial', re.I)):
                        continue
                    # Skip if it contains review-related text
                    elem_text = elem.get_text().lower()
                    if 'review' in elem_text or 'rating' in elem_text or 'guest review' in elem_text:
                        continue
                    # Only include if it has a heading or looks like a card
                    if elem.find('h3') or elem.find('h4') or elem.find('h5') or 'card' in elem.get('class', []):
                        room_elements.append(elem)
            
            # Strategy 6: Look for table rows with room data
            if not room_elements:
                room_rows = soup.find_all('tr', class_=re.compile(r'room|accommodation', re.I))
                room_elements = room_rows
            
            # Strategy 7: Look for list items with room data
            if not room_elements:
                room_items = soup.find_all('li', class_=re.compile(r'room|accommodation', re.I))
                room_elements = room_items
            
            # Strategy 8: Look for article or section tags with room data
            if not room_elements:
                room_articles = soup.find_all(['article', 'section'], class_=re.compile(r'room|accommodation', re.I))
                room_elements = room_articles
            
            # Strategy 9: Look for Booking.com's specific room card structure
            if not room_elements:
                # Booking.com uses specific data-testid patterns
                room_cards = soup.find_all('div', {'data-testid': re.compile(r'room|accommodation', re.I)})
                if room_cards:
                    room_elements = room_cards
            
            # Strategy 10: Look for any element with room-related attributes
            if not room_elements:
                # Try to find elements with room-related data attributes
                room_attrs = soup.find_all(attrs={'data-room': True}) or soup.find_all(attrs={'data-room-type': True})
                if room_attrs:
                    room_elements = room_attrs
            
            # Strategy 11: Look for room cards in sections (Booking.com structure)
            if not room_elements:
                # Find sections that might contain rooms
                sections = soup.find_all('section', class_=re.compile(r'room|accommodation', re.I))
                for section in sections:
                    # Find cards or items within the section
                    cards = section.find_all(['div', 'article'], class_=re.compile(r'card|item|type|option', re.I))
                    if cards:
                        room_elements.extend(cards)
            
            # Strategy 12: Look for room options in tabs or accordions
            if not room_elements:
                # Booking.com sometimes uses tabs or accordions for rooms
                tabs = soup.find_all(['div', 'section'], class_=re.compile(r'tab|accordion|panel', re.I))
                for tab in tabs:
                    # Check if tab contains room-related content
                    tab_text = tab.get_text().lower()
                    if any(term in tab_text for term in ['room', 'accommodation', 'suite', 'deluxe', 'standard']):
                        # Find room items within the tab
                        items = tab.find_all(['div', 'li'], class_=re.compile(r'room|accommodation|option', re.I))
                        if items:
                            room_elements.extend(items)
            
            logger.info(f"Found {len(room_elements)} potential room elements")
            
            # Deduplicate room elements (in case multiple strategies found the same element)
            seen_elements = set()
            unique_room_elements = []
            for elem in room_elements:
                elem_id = id(elem)
                if elem_id not in seen_elements:
                    seen_elements.add(elem_id)
                    unique_room_elements.append(elem)
            
            for room_elem in unique_room_elements[:20]:  # Limit to 20 rooms
                room_name = self._extract_room_name(room_elem)
                
                # If no room name found, try to extract from text content
                if not room_name:
                    # Try to get any heading or strong text
                    text_content = room_elem.get_text(strip=True)
                    # Look for first line that looks like a room name
                    lines = text_content.split('\n')
                    for line in lines[:5]:  # Check first 5 lines
                        line = line.strip()
                        if line and len(line) > 5 and len(line) < 100:
                            # Check if it doesn't contain excluded terms
                            excluded = ['review', 'rating', 'amenity', 'facility', 'policy', 'description', 'overview',
                                       'sustainability', 'environment', 'green', 'eco', 'location', 'map', 'directions',
                                       'contact', 'phone', 'email', 'address', 'check-in', 'check-out', 'cancellation',
                                       'terms', 'conditions', 'privacy', 'cookie', 'accessibility', 'access', 'wheelchair',
                                       'guest reviews', 'reviews', 'sustainability', 'environment']
                            # Also check if it looks like a room name (contains room-related words)
                            room_indicators = ['room', 'suite', 'apartment', 'villa', 'studio', 'deluxe', 'standard',
                                             'executive', 'presidential', 'junior', 'superior', 'family', 'double',
                                             'single', 'twin', 'king', 'queen', 'bed', 'accommodation', 'basic',
                                             'comfort', 'economy', 'premium', 'luxury', 'penthouse', 'loft']
                            line_lower = line.lower()
                            # Only accept if it contains room indicators - be strict
                            if not any(term in line_lower for term in excluded):
                                if any(indicator in line_lower for indicator in room_indicators):
                                    room_name = line
                                    break
                
                # Skip if still no valid room name
                if not room_name or len(room_name) < 3:
                    logger.debug(f"Skipping room element - no valid name found. Text preview: {room_elem.get_text(strip=True)[:100]}")
                    continue
                
                room_data = {
                    'room_type_name': room_name,
                    'description': self._extract_room_description(room_elem),
                    'images': self._extract_room_images(room_elem),
                    'occupancy': self._extract_room_occupancy(room_elem),
                    'amenities': self._extract_room_amenities(room_elem),
                }
                
                rooms.append(room_data)
                logger.info(f"Extracted room: {room_data['room_type_name']}")
            
            logger.info(f"Extracted {len(rooms)} rooms total")
            return rooms
            
        except Exception as e:
            logger.error(f"Error extracting rooms: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _extract_room_name(self, room_elem) -> str:
        """Extract room name."""
        try:
            # Try multiple selectors for room name
            name_elem = room_elem.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'room|title|name|heading', re.I))
            if not name_elem:
                name_elem = room_elem.find('div', class_=re.compile(r'room.*name|room.*title', re.I))
            if not name_elem:
                name_elem = room_elem.find('span', class_=re.compile(r'room.*name|room.*title', re.I))
            if not name_elem:
                # Try data-testid
                name_elem = room_elem.find('div', {'data-testid': re.compile(r'room.*name|room.*title', re.I)})
            if not name_elem:
                # Try any heading in the element (but not h1 - those are usually hotel names)
                name_elem = room_elem.find(['h2', 'h3', 'h4', 'h5'])
            if not name_elem:
                # Try strong or b tags
                name_elem = room_elem.find(['strong', 'b'])
            
            if name_elem:
                name = name_elem.get_text(strip=True)
                # Filter out generic text and non-room elements
                excluded_terms = ['room', 'rooms', 'accommodation', 'accommodations', 'guest reviews', 'reviews', 'review', 
                                 'rating', 'ratings', 'amenities', 'facilities', 'policies', 'policy', 'location', 
                                 'map', 'photos', 'images', 'gallery', 'description', 'overview', 'sustainability',
                                 'environment', 'green', 'eco', 'contact', 'phone', 'email', 'address', 'directions',
                                 'check-in', 'check-out', 'cancellation', 'terms', 'conditions', 'privacy', 'cookie',
                                 'accessibility', 'access', 'wheelchair', 'parking', 'transportation', 'airport']
                
                # Also exclude hotel names and non-room elements
                name_lower = name.lower().strip()
                
                # Filter out excluded terms
                if any(term in name_lower for term in excluded_terms):
                    return ""
                
                # Filter out common non-room elements
                non_room_patterns = ['guest reviews', 'reviews', 'sustainability', 'environment', 'green', 
                                   'eco', 'location', 'map', 'directions', 'contact', 'phone', 'email',
                                   'check-in', 'check-out', 'cancellation', 'terms', 'conditions', 'privacy',
                                   'cookie', 'accessibility', 'access', 'wheelchair', 'parking', 'transportation',
                                   'airport', 'amenities', 'facilities', 'policies', 'description', 'overview']
                if any(pattern in name_lower for pattern in non_room_patterns):
                    return ""
                
                # Check if it looks like a hotel name (too long, contains location info)
                if len(name) > 50:
                    return ''
                
                # Check for common hotel name patterns
                hotel_name_patterns = ['hotel', 'inn', 'resort', 'lodge', 'by ', 'times square', 'manhattan', 'new york']
                if any(pattern in name_lower for pattern in hotel_name_patterns) and len(name) > 30:
                    return ''
                
                # Also check if it contains room indicators (preferred)
                room_indicators = ['room', 'suite', 'apartment', 'villa', 'studio', 'deluxe', 'standard',
                                 'executive', 'presidential', 'junior', 'superior', 'family', 'double',
                                 'single', 'twin', 'king', 'queen', 'bed', 'accommodation', 'basic',
                                 'comfort', 'economy', 'premium', 'luxury', 'penthouse', 'loft', 'view',
                                 'ocean', 'city', 'garden', 'pool', 'terrace', 'balcony']
                
                # If it doesn't contain room indicators, be more cautious
                if not any(indicator in name_lower for indicator in room_indicators):
                    # Only accept if it's a very short name (likely a room type abbreviation)
                    if len(name) > 20:  # Longer names without room indicators are likely not rooms
                        return ""
                
                # Final validation: must be between 3 and 50 characters
                if 3 <= len(name) <= 50:
                    return name
            
            return ""
        except Exception as e:
            logger.debug(f"Error extracting room name: {e}")
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
        """Extract room images with high quality."""
        images = []
        try:
            img_elements = room_elem.find_all('img')
            for img in img_elements:
                # Try multiple sources for higher quality
                src = (img.get('data-high-res-src') or 
                      img.get('data-original') or 
                      img.get('data-full-src') or
                      img.get('data-large-src') or
                      img.get('data-src') or 
                      img.get('src'))
                
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    
                    # Filter out low quality
                    if not self._is_high_quality_image(src):
                        continue
                    
                    # Upgrade quality
                    src = self._upgrade_image_quality(src)
                    
                    if src not in images:
                        images.append(src)
            return images[:10]  # Limit to 10 images per room
        except:
            return []
    
    def _extract_room_occupancy(self, room_elem) -> Dict[str, Any]:
        """Extract room occupancy details."""
        occupancy = {}
        try:
            # Extract size
            size_elem = room_elem.find(string=re.compile(r'(\d+)\s*(sqm|sq\s*ft|m²)', re.I))
            if size_elem:
                size_match = re.search(r'(\d+)', size_elem)
                if size_match:
                    occupancy['size'] = int(size_match.group(1))
            
            # Extract max guests
            guests_elem = room_elem.find(string=re.compile(r'(\d+)\s*(guest|person|people)', re.I))
            if guests_elem:
                guests_match = re.search(r'(\d+)', guests_elem)
                if guests_match:
                    occupancy['max_guests'] = int(guests_match.group(1))
            
            # Extract bed type
            bed_elem = room_elem.find(string=re.compile(r'bed|sleep', re.I))
            if bed_elem:
                bed_text = bed_elem.find_next(string=True)
                if bed_text:
                    occupancy['bed_type'] = bed_text.strip()
            
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
    
    def _extract_rooms_from_json(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract rooms from JSON-LD or JavaScript data."""
        rooms = []
        try:
            # Look for JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Check for room data in structured data
                        if 'offers' in data and isinstance(data['offers'], list):
                            for offer in data['offers']:
                                if isinstance(offer, dict) and 'itemOffered' in offer:
                                    room_info = offer['itemOffered']
                                    if isinstance(room_info, dict):
                                        room_name = room_info.get('name', '')
                                        if room_name and 'review' not in room_name.lower():
                                            rooms.append({
                                                'room_type_name': room_name,
                                                'description': room_info.get('description', ''),
                                                'images': room_info.get('image', []) if isinstance(room_info.get('image'), list) else [],
                                                'occupancy': {},
                                                'amenities': [],
                                            })
                except:
                    continue
            
            # Also look for JavaScript variables with room data
            all_scripts = soup.find_all('script')
            for script in all_scripts:
                if not script.string:
                    continue
                script_text = script.string
                
                # Look for common patterns like window.__INITIAL_STATE__ or similar
                # This is a simplified approach - Booking.com might use different patterns
                try:
                    # Try to find JSON objects in the script
                    # Look for patterns like: "roomTypes": [...] or "accommodations": [...]
                    if 'roomType' in script_text.lower() or 'accommodation' in script_text.lower() or 'room' in script_text.lower():
                        # Try to extract JSON arrays containing room data
                        import re
                        # Look for arrays like: "roomTypes": [{...}, {...}]
                        array_pattern = r'(?:roomTypes|accommodations|rooms)\s*:\s*\[([^\]]+)\]'
                        array_matches = re.findall(array_pattern, script_text, re.IGNORECASE | re.DOTALL)
                        
                        for array_content in array_matches:
                            # Try to find individual room objects
                            room_obj_pattern = r'\{[^{}]*"(?:name|roomTypeName|title)"\s*:\s*"([^"]+)"[^{}]*\}'
                            room_matches = re.findall(room_obj_pattern, array_content, re.IGNORECASE)
                            
                            for room_name in room_matches:
                                if room_name and 'review' not in room_name.lower() and len(room_name) > 3:
                                    rooms.append({
                                        'room_type_name': room_name.strip(),
                                        'description': '',
                                        'images': [],
                                        'occupancy': {},
                                        'amenities': [],
                                    })
                        
                        # Also try to find individual JSON objects
                        json_obj_pattern = r'\{"name"\s*:\s*"([^"]+)"[^}]*"room|accommodation[^}]*\}'
                        obj_matches = re.findall(json_obj_pattern, script_text, re.IGNORECASE)
                        
                        for room_name in obj_matches:
                            if room_name and 'review' not in room_name.lower() and len(room_name) > 3:
                                # Check if we already have this room
                                if not any(r['room_type_name'].lower() == room_name.lower() for r in rooms):
                                    rooms.append({
                                        'room_type_name': room_name.strip(),
                                        'description': '',
                                        'images': [],
                                        'occupancy': {},
                                        'amenities': [],
                                    })
                except Exception as e:
                    logger.debug(f"Error parsing JavaScript for rooms: {e}")
                    continue
            
            return rooms
        except Exception as e:
            logger.debug(f"Error extracting rooms from JSON: {e}")
            return []
    
    def _extract_rooms_from_dict(self, data: Any, depth: int = 0, path: str = "") -> List[Dict[str, Any]]:
        """Recursively extract room data from nested dictionaries."""
        rooms = []
        if depth > 20:  # Increased recursion depth for deep API responses
            return rooms
        
        try:
            if isinstance(data, dict):
                # Check if this dict looks like room data
                keys_lower = str(data.keys()).lower()
                
                # More comprehensive room-related key detection
                room_keys = ['room', 'accommodation', 'roomtype', 'room_type', 'roomtypeid', 'roomtypename', 
                           'roomname', 'room_name', 'roomtype_name', 'rate', 'rates', 'roomrate', 
                           'room_rate', 'roomrateid', 'roomtypeid', 'roomtypename']
                
                # Check for room arrays first (most common in Booking.com API)
                # Try multiple possible keys for room arrays
                room_list = None
                room_list_keys = ['rooms', 'roomTypes', 'accommodations', 'roomTypesList', 'room_types', 
                                'roomList', 'accommodationList', 'roomOptions', 'availableRooms', 
                                'roomOptionsList', 'roomCategories', 'roomCategoriesList', 'roomTypesList',
                                'data', 'results', 'items', 'nodes', 'edges', 'roomTypeOptions',
                                'availableRoomTypes', 'roomTypeOptionsList', 'accommodationTypes']
                
                for key in room_list_keys:
                    if key in data:
                        val = data[key]
                        if isinstance(val, list) and len(val) > 0:
                            # Check if list contains room-like objects
                            if len(val) > 0 and isinstance(val[0], dict):
                                # Check if first item looks like a room
                                first_item = val[0]
                                first_keys = str(first_item.keys()).lower()
                                if any(room_key in first_keys for room_key in ['room', 'accommodation', 'name', 'title', 'roomtype']):
                                    room_list = val
                                    logger.info(f"Found room array at path {path}.{key} with {len(val)} items")
                                    break
                        elif isinstance(val, dict):
                            # Check if dict contains a list
                            for sub_key in ['items', 'results', 'data', 'nodes', 'edges', 'roomTypes', 'rooms', 'accommodations']:
                                if sub_key in val and isinstance(val[sub_key], list) and len(val[sub_key]) > 0:
                                    # Verify it's a room list
                                    if isinstance(val[sub_key][0], dict):
                                        first_keys = str(val[sub_key][0].keys()).lower()
                                        if any(room_key in first_keys for room_key in ['room', 'accommodation', 'name', 'title', 'roomtype']):
                                            room_list = val[sub_key]
                                            logger.info(f"Found room array at path {path}.{key}.{sub_key} with {len(room_list)} items")
                                            break
                            if room_list:
                                break
                
                if room_list and isinstance(room_list, list):
                    logger.info(f"Processing {len(room_list)} room items from API response")
                    for idx, room_item in enumerate(room_list):
                            if isinstance(room_item, dict):
                                room_name = (room_item.get('name') or room_item.get('roomTypeName') 
                                           or room_item.get('title') or room_item.get('roomName')
                                           or room_item.get('room_type_name') or room_item.get('roomtypename')
                                           or room_item.get('displayName') or room_item.get('display_name'))
                                if room_name and isinstance(room_name, str) and len(room_name) > 3:
                                    room_name_lower = room_name.lower()
                                    # Filter out non-room elements
                                    if 'review' not in room_name_lower and 'rating' not in room_name_lower:
                                        # Extract images - try multiple strategies
                                        images = self._extract_images_from_room_data(room_item)
                                        
                                        # Extract description
                                        description = (room_item.get('description', '') 
                                                     or room_item.get('roomDescription', '')
                                                     or room_item.get('details', '')
                                                     or room_item.get('summary', '')
                                                     or room_item.get('overview', ''))
                                        
                                        # Extract occupancy
                                        occupancy = (room_item.get('occupancy', {}) 
                                                   or room_item.get('roomOccupancy', {})
                                                   or room_item.get('capacity', {})
                                                   or room_item.get('guestCapacity', {}))
                                        
                                        # Extract amenities
                                        amenities = []
                                        if room_item.get('amenities'):
                                            if isinstance(room_item['amenities'], list):
                                                amenities = room_item['amenities']
                                            elif isinstance(room_item['amenities'], dict):
                                                # Try to extract from dict
                                                amenities = list(room_item['amenities'].values()) if room_item['amenities'] else []
                                        elif room_item.get('roomAmenities'):
                                            if isinstance(room_item['roomAmenities'], list):
                                                amenities = room_item['roomAmenities']
                                        
                                        rooms.append({
                                            'room_type_name': room_name,
                                            'description': description,
                                            'images': images[:10],  # Limit to 10 images per room
                                            'occupancy': occupancy,
                                            'amenities': amenities,
                                        })
                                        logger.info(f"Extracted room {idx+1}: {room_name} ({len(images)} images)")
                
                # Check if this dict itself is a room
                if any(key in keys_lower for key in room_keys):
                    room_name = (data.get('name') or data.get('roomTypeName') or data.get('room_type_name') 
                               or data.get('title') or data.get('roomName') or data.get('room_name')
                               or data.get('displayName') or data.get('display_name'))
                    
                    if room_name and isinstance(room_name, str) and len(room_name) > 3:
                        room_name_lower = room_name.lower()
                        # Filter out non-room elements
                        if 'review' not in room_name_lower and 'rating' not in room_name_lower:
                            # Extract images
                            images = []
                            if data.get('images'):
                                if isinstance(data['images'], list):
                                    images = data['images']
                                elif isinstance(data['images'], dict):
                                    for img_key in ['url', 'src', 'imageUrl', 'image_url']:
                                        if img_key in data['images']:
                                            img_val = data['images'][img_key]
                                            if isinstance(img_val, str):
                                                images.append(img_val)
                                            elif isinstance(img_val, list):
                                                images.extend([img for img in img_val if isinstance(img, str)])
                            
                            # Check if we already have this room (avoid duplicates)
                            if not any(r['room_type_name'].lower() == room_name.lower() for r in rooms):
                                rooms.append({
                                    'room_type_name': room_name,
                                    'description': (data.get('description', '') 
                                                  or data.get('roomDescription', '')
                                                  or data.get('details', '')),
                                    'images': images[:10],
                                    'occupancy': (data.get('occupancy', {}) 
                                                or data.get('roomOccupancy', {})
                                                or data.get('capacity', {})),
                                    'amenities': (data.get('amenities', []) 
                                                if isinstance(data.get('amenities'), list) 
                                                else data.get('roomAmenities', []) 
                                                if isinstance(data.get('roomAmenities'), list) 
                                                else []),
                                })
                                logger.debug(f"Extracted room from API data: {room_name} ({len(images)} images)")
                
                # Recursively search nested dicts (but skip if we already found rooms in arrays)
                # Always recurse if we haven't found rooms yet, or if depth is shallow
                if not rooms or depth < 8:  # Recurse deeper to find rooms
                    for key, value in data.items():
                        # Skip certain keys that are unlikely to contain room data
                        skip_keys = ['metadata', 'pagination', 'filters', 'sort', 'analytics', 'tracking', 
                                   'errors', 'extensions', '__typename', 'clientMutationId', 'cost',
                                   'currency', 'price', 'pricing', 'availability', 'dates', 'calendar']
                        if key.lower() not in [k.lower() for k in skip_keys]:
                            new_path = f"{path}.{key}" if path else key
                            # Only recurse if we haven't found many rooms yet or depth is shallow
                            if not rooms or depth < 5:
                                extracted = self._extract_rooms_from_dict(value, depth + 1, new_path)
                                if extracted:
                                    logger.debug(f"Found {len(extracted)} rooms at path {new_path}")
                                rooms.extend(extracted)
            
            elif isinstance(data, list):
                # Recursively search list items
                for idx, item in enumerate(data):
                    new_path = f"{path}[{idx}]" if path else f"[{idx}]"
                    rooms.extend(self._extract_rooms_from_dict(item, depth + 1, new_path))
        
        except Exception as e:
            logger.debug(f"Error extracting rooms from dict: {e}")
            pass
        
        # Deduplicate rooms by name
        seen_names = set()
        unique_rooms = []
        for room in rooms:
            room_name_lower = room.get('room_type_name', '').lower()
            if room_name_lower and room_name_lower not in seen_names:
                seen_names.add(room_name_lower)
                unique_rooms.append(room)
        
        return unique_rooms
    
    def _extract_images_from_room_data(self, room_item: Dict[str, Any]) -> List[str]:
        """Extract images from room data structure."""
        images = []
        try:
            # Strategy 1: Direct images array
            if room_item.get('images'):
                if isinstance(room_item['images'], list):
                    for img in room_item['images']:
                        if isinstance(img, str):
                            images.append(img)
                        elif isinstance(img, dict):
                            img_url = img.get('url') or img.get('src') or img.get('imageUrl') or img.get('thumbnail')
                            if img_url:
                                images.append(img_url)
                elif isinstance(room_item['images'], dict):
                    # Try to find image URLs in nested structure
                    for img_key in ['url', 'src', 'imageUrl', 'image_url', 'thumbnail', 'original', 'large', 'medium']:
                        if img_key in room_item['images']:
                            img_val = room_item['images'][img_key]
                            if isinstance(img_val, str):
                                images.append(img_val)
                            elif isinstance(img_val, list):
                                images.extend([img for img in img_val if isinstance(img, str)])
            
            # Strategy 2: Media array
            if not images and 'media' in room_item:
                media = room_item['media']
                if isinstance(media, list):
                    for media_item in media:
                        if isinstance(media_item, dict):
                            img_url = (media_item.get('url') or media_item.get('src') 
                                      or media_item.get('imageUrl') or media_item.get('thumbnail')
                                      or media_item.get('original') or media_item.get('large'))
                            if img_url:
                                images.append(img_url)
                        elif isinstance(media_item, str):
                            images.append(media_item)
            
            # Strategy 3: Photos array
            if not images and 'photos' in room_item:
                photos = room_item['photos']
                if isinstance(photos, list):
                    for photo in photos:
                        if isinstance(photo, dict):
                            img_url = photo.get('url') or photo.get('src') or photo.get('imageUrl')
                            if img_url:
                                images.append(img_url)
                        elif isinstance(photo, str):
                            images.append(photo)
            
            # Strategy 4: Image object
            if not images and 'image' in room_item:
                image = room_item['image']
                if isinstance(image, str):
                    images.append(image)
                elif isinstance(image, dict):
                    img_url = image.get('url') or image.get('src') or image.get('imageUrl')
                    if img_url:
                        images.append(img_url)
            
            # Strategy 5: Thumbnail
            if not images and 'thumbnail' in room_item:
                thumbnail = room_item['thumbnail']
                if isinstance(thumbnail, str):
                    images.append(thumbnail)
                elif isinstance(thumbnail, dict):
                    img_url = thumbnail.get('url') or thumbnail.get('src')
                    if img_url:
                        images.append(img_url)
            
            # Clean and validate URLs
            cleaned_images = []
            for img in images:
                if isinstance(img, str) and img.startswith(('http://', 'https://')):
                    cleaned_images.append(img)
            
            return cleaned_images
        except Exception as e:
            logger.debug(f"Error extracting images from room data: {e}")
            return []
    
    def _extract_amenities_from_reviews(self, reviews: List[Dict[str, Any]]) -> List[str]:
        """Extract amenities mentioned in reviews."""
        amenities = []
        try:
            # Common amenities to look for in review text
            common_amenities = {
                'wifi': ['wifi', 'wi-fi', 'wireless', 'internet', 'free wifi'],
                'parking': ['parking', 'valet', 'garage', 'car park'],
                'pool': ['pool', 'swimming pool', 'outdoor pool', 'indoor pool'],
                'gym': ['gym', 'fitness', 'fitness center', 'workout', 'exercise'],
                'spa': ['spa', 'massage', 'sauna', 'steam room'],
                'restaurant': ['restaurant', 'dining', 'breakfast', 'buffet'],
                'bar': ['bar', 'lounge', 'cocktail'],
                'room service': ['room service', 'in-room dining'],
                'air conditioning': ['air conditioning', 'ac', 'climate control'],
                'breakfast': ['breakfast', 'continental breakfast', 'buffet breakfast'],
                'pet friendly': ['pet friendly', 'pets allowed', 'dog friendly'],
                'business center': ['business center', 'business facilities', 'meeting room'],
                'concierge': ['concierge', 'front desk', 'reception'],
                'laundry': ['laundry', 'dry cleaning', 'washing machine'],
                'shuttle': ['shuttle', 'airport shuttle', 'transportation'],
                'safe': ['safe', 'safe deposit box'],
                'minibar': ['minibar', 'mini bar', 'refrigerator'],
                'balcony': ['balcony', 'terrace', 'patio'],
                'kitchen': ['kitchen', 'kitchenette', 'cooking facilities'],
                'jacuzzi': ['jacuzzi', 'hot tub', 'whirlpool'],
            }
            
            # Extract text from all reviews
            review_texts = []
            for review in reviews:
                text = review.get('text', '') or review.get('title', '')
                if text:
                    review_texts.append(text.lower())
            
            # Combine all review text
            all_review_text = ' '.join(review_texts)
            
            # Look for amenities in review text
            found_amenities = set()
            for amenity_name, keywords in common_amenities.items():
                for keyword in keywords:
                    # Use word boundary to avoid partial matches
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    if re.search(pattern, all_review_text, re.IGNORECASE):
                        found_amenities.add(amenity_name.title())
                        break  # Found this amenity, move to next
            
            amenities = list(found_amenities)
            if amenities:
                logger.info(f"Extracted {len(amenities)} amenities from reviews")
            
            return amenities
        except Exception as e:
            logger.debug(f"Error extracting amenities from reviews: {e}")
            return []
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract hotel reviews from Booking.com."""
        reviews = []
        try:
            # Try multiple selectors for Booking.com reviews
            # Booking.com uses various structures for reviews
            review_elements = []
            
            # Method 1: Look for review items with data-testid
            review_elements = soup.find_all('div', {'data-testid': re.compile(r'review|comment', re.I)})
            
            # Method 2: Look for review items in reviews section
            if not review_elements:
                reviews_section = soup.find('div', {'data-testid': 'reviews'})
                if reviews_section:
                    review_elements = reviews_section.find_all('div', class_=re.compile(r'review|comment|item', re.I))
            
            # Method 3: Look for review cards
            if not review_elements:
                review_elements = soup.find_all('div', class_=re.compile(r'review.*card|comment.*card|review-item', re.I))
            
            # Method 4: Look for any div with review-related classes
            if not review_elements:
                review_elements = soup.find_all('div', class_=re.compile(r'review|testimonial|comment', re.I))
                # Filter out parent containers
                review_elements = [e for e in review_elements if e.find('div', class_=re.compile(r'text|content|comment', re.I))]
            
            logger.debug(f"Found {len(review_elements)} potential review elements")
            
            for review_elem in review_elements[:30]:  # Limit to 30 reviews
                review_data = {
                    'title': self._extract_review_title(review_elem),
                    'text': self._extract_review_text(review_elem),
                    'author': self._extract_review_author(review_elem),
                    'rating': self._extract_review_rating(review_elem),
                    'pros': self._extract_review_pros(review_elem),
                    'cons': self._extract_review_cons(review_elem),
                    'category_ratings': self._extract_review_category_ratings(review_elem),
                }
                
                # Only add if we have meaningful content
                if review_data['text'] and len(review_data['text'].strip()) > 20:
                    reviews.append(review_data)
                elif review_data['title'] and len(review_data['title'].strip()) > 5:
                    reviews.append(review_data)
            
            logger.info(f"Extracted {len(reviews)} reviews")
            return reviews
            
        except Exception as e:
            logger.error(f"Error extracting reviews: {e}")
            import traceback
            logger.debug(traceback.format_exc())
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
            # Try multiple selectors for review text
            text_elem = None
            
            # Method 1: data-testid="review-text" or similar
            text_elem = review_elem.find('div', {'data-testid': re.compile(r'text|content|comment|review', re.I)})
            
            # Method 2: class with text/content/comment
            if not text_elem:
                text_elem = review_elem.find('div', class_=re.compile(r'review.*text|comment.*text|content|text.*review', re.I))
            
            # Method 3: paragraph or div with review content
            if not text_elem:
                text_elem = review_elem.find(['p', 'div'], class_=re.compile(r'text|content|comment|description', re.I))
            
            # Method 4: Any paragraph or div with substantial text
            if not text_elem:
                for elem in review_elem.find_all(['p', 'div']):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 20:  # Substantial text
                        text_elem = elem
                        break
            
            if text_elem:
                text = text_elem.get_text(separator=' ', strip=True)
                # Clean up text
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                return text
            return ""
        except Exception as e:
            logger.debug(f"Error extracting review text: {e}")
            return ""
    
    def _extract_review_author(self, review_elem) -> str:
        """Extract review author."""
        try:
            # Try multiple methods to find author
            author_elem = None
            
            # Method 1: data-testid="review-author" or similar
            author_elem = review_elem.find(['span', 'div'], {'data-testid': re.compile(r'author|name|user', re.I)})
            
            # Method 2: class with author/name/user
            if not author_elem:
                author_elem = review_elem.find(['span', 'div', 'p'], class_=re.compile(r'author|name|user|reviewer', re.I))
            
            # Method 3: Look for name-like patterns
            if not author_elem:
                for elem in review_elem.find_all(['span', 'div']):
                    text = elem.get_text(strip=True)
                    # Check if it looks like a name (short, capitalized words)
                    if text and len(text) < 50 and re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text):
                        author_elem = elem
                        break
            
            if author_elem:
                author = author_elem.get_text(strip=True)
                # Clean up author name
                author = re.sub(r'\s+', ' ', author)
                return author
            return "Anonymous"
        except Exception as e:
            logger.debug(f"Error extracting review author: {e}")
            return "Anonymous"
    
    def _extract_review_rating(self, review_elem) -> float:
        """Extract review rating."""
        try:
            # Try multiple methods to find rating
            rating = None
            
            # Method 1: Look for rating in data attributes
            rating_attr = review_elem.get('data-rating') or review_elem.get('data-score')
            if rating_attr:
                try:
                    return float(rating_attr)
                except:
                    pass
            
            # Method 2: Look for rating element with class
            rating_elem = review_elem.find(['div', 'span'], class_=re.compile(r'rating|score|badge', re.I))
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Look for number (could be 1-10 or 1-5 scale)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
                    # Normalize to 1-10 scale if it's 1-5
                    if rating <= 5:
                        rating = rating * 2
                    return rating
            
            # Method 3: Look for star ratings
            stars = review_elem.find_all(['span', 'div'], class_=re.compile(r'star|filled', re.I))
            if stars:
                return len(stars) * 2.0  # Convert stars to 1-10 scale
            
            # Method 4: Look for any number that could be a rating
            all_text = review_elem.get_text()
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|/|stars?)', all_text, re.I)
            if rating_match:
                rating = float(rating_match.group(1))
                if rating <= 5:
                    rating = rating * 2
                return rating
            
            return 0.0
        except Exception as e:
            logger.debug(f"Error extracting review rating: {e}")
            return 0.0
    
    def _extract_review_pros(self, review_elem) -> List[str]:
        """Extract review pros."""
        pros = []
        try:
            pros_section = review_elem.find('div', class_=re.compile(r'pro|positive|good', re.I))
            if pros_section:
                pros_items = pros_section.find_all('li')
                for item in pros_items:
                    text = item.get_text(strip=True)
                    if text:
                        pros.append(text)
            return pros
        except:
            return []
    
    def _extract_review_cons(self, review_elem) -> List[str]:
        """Extract review cons."""
        cons = []
        try:
            cons_section = review_elem.find('div', class_=re.compile(r'con|negative|bad', re.I))
            if cons_section:
                cons_items = cons_section.find_all('li')
                for item in cons_items:
                    text = item.get_text(strip=True)
                    if text:
                        cons.append(text)
            return cons
        except:
            return []
    
    def _extract_review_category_ratings(self, review_elem) -> Dict[str, float]:
        """Extract review category ratings."""
        category_ratings = {}
        try:
            categories = review_elem.find_all('div', class_=re.compile(r'category|rating', re.I))
            for cat_elem in categories:
                cat_name = cat_elem.find('span', class_=re.compile(r'name|label', re.I))
                cat_rating = cat_elem.find('span', class_=re.compile(r'score|rating', re.I))
                
                if cat_name and cat_rating:
                    name = cat_name.get_text(strip=True).lower()
                    rating_text = cat_rating.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        category_ratings[name] = float(rating_match.group(1))
            
            return category_ratings
        except:
            return {}
    
    def _extract_location_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract location details."""
        location = {}
        try:
            # Extract nearby attractions
            attractions_section = soup.find('div', class_=re.compile(r'attractions|nearby|location', re.I))
            if attractions_section:
                attractions = []
                attraction_items = attractions_section.find_all('li')
                for item in attraction_items:
                    text = item.get_text(strip=True)
                    if text:
                        attractions.append(text)
                location['nearby_attractions'] = attractions
            
            return location
        except:
            return {}

