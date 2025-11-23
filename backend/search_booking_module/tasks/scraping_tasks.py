"""
Data scraping background tasks using Celery.

This module handles asynchronous hotel data scraping to avoid blocking HTTP requests.
"""

from auth_module.core.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_hotel_data_async(
    self,
    destination: str,
    max_hotels: int = 50
):
    """
    Scrape hotel data for a destination asynchronously.
    
    Args:
        destination: Destination city or location
        max_hotels: Maximum number of hotels to scrape
    
    Returns:
        dict: Scraping results with hotel count
    """
    try:
        # Import here to avoid circular dependencies
        from ..scraping.hotel_data_collector import HotelDataCollector
        from auth_module.infrastructure.db.database import get_db
        
        db = next(get_db())
        collector = HotelDataCollector(db_session=db)
        
        result = collector.collect_hotels_for_destination(
            destination=destination,
            limit=max_hotels
        )
        
        logger.info(f"Scraped {result.get('hotels_added', 0)} hotels for {destination}")
        return result
    except Exception as exc:
        logger.error(f"Failed to scrape hotels for {destination}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=600)
def refresh_hotel_prices_async(
    self,
    hotel_id: str = None
):
    """
    Refresh hotel prices asynchronously.
    
    Args:
        hotel_id: Specific hotel ID to refresh (None for all hotels)
    
    Returns:
        dict: Refresh results
    """
    try:
        from ..scraping.hotel_data_collector import HotelDataCollector
        from auth_module.infrastructure.db.database import get_db
        
        db = next(get_db())
        collector = HotelDataCollector(db_session=db)
        
        if hotel_id:
            result = collector.refresh_hotel_prices(hotel_id)
        else:
            result = collector.refresh_all_hotel_prices()
        
        logger.info(f"Refreshed prices for {result.get('hotels_updated', 0)} hotels")
        return result
    except Exception as exc:
        logger.error(f"Failed to refresh hotel prices: {exc}")
        raise self.retry(exc=exc)

