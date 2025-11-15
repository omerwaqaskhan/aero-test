"""Data collector service for aggregating hotel data from multiple sources."""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import asyncio
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..infrastructure.db.models import HotelModel, RoomModel, OfferModel, ReviewModel
from ..domain.models import Hotel, Provider
from .tripadvisor_scraper import TripAdvisorScraper
from .booking_scraper import BookingScraper
from .enhanced_booking_scraper import EnhancedBookingScraper
from .expedia_scraper import ExpediaScraper
from .hotels_com_scraper import HotelsComScraper
from .agoda_scraper import AgodaScraper
from .geocoding import GeocodingService
from .concurrent_scraper import ConcurrentScraper
from .monitoring import get_monitor
from .alerting import get_alert_manager, AlertSeverity
from .config import (
    SCRAPER_RATE_LIMIT,
    SCRAPER_MAX_CONCURRENT,
    SCRAPER_PROXIES,
    SCRAPER_MAX_RETRIES,
    SCRAPER_TIMEOUT
)

logger = logging.getLogger(__name__)


class HotelDataCollector:
    """Service for collecting and storing hotel data from web scrapers."""
    
    def __init__(
        self,
        db_session: Session,
        use_enhanced_scraping: bool = True,
        max_concurrent: Optional[int] = None,
        rate_limit: Optional[float] = None,
        proxies: Optional[List[str]] = None
    ):
        """Initialize data collector with database session.
        
        Args:
            db_session: Database session
            use_enhanced_scraping: Whether to use enhanced scrapers with browser support
            max_concurrent: Maximum concurrent scraping tasks (defaults to config)
            rate_limit: Requests per second per scraper (defaults to config)
            proxies: List of proxy URLs for scraping (defaults to config)
        """
        self.db_session = db_session
        self.use_enhanced_scraping = use_enhanced_scraping
        self.max_concurrent = max_concurrent or SCRAPER_MAX_CONCURRENT
        self.rate_limit = rate_limit or SCRAPER_RATE_LIMIT
        self.proxies = proxies or SCRAPER_PROXIES
        
        # Initialize concurrent scraper for parallel processing
        self.concurrent_scraper = ConcurrentScraper(
            max_workers=self.max_concurrent,
            queue_size=200,
            timeout=300.0
        )
        
        # Initialize proxy pool if proxies are configured
        if self.proxies:
            from .proxy_pool import ProxyPool
            self.proxy_pool = ProxyPool(proxies=self.proxies)
            logger.info(f"Initialized proxy pool with {len(self.proxies)} proxies")
        else:
            self.proxy_pool = None
            logger.info("No proxies configured, using direct connections")
        
        # Use enhanced scrapers if available - multiple providers for better coverage
        if use_enhanced_scraping:
            try:
                self.scrapers = [
                    EnhancedBookingScraper(use_browser=True),
                    ExpediaScraper(use_browser=True),
                    HotelsComScraper(use_browser=True),
                    AgodaScraper(use_browser=True),
                    TripAdvisorScraper(),
                ]
                logger.info(f"Initialized {len(self.scrapers)} scrapers: {[s.__class__.__name__ for s in self.scrapers]}")
            except Exception as e:
                logger.warning(f"Enhanced scrapers not available: {e}. Falling back to basic scrapers.")
                self.scrapers = [
                    BookingScraper(),
                    TripAdvisorScraper(),
                ]
                self.use_enhanced_scraping = False
        else:
            self.scrapers = [
                BookingScraper(),
                TripAdvisorScraper(),
            ]
        
        self.geocoding = GeocodingService()
        
        # Initialize monitoring and alerting
        self.monitor = get_monitor()
        self.alert_manager = get_alert_manager()
    
    async def start(self):
        """Start the concurrent scraper and proxy pool health monitoring."""
        await self.concurrent_scraper.start()
        
        # Start proxy pool health monitoring if configured
        if self.proxy_pool:
            asyncio.create_task(self.proxy_pool.start_health_monitoring())
            logger.info("Proxy pool health monitoring started")
    
    async def stop(self):
        """Stop the concurrent scraper and proxy pool health monitoring."""
        await self.concurrent_scraper.stop()
        
        # Stop proxy pool health monitoring if configured
        if self.proxy_pool:
            await self.proxy_pool.stop_health_monitoring()
            logger.info("Proxy pool health monitoring stopped")
    
    async def collect_hotels_for_destination(
        self,
        destination: str,
        country: Optional[str] = None,
        max_hotels: int = 50
    ) -> int:
        """Collect hotels for a specific destination.
        
        Args:
            destination: City or location name
            country: Country name (optional)
            max_hotels: Maximum number of hotels to collect
            
        Returns:
            Number of hotels collected
        """
        collected_count = 0
        
        try:
            # Collect from all scrapers concurrently
            all_hotels = []
            
            # Create tasks for concurrent scraping
            async def scrape_with_provider(scraper, dest):
                """Scrape hotels from a single provider."""
                scraper_name = scraper.__class__.__name__
                start_time = asyncio.get_event_loop().time()
                
                try:
                    self.monitor.record_metric(scraper_name, 'request')
                    
                    async with scraper:
                        hotels = await scraper.search_hotels(destination=dest)
                        
                        response_time = asyncio.get_event_loop().time() - start_time
                        
                        if hotels:
                            self.monitor.record_metric(
                                scraper_name,
                                'success',
                                value=len(hotels),
                                metadata={'response_time': response_time}
                            )
                            logger.info(f"✓ Collected {len(hotels)} hotels from {scraper_name} for {dest}")
                        else:
                            self.monitor.record_metric(
                                scraper_name,
                                'failure',
                                metadata={'error_type': 'no_results', 'response_time': response_time}
                            )
                            logger.warning(f"⚠ No hotels found from {scraper_name} for {dest}")
                        return hotels or []
                except Exception as e:
                    response_time = asyncio.get_event_loop().time() - start_time
                    error_type = type(e).__name__
                    
                    self.monitor.record_metric(
                        scraper_name,
                        'failure',
                        metadata={'error_type': error_type, 'response_time': response_time, 'error': str(e)}
                    )
                    
                    # Create alert for failures
                    self.alert_manager.create_alert(
                        severity=AlertSeverity.WARNING,
                        title=f"Scraping failure: {scraper_name}",
                        message=f"Error collecting from {scraper_name} for {dest}: {e}",
                        source=scraper_name,
                        metadata={'destination': dest, 'error_type': error_type}
                    )
                    
                    logger.warning(f"⚠ Error collecting from {scraper_name}: {e}")
                    return []
            
            # Submit all scraping tasks concurrently
            tasks = []
            for scraper in self.scrapers:
                task_id = f"{scraper.__class__.__name__}_{destination}_{id(scraper)}"
                await self.concurrent_scraper.submit(
                    task_id=task_id,
                    func=scrape_with_provider,
                    args=(scraper, destination),
                    priority=5  # Normal priority
                )
                tasks.append(task_id)
            
            # Wait for all tasks to complete
            for task_id in tasks:
                try:
                    hotels = await self.concurrent_scraper.wait_for_task(task_id, timeout=180.0)
                    if hotels:
                        all_hotels.extend(hotels)
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    continue
            
            # Deduplicate and merge hotels from multiple sources
            unique_hotels = self._deduplicate_and_merge_hotels(all_hotels)
            
            # Process hotels concurrently (detail fetching and saving)
            async def process_hotel(hotel_data):
                """Process a single hotel (fetch details and save)."""
                try:
                    # If we have a source URL and enhanced scraping, get detailed information
                    if self.use_enhanced_scraping and hotel_data.get('source_url'):
                        try:
                            # Use enhanced scraper to get detailed information
                            enhanced_scraper = None
                            for scraper in self.scrapers:
                                if hasattr(scraper, 'get_hotel_details'):
                                    enhanced_scraper = scraper
                                    break
                            
                            if enhanced_scraper:
                                logger.info(f"Fetching detailed information for {hotel_data.get('name')}")
                                details = await enhanced_scraper.get_hotel_details(hotel_data['source_url'])
                                
                                if details:
                                    # Extract hotel's official website URL from Booking.com page
                                    hotel_website_url = details.get('hotel_website_url')
                                    
                                    # Merge detailed information
                                    hotel_data.update({
                                        'description': details.get('description', hotel_data.get('description', '')),
                                        'property_overview': details.get('property_overview', ''),
                                        'images': details.get('images', [hotel_data.get('image_url')] if hotel_data.get('image_url') else []),
                                        'amenities': details.get('amenities', hotel_data.get('amenities', [])),
                                        'policies': details.get('policies', {}),
                                        'rooms_data': details.get('rooms', []),
                                        'reviews_data': details.get('reviews', []),
                                        'location_details': details.get('location_details', {}),
                                        'hotel_website_url': hotel_website_url,
                                    })
                                    
                                    # If we found hotel website URL, scrape it for more comprehensive data
                                    if hotel_website_url:
                                        logger.info(f"Found hotel website: {hotel_website_url}, scraping for comprehensive data...")
                                        try:
                                            from .hotel_website_scraper import HotelWebsiteScraper
                                            website_scraper = HotelWebsiteScraper(use_browser=True)
                                            async with website_scraper:
                                                website_data = await website_scraper.scrape_hotel_website(hotel_website_url)
                                                if website_data:
                                                    # Merge website data (prefer website data as it's more comprehensive)
                                                    if website_data.get('rooms'):
                                                        hotel_data['rooms_data'] = website_data['rooms']
                                                        logger.info(f"Found {len(website_data['rooms'])} rooms from hotel website")
                                                    if website_data.get('images'):
                                                        # Merge images from website
                                                        existing_images = hotel_data.get('images', [])
                                                        website_images = website_data.get('images', [])
                                                        all_images = list(set(existing_images + website_images))
                                                        hotel_data['images'] = all_images[:50]
                                                    if website_data.get('description'):
                                                        hotel_data['description'] = website_data['description']
                                                    if website_data.get('amenities'):
                                                        # Merge amenities
                                                        existing_amenities = hotel_data.get('amenities', [])
                                                        website_amenities = website_data.get('amenities', [])
                                                        all_amenities = list(set(existing_amenities + website_amenities))
                                                        hotel_data['amenities'] = all_amenities
                                        except Exception as e:
                                            logger.warning(f"Error scraping hotel website: {e}")
                        except Exception as e:
                            logger.warning(f"Error fetching detailed information for {hotel_data.get('name')}: {e}. Using basic data.")
                    
                    saved = await self._save_hotel(hotel_data, destination, country)
                    return saved
                except Exception as e:
                    logger.error(f"Error processing hotel {hotel_data.get('name')}: {e}")
                    return False
            
            # Process hotels concurrently
            hotel_tasks = []
            for hotel_data in unique_hotels[:max_hotels]:
                task_id = f"hotel_{hotel_data.get('name', 'unknown')}_{id(hotel_data)}"
                await self.concurrent_scraper.submit(
                    task_id=task_id,
                    func=process_hotel,
                    args=(hotel_data,),
                    priority=10  # Higher priority for detail fetching
                )
                hotel_tasks.append(task_id)
            
            # Wait for all hotel processing tasks
            for task_id in hotel_tasks:
                try:
                    saved = await self.concurrent_scraper.wait_for_task(task_id, timeout=300.0)
                    if saved:
                        collected_count += 1
                except Exception as e:
                    logger.error(f"Hotel processing task {task_id} failed: {e}")
                    continue
            
            self.db_session.commit()
            logger.info(f"Successfully collected {collected_count} hotels for {destination}")
            
        except Exception as e:
            logger.error(f"Error collecting hotels for {destination}: {e}")
            self.db_session.rollback()
        
        return collected_count
    
    def _deduplicate_hotels(self, hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate hotels based on name and location."""
        seen = set()
        unique = []
        
        for hotel in hotels:
            # Create a key from name and city
            key = (hotel.get('name', '').lower().strip(), hotel.get('city', '').lower().strip())
            
            if key not in seen and key[0]:  # Ensure name is not empty
                seen.add(key)
                unique.append(hotel)
        
        return unique
    
    def _deduplicate_and_merge_hotels(self, hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate hotels and merge data from multiple sources."""
        hotel_map = {}  # key: (name, city) -> hotel_data
        
        for hotel in hotels:
            # Normalize hotel name (remove common suffixes)
            name = hotel.get('name', '').lower().strip()
            # Remove common suffixes like "Opens in new window", etc.
            name = re.sub(r'\s*(opens?\s+in\s+new\s+window|\.\.\.|…)\s*$', '', name, flags=re.IGNORECASE)
            city = hotel.get('city', '').lower().strip()
            
            key = (name, city)
            
            if not name:
                continue
            
            if key in hotel_map:
                # Merge data from multiple sources
                existing = hotel_map[key]
                
                # Merge images (combine unique images)
                existing_images = existing.get('images', []) or []
                new_images = hotel.get('images', []) or []
                if hotel.get('image_url'):
                    new_images.append(hotel['image_url'])
                all_images = list(set(existing_images + new_images))
                existing['images'] = all_images[:50]  # Limit to 50
                
                # Merge amenities (combine unique amenities)
                existing_amenities = existing.get('amenities', []) or []
                new_amenities = hotel.get('amenities', []) or []
                all_amenities = list(set(existing_amenities + new_amenities))
                existing['amenities'] = all_amenities
                
                # Use better rating if available
                if hotel.get('rating') and (not existing.get('rating') or hotel.get('rating', 0) > existing.get('rating', 0)):
                    existing['rating'] = hotel.get('rating')
                
                # Use better price if available (lower is better)
                if hotel.get('price_per_night') and (not existing.get('price_per_night') or hotel.get('price_per_night', 0) < existing.get('price_per_night', float('inf'))):
                    existing['price_per_night'] = hotel.get('price_per_night')
                
                # Merge sources (track which providers have this hotel)
                if 'sources' not in existing:
                    existing['sources'] = [existing.get('source', 'unknown')]
                if hotel.get('source') and hotel.get('source') not in existing['sources']:
                    existing['sources'].append(hotel.get('source'))
                
                # Use source URL if not already set
                if not existing.get('source_url') and hotel.get('source_url'):
                    existing['source_url'] = hotel.get('source_url')
                
                # Merge other fields if missing
                if not existing.get('description') and hotel.get('description'):
                    existing['description'] = hotel.get('description')
                if not existing.get('address') and hotel.get('address'):
                    existing['address'] = hotel.get('address')
                if not existing.get('stars') and hotel.get('stars'):
                    existing['stars'] = hotel.get('stars')
            else:
                # First occurrence of this hotel
                hotel_copy = hotel.copy()
                # Normalize images list
                images = hotel_copy.get('images', []) or []
                if hotel_copy.get('image_url'):
                    images.append(hotel_copy['image_url'])
                hotel_copy['images'] = list(set(images))[:50]
                # Track sources
                hotel_copy['sources'] = [hotel_copy.get('source', 'unknown')]
                hotel_map[key] = hotel_copy
        
        return list(hotel_map.values())
    
    async def _save_hotel(
        self,
        hotel_data: Dict[str, Any],
        destination: str,
        country: Optional[str] = None
    ) -> bool:
        """Save hotel data to database."""
        try:
            # Check if hotel already exists
            existing = self.db_session.query(HotelModel).filter(
                and_(
                    HotelModel.name.ilike(hotel_data.get('name', '')),
                    HotelModel.city.ilike(destination)
                )
            ).first()
            
            if existing:
                # Update existing hotel with enhanced data (only if real data exists)
                if hotel_data.get('address'):
                    existing.address = hotel_data.get('address')
                if hotel_data.get('description'):
                    existing.description = hotel_data.get('description')
                if hotel_data.get('property_overview'):
                    existing.property_overview = hotel_data.get('property_overview')
                
                # Update images - merge new images with existing
                new_images = hotel_data.get('images', [])
                if not new_images and hotel_data.get('image_url'):
                    new_images = [hotel_data['image_url']]
                if new_images:
                    # Merge and deduplicate images
                    existing_images = existing.images or []
                    all_images = list(set(existing_images + new_images))
                    existing.images = all_images[:50]  # Limit to 50 images
                
                existing.amenities = hotel_data.get('amenities') or existing.amenities
                existing.policies = hotel_data.get('policies') or existing.policies
                if hotel_data.get('rating'):
                    existing.rating = hotel_data.get('rating')
                if hotel_data.get('stars'):
                    existing.stars = hotel_data.get('stars')
                existing.updated_at = datetime.utcnow()
                
                # Update rooms and reviews if we have new data
                rooms_data = hotel_data.get('rooms_data', [])
            if rooms_data:
                # Filter out invalid rooms (like "Guest reviews", "Sustainability", etc.)
                valid_rooms = []
                for room in rooms_data:
                    room_name = room.get('room_type_name', '').lower().strip()
                    # Filter out non-room elements
                    invalid_patterns = ['guest reviews', 'reviews', 'sustainability', 'environment', 
                                      'green', 'eco', 'location', 'map', 'directions', 'contact',
                                      'check-in', 'check-out', 'cancellation', 'terms', 'conditions',
                                      'privacy', 'cookie', 'accessibility', 'access', 'wheelchair',
                                      'parking', 'transportation', 'airport', 'amenities', 'facilities',
                                      'policies', 'description', 'overview']
                    if not any(pattern in room_name for pattern in invalid_patterns):
                        # Also check if it's a valid room name (has room indicators or is short)
                        room_indicators = ['room', 'suite', 'apartment', 'villa', 'studio', 'deluxe', 
                                         'standard', 'executive', 'presidential', 'junior', 'superior',
                                         'family', 'double', 'single', 'twin', 'king', 'queen', 'bed',
                                         'accommodation', 'basic']
                        if any(indicator in room_name for indicator in room_indicators) or len(room.get('room_type_name', '')) <= 20:
                            valid_rooms.append(room)
                
                if valid_rooms:
                    # Delete old rooms and create new ones with ALL valid rooms (no limit!)
                    self.db_session.query(RoomModel).filter(RoomModel.hotel_id == existing.id).delete()
                    await self._save_real_rooms(existing, valid_rooms)
                    logger.info(f"Updated {existing.name} with {len(valid_rooms)} real rooms")
                else:
                    # If no valid rooms found, keep existing rooms or leave empty (no dummy rooms)
                    existing_room_count = self.db_session.query(RoomModel).filter(RoomModel.hotel_id == existing.id).count()
                    if existing_room_count == 0:
                        logger.info(f"No valid rooms found for {existing.name}, hotel will have no rooms (real data only)")
                    else:
                        logger.info(f"No new valid rooms found for {existing.name}, keeping {existing_room_count} existing rooms")
                
                reviews_data = hotel_data.get('reviews_data', [])
                if reviews_data:
                    # Add new reviews (don't delete old ones)
                    await self._save_real_reviews(existing, reviews_data)
                
                return True
            
            # Create new hotel
            # Map source to provider
            source = hotel_data.get('source', 'unknown')
            provider_map = {
                'booking.com': Provider.BOOKING_COM,
                'tripadvisor': Provider.BOOKING_COM,  # Use booking.com as default
            }
            provider = provider_map.get(source.lower(), Provider.BOOKING_COM)
            
            # Extract coordinates if available
            latitude = hotel_data.get('latitude')
            longitude = hotel_data.get('longitude')
            
            # If no coordinates, geocode the address
            if not latitude or not longitude:
                coords = await self.geocoding.geocode(
                    address=hotel_data.get('address', ''),
                    city=destination,
                    country=country
                )
                if coords:
                    latitude, longitude = coords
                else:
                    # Fallback: geocode just the city
                    coords = await self.geocoding.geocode_city(city=destination, country=country)
                    if coords:
                        latitude, longitude = coords
                    else:
                        # No coordinates available - skip this hotel (we need real location data)
                        logger.warning(f"Could not geocode location for {hotel_data.get('name')} in {destination}, skipping hotel")
                        return False
            
            # Get images - prefer scraped images, fallback to single image_url
            images = hotel_data.get('images', [])
            if not images and hotel_data.get('image_url'):
                images = [hotel_data['image_url']]
            
            # Upgrade image quality before saving
            if images:
                upgraded_images = []
                for img_url in images:
                    if isinstance(img_url, str):
                        # Upgrade Booking.com images
                        if 'bstatic.com' in img_url:
                            import re
                            img_url = re.sub(r'/max\d+x?\d*/', '/max1920x1080/', img_url)
                            img_url = re.sub(r'/square\d+/', '/max1920x1080/', img_url)
                            img_url = re.sub(r'/max\d+/', '/max1920x1080/', img_url)
                        # Upgrade Expedia images
                        elif 'expedia.com' in img_url or 'media.expedia.com' in img_url:
                            import re
                            img_url = re.sub(r'[?&]w=\d+', '?w=1920', img_url)
                            img_url = re.sub(r'[?&]h=\d+', '&h=1080', img_url)
                            if '?' not in img_url:
                                img_url += '?w=1920&h=1080'
                        # Upgrade Hotels.com images
                        elif 'hotels.com' in img_url or 'media.hotels.com' in img_url:
                            import re
                            img_url = re.sub(r'[?&]size=\w+', '?size=large', img_url)
                            if '?' not in img_url:
                                img_url += '?size=large'
                        upgraded_images.append(img_url)
                    else:
                        upgraded_images.append(img_url)
                images = upgraded_images
            
            new_hotel = HotelModel(
                provider_hotel_id=f"{source}_{hotel_data.get('name', '')[:50]}",
                provider=provider.value,
                name=hotel_data.get('name', 'Unknown Hotel'),
                address=hotel_data.get('address') or destination,
                city=destination,
                country=country or hotel_data.get('country', 'Unknown'),
                latitude=latitude,
                longitude=longitude,
                stars=hotel_data.get('stars', 3),
                description=hotel_data.get('description') or None,  # No dummy description
                property_overview=hotel_data.get('property_overview', ''),
                images=images,
                amenities=hotel_data.get('amenities', []),
                policies=hotel_data.get('policies', {}),
                rating=hotel_data.get('rating'),
                source_url=hotel_data.get('source_url'),
            )
            
            self.db_session.add(new_hotel)
            self.db_session.flush()  # Get the ID
            
            # Use real room data if available, otherwise create defaults
            rooms_data = hotel_data.get('rooms_data', [])
            if rooms_data:
                # Filter out invalid rooms (like "Guest reviews", "Sustainability", etc.)
                valid_rooms = []
                for room in rooms_data:
                    room_name = room.get('room_type_name', '').lower().strip()
                    # Filter out non-room elements
                    invalid_patterns = ['guest reviews', 'reviews', 'sustainability', 'environment', 
                                      'green', 'eco', 'location', 'map', 'directions', 'contact',
                                      'check-in', 'check-out', 'cancellation', 'terms', 'conditions',
                                      'privacy', 'cookie', 'accessibility', 'access', 'wheelchair',
                                      'parking', 'transportation', 'airport', 'amenities', 'facilities',
                                      'policies', 'description', 'overview']
                    if not any(pattern in room_name for pattern in invalid_patterns):
                        # Also check if it's a valid room name (has room indicators or is short)
                        room_indicators = ['room', 'suite', 'apartment', 'villa', 'studio', 'deluxe', 
                                         'standard', 'executive', 'presidential', 'junior', 'superior',
                                         'family', 'double', 'single', 'twin', 'king', 'queen', 'bed',
                                         'accommodation', 'basic']
                        if any(indicator in room_name for indicator in room_indicators) or len(room.get('room_type_name', '')) <= 20:
                            valid_rooms.append(room)
                
                if valid_rooms:
                    await self._save_real_rooms(new_hotel, valid_rooms)
                    logger.info(f"Created {new_hotel.name} with {len(valid_rooms)} real rooms")
                else:
                    # If no valid rooms found, hotel will have no rooms (real data only)
                    logger.info(f"No valid rooms found for {new_hotel.name}, hotel will have no rooms (real data only)")
            # If no rooms data at all, hotel will have no rooms (real data only)
            
            # Use real review data only - no dummy reviews
            reviews_data = hotel_data.get('reviews_data', [])
            if reviews_data:
                await self._save_real_reviews(new_hotel, reviews_data)
                logger.info(f"Saved {len(reviews_data)} real reviews for {new_hotel.name}")
            # If no reviews found, hotel will have no reviews (which is fine - only show real data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving hotel: {e}")
            return False
    
    async def collect_popular_destinations(self, destinations: List[Dict[str, str]]) -> Dict[str, int]:
        """Collect hotels for multiple popular destinations.
        
        Args:
            destinations: List of dicts with 'city' and 'country' keys
            
        Returns:
            Dictionary mapping destination to number of hotels collected
        """
        results = {}
        
        for dest in destinations:
            city = dest.get('city')
            country = dest.get('country')
            
            logger.info(f"Collecting hotels for {city}, {country}")
            count = await self.collect_hotels_for_destination(
                destination=city,
                country=country,
                max_hotels=50
            )
            results[f"{city}, {country}"] = count
            
            # Delay between destinations
            await asyncio.sleep(2)
        
        return results
    
    async def _create_default_rooms(self, hotel: HotelModel) -> None:
        """Create default rooms for a hotel."""
        room_types = [
            {
                'name': 'Standard Room',
                'size': 18,
                'max_guests': 2,
                'bed_type': '1 queen bed or 2 separate beds',
                'price': 180
            },
            {
                'name': 'Comfort Room',
                'size': 25,
                'max_guests': 2,
                'bed_type': '1 king size bed',
                'price': 220
            },
            {
                'name': 'Deluxe Room',
                'size': 35,
                'max_guests': 2,
                'bed_type': '1 king size bed and couch',
                'price': 280
            },
        ]
        
        for room_data in room_types:
            room = RoomModel(
                hotel_id=hotel.id,
                room_type_name=room_data['name'],
                description=f"Comfortable {room_data['name'].lower()} with modern amenities",
                images=hotel.images[:1] if hotel.images else [],
                occupancy={
                    'size': room_data['size'],
                    'max_guests': room_data['max_guests'],
                    'bed_type': room_data['bed_type']
                },
                amenities=['WiFi', 'TV', 'Air conditioning', 'Private bathroom']
            )
            self.db_session.add(room)
            self.db_session.flush()
            
            # Create offer for this room
            check_in = date.today() + timedelta(days=1)
            check_out = check_in + timedelta(days=2)
            
            offer = OfferModel(
                hotel_id=hotel.id,
                room_id=room.id,
                provider=hotel.provider,
                provider_rate_id=f"default_{hotel.id}_{room.id}",
                currency='USD',
                price=room_data['price'],
                taxes_included=True,
                check_in=check_in,
                check_out=check_out,
                availability_count=5,
                cancellation_policy={'free_cancellation': True, 'deadline': '24 hours before check-in'},
            )
            self.db_session.add(offer)
    
    async def _create_default_reviews(self, hotel: HotelModel, rating: float) -> None:
        """Create default reviews for a hotel."""
        review_data = [
            {
                'title': 'Excellent value for the price!',
                'author': 'Mark M.',
                'text': 'We enjoyed our stay at this hotel. We will definitely come back!',
                'rating': min(10.0, rating + 0.5) if rating else 10.0,
                'pros': ['Great location!', 'Service', 'Bottle of champagne in the room!'],
                'cons': [],
                'category_ratings': {'cleanliness': 10, 'amenities': 9, 'location': 10, 'comfort': 9, 'wifi': 9}
            },
            {
                'title': 'Good hotel but noisy location',
                'author': 'Karena L.',
                'text': 'Had room facing the street and it was super noisy. Unfortunately, we couldn\'t change room.',
                'rating': max(5.0, rating - 1.0) if rating else 5.6,
                'pros': [],
                'cons': ['Noise'],
                'category_ratings': {'cleanliness': 7, 'amenities': 6, 'location': 4, 'comfort': 6, 'wifi': 7}
            }
        ]
        
        for rev_data in review_data:
            review = ReviewModel(
                hotel_id=hotel.id,
                provider=hotel.provider,
                rating=rev_data['rating'],
                title=rev_data['title'],
                text=rev_data['text'],
                author=rev_data['author'],
                pros=rev_data['pros'],
                cons=rev_data['cons'],
                category_ratings=rev_data['category_ratings']
            )
            self.db_session.add(review)
    
    async def _save_real_rooms(self, hotel: HotelModel, rooms_data: List[Dict[str, Any]]) -> None:
        """Save real room data scraped from hotel detail page."""
        logger.info(f"Saving {len(rooms_data)} rooms for {hotel.name}")
        for room_data in rooms_data:
            try:
                # Extract images - use room images if available, otherwise use hotel images
                room_images = room_data.get('images', [])
                if not room_images and hotel.images:
                    # Use first hotel image as fallback
                    room_images = hotel.images[:1]
                
                # Ensure images is a list
                if not isinstance(room_images, list):
                    room_images = [room_images] if room_images else []
                
                # Clean image URLs
                cleaned_images = []
                for img in room_images:
                    if isinstance(img, str) and img.startswith(('http://', 'https://')):
                        cleaned_images.append(img)
                    elif isinstance(img, dict):
                        # Extract URL from image dict
                        img_url = img.get('url') or img.get('src') or img.get('imageUrl')
                        if img_url:
                            cleaned_images.append(img_url)
                
                room = RoomModel(
                    hotel_id=hotel.id,
                    room_type_name=room_data.get('room_type_name', 'Standard Room'),
                    description=room_data.get('description', ''),
                    images=cleaned_images[:10],  # Limit to 10 images per room
                    occupancy=room_data.get('occupancy', {
                        'size': 18,
                        'max_guests': 2,
                        'bed_type': '1 queen bed or 2 separate beds'
                    }),
                    amenities=room_data.get('amenities', ['WiFi', 'TV', 'Air conditioning', 'Private bathroom'])
                )
                self.db_session.add(room)
                self.db_session.flush()
                logger.debug(f"Saved room: {room.room_type_name} with {len(cleaned_images)} images")
                
                # Create offer for this room
                check_in = date.today() + timedelta(days=1)
                check_out = check_in + timedelta(days=2)
                
                # Calculate price based on room type (rough estimate)
                base_price = 180
                if 'deluxe' in room_data.get('room_type_name', '').lower():
                    base_price = 280
                elif 'comfort' in room_data.get('room_type_name', '').lower():
                    base_price = 220
                
                offer = OfferModel(
                    hotel_id=hotel.id,
                    room_id=room.id,
                    provider=hotel.provider,
                    provider_rate_id=f"default_{hotel.id}_{room.id}",
                    currency='USD',
                    price=base_price,
                    taxes_included=True,
                    check_in=check_in,
                    check_out=check_out,
                    availability_count=5,
                    cancellation_policy={'free_cancellation': True, 'deadline': '24 hours before check-in'},
                )
                self.db_session.add(offer)
            except Exception as e:
                logger.error(f"Error saving room {room_data.get('room_type_name')}: {e}")
                continue
    
    async def _save_real_reviews(self, hotel: HotelModel, reviews_data: List[Dict[str, Any]]) -> None:
        """Save real review data scraped from hotel detail page."""
        for review_data in reviews_data:
            try:
                review = ReviewModel(
                    hotel_id=hotel.id,
                    provider=hotel.provider,
                    rating=review_data.get('rating', hotel.rating or 9.0),
                    title=review_data.get('title', ''),
                    text=review_data.get('text', ''),
                    author=review_data.get('author', 'Anonymous'),
                    pros=review_data.get('pros', []),
                    cons=review_data.get('cons', []),
                    category_ratings=review_data.get('category_ratings', {})
                )
                self.db_session.add(review)
            except Exception as e:
                logger.error(f"Error saving review: {e}")
                continue

