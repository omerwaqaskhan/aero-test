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
                    # Update hotel with new data
                    if details.get('description'):
                        hotel.description = details.get('description')
                    if details.get('property_overview'):
                        hotel.property_overview = details.get('property_overview')
                    if details.get('images'):
                        # Merge images
                        existing_images = hotel.images or []
                        new_images = details.get('images', [])
                        all_images = list(set(existing_images + new_images))
                        hotel.images = all_images[:50]
                    if details.get('amenities'):
                        hotel.amenities = details.get('amenities')
                    if details.get('policies'):
                        hotel.policies = details.get('policies')
                    
                    # Update rooms
                    rooms_data = details.get('rooms', [])
                    if rooms_data:
                        logger.info(f"Found {len(rooms_data)} rooms for {hotel.name}")
                        # Delete old rooms
                        db.query(RoomModel).filter(RoomModel.hotel_id == hotel.id).delete()
                        # Save new rooms
                        await collector._save_real_rooms(hotel, rooms_data)
                    
                    # Update reviews
                    reviews_data = details.get('reviews', [])
                    if reviews_data:
                        logger.info(f"Found {len(reviews_data)} reviews for {hotel.name}")
                        # Add new reviews (don't delete old ones)
                        await collector._save_real_reviews(hotel, reviews_data)
                    
                    db.commit()
                    logger.info(f"✓ Successfully updated {hotel.name}")
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

