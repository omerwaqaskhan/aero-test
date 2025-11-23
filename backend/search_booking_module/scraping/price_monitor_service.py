"""Background service for continuous price monitoring."""

import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .price_checker import PriceChecker
from .config import (
    PRICE_CHECK_ENABLED,
    PRICE_CHECK_INTERVAL_HOURS,
    PRICE_CHECK_MAX_CONCURRENT,
    PRICE_CHECK_MAX_AGE_HOURS
)
from auth_module.infrastructure.db.database import SessionLocal

logger = logging.getLogger(__name__)


class PriceMonitorService:
    """Background service for monitoring and updating hotel prices."""
    
    def __init__(
        self,
        db_session_factory=SessionLocal,
        enabled: Optional[bool] = None,
        check_interval_hours: Optional[int] = None,
        max_concurrent: Optional[int] = None
    ):
        """Initialize price monitor service.
        
        Args:
            db_session_factory: Factory function to create database sessions
            enabled: Whether price monitoring is enabled (defaults to config)
            check_interval_hours: Hours between price checks (defaults to config)
            max_concurrent: Maximum concurrent price checks (defaults to config)
        """
        self.db_session_factory = db_session_factory
        self.enabled = enabled if enabled is not None else PRICE_CHECK_ENABLED
        self.check_interval_hours = check_interval_hours or PRICE_CHECK_INTERVAL_HOURS
        self.max_concurrent = max_concurrent or PRICE_CHECK_MAX_CONCURRENT
        self.price_checker: Optional[PriceChecker] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """Start the price monitoring service."""
        if not self.enabled:
            logger.info("Price monitoring is disabled")
            return
        
        if self.is_running:
            logger.warning("Price monitor service is already running")
            return
        
        logger.info("Starting price monitor service...")
        
        # Create database session and price checker
        db: Session = self.db_session_factory()
        try:
            self.price_checker = PriceChecker(
                db_session=db,
                max_concurrent=self.max_concurrent,
                check_interval_hours=self.check_interval_hours
            )
            await self.price_checker.start()
            
            # Start background monitoring task
            self.monitor_task = asyncio.create_task(self._monitor_prices_continuously())
            self.is_running = True
            
            logger.info(f"Price monitor service started (check interval: {self.check_interval_hours}h)")
        except Exception as e:
            logger.error(f"Failed to start price monitor service: {e}")
            db.close()
            raise
    
    async def stop(self):
        """Stop the price monitoring service."""
        if not self.is_running:
            return
        
        logger.info("Stopping price monitor service...")
        
        self.is_running = False
        
        # Cancel monitoring task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop price checker
        if self.price_checker:
            await self.price_checker.stop()
            # Close database session
            if hasattr(self.price_checker, 'db_session'):
                self.price_checker.db_session.close()
        
        logger.info("Price monitor service stopped")
    
    async def _monitor_prices_continuously(self):
        """Continuously monitor and update prices."""
        logger.info("Price monitoring loop started")
        
        while self.is_running:
            try:
                # Check stale prices
                logger.info(f"Checking prices for hotels with stale data (max age: {PRICE_CHECK_MAX_AGE_HOURS}h)...")
                results = await self.price_checker.check_stale_prices(
                    max_age_hours=PRICE_CHECK_MAX_AGE_HOURS,
                    limit=100  # Check 100 hotels per cycle
                )
                
                logger.info(f"Price check cycle completed: {len(results)} hotels checked")
                
                # Wait before next check cycle
                wait_seconds = self.check_interval_hours * 3600
                logger.info(f"Next price check in {self.check_interval_hours} hours...")
                
                # Wait in smaller intervals to allow for graceful shutdown
                for _ in range(wait_seconds // 60):  # Check every minute
                    if not self.is_running:
                        break
                    await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                logger.info("Price monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in price monitoring loop: {e}")
                # Wait 5 minutes before retrying on error
                await asyncio.sleep(300)
    
    async def check_prices_now(self, limit: int = 50):
        """Manually trigger price check for stale hotels.
        
        Args:
            limit: Maximum number of hotels to check
        """
        if not self.price_checker:
            logger.error("Price checker not initialized")
            return []
        
        try:
            results = await self.price_checker.check_stale_prices(
                max_age_hours=PRICE_CHECK_MAX_AGE_HOURS,
                limit=limit
            )
            logger.info(f"Manual price check completed: {len(results)} hotels checked")
            return results
        except Exception as e:
            logger.error(f"Error in manual price check: {e}")
            return []


# Global price monitor instance
_global_price_monitor: Optional[PriceMonitorService] = None


def get_price_monitor() -> PriceMonitorService:
    """Get or create the global price monitor instance."""
    global _global_price_monitor
    if _global_price_monitor is None:
        _global_price_monitor = PriceMonitorService()
    return _global_price_monitor


async def start_price_monitor():
    """Start the global price monitor."""
    monitor = get_price_monitor()
    await monitor.start()


async def stop_price_monitor():
    """Stop the global price monitor."""
    monitor = get_price_monitor()
    await monitor.stop()

