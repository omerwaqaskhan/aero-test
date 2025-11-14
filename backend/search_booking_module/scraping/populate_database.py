"""Script to populate database with hotel data from web scraping."""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.orm import Session
from auth_module.infrastructure.db.database import SessionLocal, engine, Base
from search_booking_module.scraping.data_collector import HotelDataCollector
from search_booking_module.infrastructure.db.models import HotelModel
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Popular destinations to collect
POPULAR_DESTINATIONS = [
    {"city": "New York", "country": "USA"},
    {"city": "Paris", "country": "France"},
    {"city": "London", "country": "UK"},
    {"city": "Tokyo", "country": "Japan"},
    {"city": "Dubai", "country": "UAE"},
    {"city": "Barcelona", "country": "Spain"},
    {"city": "Rome", "country": "Italy"},
    {"city": "Amsterdam", "country": "Netherlands"},
    {"city": "Bangkok", "country": "Thailand"},
    {"city": "Singapore", "country": "Singapore"},
    {"city": "Sydney", "country": "Australia"},
    {"city": "Los Angeles", "country": "USA"},
    {"city": "Berlin", "country": "Germany"},
    {"city": "Vienna", "country": "Austria"},
    {"city": "Prague", "country": "Czech Republic"},
    {"city": "Istanbul", "country": "Turkey"},
    {"city": "Cairo", "country": "Egypt"},
    {"city": "Mumbai", "country": "India"},
    {"city": "Shanghai", "country": "China"},
    {"city": "Hong Kong", "country": "China"},
]


async def populate_database(destinations: list = None, max_hotels_per_destination: int = 50):
    """Populate database with hotel data.
    
    Args:
        destinations: List of dicts with 'city' and 'country' keys. If None, uses popular destinations.
        max_hotels_per_destination: Maximum number of hotels to collect per destination
    """
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db: Session = SessionLocal()
    
    try:
        # Create data collector with concurrent scraping (uses config defaults)
        collector = HotelDataCollector(
            db_session=db,
            use_enhanced_scraping=True
        )
        
        # Start concurrent scraper
        await collector.start()
        logger.info("Concurrent scraper started")
        
        try:
            # Use provided destinations or default
            if destinations is None:
                destinations = POPULAR_DESTINATIONS
            
            logger.info(f"Starting data collection for {len(destinations)} destinations...")
            
            # Collect hotels for each destination
            results = {}
            for dest in destinations:
                city = dest.get('city')
                country = dest.get('country')
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Collecting hotels for {city}, {country}")
                logger.info(f"{'='*60}")
                
                try:
                    count = await collector.collect_hotels_for_destination(
                        destination=city,
                        country=country,
                        max_hotels=max_hotels_per_destination
                    )
                    results[f"{city}, {country}"] = count
                    logger.info(f"✓ Collected {count} hotels for {city}, {country}")
                except Exception as e:
                    logger.error(f"✗ Error collecting hotels for {city}, {country}: {e}")
                    results[f"{city}, {country}"] = 0
                    continue
                
                # Delay between destinations
                await asyncio.sleep(3)
            
            # Summary
            logger.info(f"\n{'='*60}")
            logger.info("Data Collection Summary")
            logger.info(f"{'='*60}")
            total_hotels = sum(results.values())
            logger.info(f"Total hotels collected: {total_hotels}")
            logger.info(f"\nPer destination:")
            for dest, count in results.items():
                logger.info(f"  {dest}: {count} hotels")
        
            # Verify in database
            total_in_db = db.query(HotelModel).count()
            logger.info(f"\nTotal hotels in database: {total_in_db}")
            
            # Print scraper statistics
            stats = collector.concurrent_scraper.get_stats()
            logger.info(f"\n{'='*60}")
            logger.info("Scraper Statistics")
            logger.info(f"{'='*60}")
            logger.info(f"Total tasks: {stats['total_tasks']}")
            logger.info(f"Completed: {stats['completed_tasks']}")
            logger.info(f"Failed: {stats['failed_tasks']}")
            logger.info(f"Retried: {stats['retried_tasks']}")
            logger.info(f"Success rate: {stats['success_rate']:.2%}")
            logger.info(f"Average task time: {stats['avg_task_time']:.2f}s")
            
        finally:
            # Stop concurrent scraper
            await collector.stop()
            logger.info("Concurrent scraper stopped")
        
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate database with hotel data')
    parser.add_argument(
        '--destinations',
        type=str,
        nargs='+',
        help='List of destinations (format: "City,Country")',
        default=None
    )
    parser.add_argument(
        '--max-hotels',
        type=int,
        default=50,
        help='Maximum hotels per destination (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Parse destinations if provided
    destinations = None
    if args.destinations:
        destinations = []
        for dest in args.destinations:
            parts = dest.split(',')
            if len(parts) == 2:
                destinations.append({
                    'city': parts[0].strip(),
                    'country': parts[1].strip()
                })
            else:
                logger.warning(f"Invalid destination format: {dest}. Expected 'City,Country'")
    
    await populate_database(destinations=destinations, max_hotels_per_destination=args.max_hotels)


if __name__ == "__main__":
    asyncio.run(main())

