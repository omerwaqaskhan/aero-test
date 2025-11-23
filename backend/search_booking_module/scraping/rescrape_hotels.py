"""Script to re-scrape existing hotels to get real room and review data."""

import asyncio
import logging
from sqlalchemy.orm import Session
from auth_module.infrastructure.db.database import SessionLocal
from search_booking_module.infrastructure.db.models import HotelModel, RoomModel, ReviewModel
from search_booking_module.scraping.data_collector import HotelDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def rescrape_hotels(limit: int = None, hotel_ids: list = None):
    """Re-scrape existing hotels to get real room and review data.
    
    Args:
        limit: Maximum number of hotels to re-scrape (None for all)
        hotel_ids: Specific hotel IDs to re-scrape (None for all)
    """
    db: Session = SessionLocal()
    try:
        collector = HotelDataCollector(db_session=db, use_enhanced_scraping=True)
        
        # Get hotels to re-scrape
        query = db.query(HotelModel)
        
        if hotel_ids:
            query = query.filter(HotelModel.id.in_(hotel_ids))
        
        hotels = query.all()
        
        if limit:
            hotels = hotels[:limit]
        
        logger.info(f"Re-scraping {len(hotels)} hotels...")
        
        for i, hotel in enumerate(hotels, 1):
            try:
                logger.info(f"[{i}/{len(hotels)}] Re-scraping {hotel.name}...")
                
                if not hotel.source_url:
                    logger.warning(f"No source URL for {hotel.name}, skipping")
                    continue
                
                # Get enhanced scraper
                enhanced_scraper = None
                for scraper in collector.scrapers:
                    if hasattr(scraper, 'get_hotel_details'):
                        enhanced_scraper = scraper
                        break
                
                if not enhanced_scraper:
                    logger.error("Enhanced scraper not available")
                    break
                
                # Fetch detailed information
                try:
                    async with enhanced_scraper:
                        details = await enhanced_scraper.get_hotel_details(hotel.source_url)
                except Exception as e:
                    logger.error(f"Error accessing enhanced scraper for {hotel.name}: {e}")
                    details = None
                
                if details:
                    # Prepare hotel data in the format expected by _save_hotel
                    hotel_data = {
                        'name': hotel.name,
                        'source': 'booking.com',  # Default, will be updated if available
                        'source_url': hotel.source_url,
                        'description': details.get('description', ''),
                        'property_overview': details.get('property_overview', ''),
                        'images': details.get('images', []),
                        'amenities': details.get('amenities', []),
                        'policies': details.get('policies', {}),
                        'rooms_data': details.get('rooms', []),
                        'reviews_data': details.get('reviews', []),
                    }
                    
                    # Use the same update logic as in _save_hotel to ensure consistency
                    # This will properly handle updates, deduplication, and only update when data changes
                    updated = await collector._save_hotel(hotel_data, hotel.city, hotel.country)
                    
                    # Commit the transaction
                    db.commit()
                    
                    if updated:
                        logger.info(f"✓ Successfully updated {hotel.name} with {len(details.get('rooms', []))} rooms, {len(details.get('reviews', []))} reviews, {len(details.get('amenities', []))} amenities")
                    else:
                        logger.warning(f"Failed to update {hotel.name}")
                else:
                    logger.warning(f"No details found for {hotel.name}")
                
                # Delay between hotels
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error re-scraping {hotel.name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                db.rollback()
                continue
        
        logger.info("Re-scraping completed!")
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    limit = None
    hotel_ids = None
    
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            limit = int(sys.argv[1])
        else:
            hotel_ids = sys.argv[1].split(',')
    
    asyncio.run(rescrape_hotels(limit=limit, hotel_ids=hotel_ids))

