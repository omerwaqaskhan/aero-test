"""Background scheduler for automatic hotel data collection."""

import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .data_collector import HotelDataCollector
from .config import (
    AUTO_POPULATE_ON_STARTUP,
    AUTO_REFRESH_ENABLED,
    REFRESH_TIME,
    REFRESH_INTERVAL_HOURS,
    POPULAR_DESTINATIONS,
    PRICE_CHECK_ENABLED
)
from auth_module.infrastructure.db.database import SessionLocal
from .price_monitor_service import start_price_monitor, stop_price_monitor

logger = logging.getLogger(__name__)


class HotelDataScheduler:
    """Scheduler for automatic hotel data collection and updates."""
    
    def __init__(
        self,
        db_session_factory=SessionLocal,
        initial_populate: Optional[bool] = None,
        auto_refresh: Optional[bool] = None,
        refresh_interval_hours: Optional[int] = None,
        refresh_time: Optional[str] = None
    ):
        """Initialize scheduler.
        
        Args:
            db_session_factory: Factory function to create database sessions
            initial_populate: If True, populate database on startup if empty
            auto_refresh: If True, schedule automatic data refresh
            refresh_interval_hours: Hours between refreshes (if using interval)
            refresh_time: Time of day for refresh (HH:MM format, if using cron)
        """
        self.db_session_factory = db_session_factory
        self.initial_populate = initial_populate if initial_populate is not None else AUTO_POPULATE_ON_STARTUP
        self.auto_refresh = auto_refresh if auto_refresh is not None else AUTO_REFRESH_ENABLED
        self.refresh_interval_hours = refresh_interval_hours or REFRESH_INTERVAL_HOURS
        self.refresh_time = refresh_time or REFRESH_TIME
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting hotel data scheduler...")
        
        # Initial population if enabled and database is empty
        if self.initial_populate:
            await self._check_and_populate()
        
        # Schedule automatic refresh if enabled
        if self.auto_refresh:
            # Schedule daily refresh at specified time
            hour, minute = map(int, self.refresh_time.split(':'))
            self.scheduler.add_job(
                self._refresh_all_destinations,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_hotel_refresh',
                name='Daily Hotel Data Refresh',
                replace_existing=True
            )
            logger.info(f"Scheduled daily refresh at {self.refresh_time}")
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Hotel data scheduler started")
        
        # Start price monitoring service if enabled
        if PRICE_CHECK_ENABLED:
            try:
                await start_price_monitor()
                logger.info("Price monitoring service started")
            except Exception as e:
                logger.error(f"Failed to start price monitoring service: {e}")
                # Continue even if price monitoring fails
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        logger.info("Stopping hotel data scheduler...")
        
        # Stop price monitoring service
        try:
            await stop_price_monitor()
            logger.info("Price monitoring service stopped")
        except Exception as e:
            logger.error(f"Error stopping price monitoring service: {e}")
        
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Hotel data scheduler stopped")
    
    async def _check_and_populate(self):
        """Check if database is empty and populate if needed."""
        try:
            db: Session = self.db_session_factory()
            try:
                from search_booking_module.infrastructure.db.models import HotelModel
                
                # Check if database has hotels
                hotel_count = db.query(HotelModel).count()
                
                if hotel_count == 0:
                    logger.info("Database is empty. Starting initial population...")
                    await self._populate_initial_destinations()
                else:
                    logger.info(f"Database already has {hotel_count} hotels. Skipping initial population.")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error checking database: {e}")
    
    async def _populate_initial_destinations(self):
        """Populate database with initial popular destinations."""
        db: Session = self.db_session_factory()
        try:
            collector = HotelDataCollector(db_session=db)
            
            logger.info(f"Populating {len(POPULAR_DESTINATIONS)} popular destinations...")
            
            # Start with first 10 destinations to avoid long startup time
            for dest in POPULAR_DESTINATIONS[:10]:
                city = dest.get('city')
                country = dest.get('country')
                
                try:
                    logger.info(f"Collecting hotels for {city}, {country}...")
                    count = await collector.collect_hotels_for_destination(
                        destination=city,
                        country=country,
                        max_hotels=30  # Start with fewer hotels for initial population
                    )
                    logger.info(f"✓ Collected {count} hotels for {city}, {country}")
                except Exception as e:
                    logger.error(f"✗ Error collecting hotels for {city}, {country}: {e}")
                    continue
                
                # Small delay between destinations
                await asyncio.sleep(2)
            
            logger.info("Initial population completed")
        except Exception as e:
            logger.error(f"Error during initial population: {e}")
        finally:
            db.close()
    
    async def _refresh_all_destinations(self):
        """Refresh hotel data for all destinations in database."""
        try:
            db: Session = self.db_session_factory()
            try:
                from search_booking_module.infrastructure.db.models import HotelModel
                
                # Get all unique cities from database
                cities = db.query(HotelModel.city, HotelModel.country).distinct().all()
                
                if not cities:
                    logger.warning("No destinations found in database. Running initial population...")
                    await self._populate_initial_destinations()
                    return
                
                logger.info(f"Refreshing hotel data for {len(cities)} destinations...")
                
                collector = HotelDataCollector(db_session=db)
                
                for city, country in cities:
                    try:
                        logger.info(f"Refreshing hotels for {city}, {country}...")
                        count = await collector.collect_hotels_for_destination(
                            destination=city,
                            country=country,
                            max_hotels=50
                        )
                        logger.info(f"✓ Refreshed {count} hotels for {city}, {country}")
                    except Exception as e:
                        logger.error(f"✗ Error refreshing hotels for {city}, {country}: {e}")
                        continue
                    
                    # Delay between destinations
                    await asyncio.sleep(3)
                
                logger.info("Hotel data refresh completed")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error during data refresh: {e}")
    
    async def refresh_destination(self, city: str, country: str, max_hotels: int = 50):
        """Manually refresh data for a specific destination.
        
        Args:
            city: City name
            country: Country name
            max_hotels: Maximum hotels to collect
        """
        db: Session = self.db_session_factory()
        try:
            collector = HotelDataCollector(db_session=db)
            count = await collector.collect_hotels_for_destination(
                destination=city,
                country=country,
                max_hotels=max_hotels
            )
            logger.info(f"Refreshed {count} hotels for {city}, {country}")
            return count
        finally:
            db.close()


# Global scheduler instance
_scheduler: Optional[HotelDataScheduler] = None


def get_scheduler() -> HotelDataScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = HotelDataScheduler()
    return _scheduler


async def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()

