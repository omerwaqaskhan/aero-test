"""Real-time price checking service."""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import asyncio
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..infrastructure.db.models import HotelModel, OfferModel, RoomModel
from .enhanced_booking_scraper import EnhancedBookingScraper
from .expedia_scraper import ExpediaScraper
from .hotels_com_scraper import HotelsComScraper
from .agoda_scraper import AgodaScraper
from .concurrent_scraper import ConcurrentScraper
from .config import (
    PRICE_CHECK_INTERVAL_HOURS,
    PRICE_CHECK_MAX_CONCURRENT
)

logger = logging.getLogger(__name__)


class PriceChecker:
    """Service for checking and updating hotel prices in real-time."""
    
    def __init__(
        self,
        db_session: Session,
        max_concurrent: Optional[int] = None,
        check_interval_hours: Optional[int] = None
    ):
        """Initialize price checker.
        
        Args:
            db_session: Database session
            max_concurrent: Maximum concurrent price checks (defaults to config)
            check_interval_hours: How often to check prices (defaults to config)
        """
        self.db_session = db_session
        self.max_concurrent = max_concurrent or PRICE_CHECK_MAX_CONCURRENT
        self.check_interval_hours = check_interval_hours or PRICE_CHECK_INTERVAL_HOURS
        
        # Initialize scrapers
        self.scrapers = [
            EnhancedBookingScraper(use_browser=True),
            ExpediaScraper(use_browser=True),
            HotelsComScraper(use_browser=True),
            AgodaScraper(use_browser=True),
        ]
        
        # Initialize concurrent scraper
        self.concurrent_scraper = ConcurrentScraper(
            max_workers=max_concurrent,
            queue_size=500,
            timeout=120.0
        )
        
        self.is_running = False
    
    async def start(self):
        """Start the price checker."""
        await self.concurrent_scraper.start()
        self.is_running = True
        logger.info("Price checker started")
    
    async def stop(self):
        """Stop the price checker."""
        self.is_running = False
        await self.concurrent_scraper.stop()
        logger.info("Price checker stopped")
    
    async def check_hotel_prices(
        self,
        hotel_id: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None
    ) -> Dict[str, Any]:
        """Check prices for a specific hotel.
        
        Args:
            hotel_id: Hotel ID
            check_in: Check-in date (default: tomorrow)
            check_out: Check-out date (default: check_in + 2 days)
            
        Returns:
            Dictionary with price information from multiple providers
        """
        if check_in is None:
            check_in = date.today() + timedelta(days=1)
        if check_out is None:
            check_out = check_in + timedelta(days=2)
        
        # Get hotel from database
        hotel = self.db_session.query(HotelModel).filter(
            HotelModel.id == hotel_id
        ).first()
        
        if not hotel:
            raise ValueError(f"Hotel {hotel_id} not found")
        
        logger.info(f"Checking prices for {hotel.name} ({check_in} to {check_out})")
        
        # Check prices from all providers concurrently
        price_results = {}
        
        async def check_provider_price(scraper, hotel_name, hotel_url, dest):
            """Check price from a single provider."""
            try:
                if not hotel_url:
                    return None
                
                # Get hotel details which includes pricing
                details = await scraper.get_hotel_details(hotel_url)
                if not details:
                    return None
                
                # Extract pricing information
                # This would need to be implemented based on scraper response
                # For now, we'll return a placeholder
                return {
                    'provider': scraper.__class__.__name__,
                    'price': None,  # Would extract from details
                    'currency': 'USD',
                    'available': True,
                    'checked_at': datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Error checking price from {scraper.__class__.__name__}: {e}")
                return None
        
        # Submit price check tasks
        tasks = []
        for scraper in self.scrapers:
            task_id = f"price_check_{hotel_id}_{scraper.__class__.__name__}"
            await self.concurrent_scraper.submit(
                task_id=task_id,
                func=check_provider_price,
                args=(scraper, hotel.name, hotel.source_url, f"{hotel.city}, {hotel.country}"),
                priority=5
            )
            tasks.append(task_id)
        
        # Wait for results
        for task_id in tasks:
            try:
                result = await self.concurrent_scraper.wait_for_task(task_id, timeout=120.0)
                if result:
                    provider = result.get('provider')
                    if provider:
                        price_results[provider] = result
            except Exception as e:
                logger.error(f"Price check task {task_id} failed: {e}")
                continue
        
        return {
            'hotel_id': hotel_id,
            'hotel_name': hotel.name,
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'prices': price_results,
            'checked_at': datetime.utcnow().isoformat()
        }
    
    async def update_hotel_offers(
        self,
        hotel_id: str,
        check_in: date,
        check_out: date,
        prices: Dict[str, Dict[str, Any]]
    ) -> int:
        """Update hotel offers with new prices.
        
        Args:
            hotel_id: Hotel ID
            check_in: Check-in date
            check_out: Check-out date
            prices: Dictionary of prices from providers
            
        Returns:
            Number of offers updated
        """
        hotel = self.db_session.query(HotelModel).filter(
            HotelModel.id == hotel_id
        ).first()
        
        if not hotel:
            return 0
        
        updated_count = 0
        
        # Get or create rooms
        rooms = self.db_session.query(RoomModel).filter(
            RoomModel.hotel_id == hotel_id
        ).all()
        
        if not rooms:
            # No rooms available - can't create offers without real room data
            logger.warning(f"No rooms found for hotel {hotel_id}, cannot create offers")
            return 0
        
        # Update offers for each provider
        for provider_name, price_data in prices.items():
            if not price_data or not price_data.get('price'):
                continue
            
            # Map provider name to provider enum
            provider_map = {
                'EnhancedBookingScraper': 'booking_com',
                'ExpediaScraper': 'expedia',
                'HotelsComScraper': 'hotels_com',
                'AgodaScraper': 'agoda',
            }
            
            provider = provider_map.get(provider_name, 'booking_com')
            price = price_data.get('price')
            
            # Find or create offer
            for room in rooms:
                offer = self.db_session.query(OfferModel).filter(
                    and_(
                        OfferModel.hotel_id == hotel_id,
                        OfferModel.room_id == room.id,
                        OfferModel.provider == provider,
                        OfferModel.check_in == check_in,
                        OfferModel.check_out == check_out
                    )
                ).first()
                
                if offer:
                    # Update existing offer
                    offer.price = price
                    offer.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new offer
                    new_offer = OfferModel(
                        hotel_id=hotel_id,
                        room_id=room.id,
                        provider=provider,
                        provider_rate_id=f"{provider}_{hotel_id}_{room.id}_{check_in}",
                        currency=price_data.get('currency', 'USD'),
                        price=price,
                        taxes_included=True,
                        check_in=check_in,
                        check_out=check_out,
                        availability_count=5 if price_data.get('available') else 0,
                        cancellation_policy={'free_cancellation': True}
                    )
                    self.db_session.add(new_offer)
                    updated_count += 1
        
        self.db_session.commit()
        logger.info(f"Updated {updated_count} offers for hotel {hotel_id}")
        
        return updated_count
    
    async def check_stale_prices(
        self,
        max_age_hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Check prices for hotels with stale price data.
        
        Args:
            max_age_hours: Maximum age of price data in hours
            limit: Maximum number of hotels to check
            
        Returns:
            List of price check results
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Find hotels with stale or missing offers
        hotels = self.db_session.query(HotelModel).filter(
            HotelModel.updated_at < cutoff_time
        ).limit(limit).all()
        
        logger.info(f"Found {len(hotels)} hotels with stale prices")
        
        results = []
        for hotel in hotels:
            try:
                result = await self.check_hotel_prices(hotel.id)
                results.append(result)
                
                # Update offers if we got prices
                if result.get('prices'):
                    check_in = date.today() + timedelta(days=1)
                    check_out = check_in + timedelta(days=2)
                    await self.update_hotel_offers(
                        hotel.id,
                        check_in,
                        check_out,
                        result['prices']
                    )
                
                # Small delay between hotels
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error checking prices for hotel {hotel.id}: {e}")
                continue
        
        return results
    
    async def monitor_prices_continuously(self):
        """Continuously monitor and update prices."""
        logger.info("Starting continuous price monitoring")
        
        while self.is_running:
            try:
                # Check stale prices
                await self.check_stale_prices(max_age_hours=self.check_interval_hours)
                
                # Wait before next check cycle
                await asyncio.sleep(self.check_interval_hours * 3600)
            except Exception as e:
                logger.error(f"Error in continuous price monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

