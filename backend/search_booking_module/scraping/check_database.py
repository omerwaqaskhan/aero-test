"""Script to check if database tables are populated."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.orm import Session
from auth_module.infrastructure.db.database import SessionLocal
from search_booking_module.infrastructure.db.models import (
    HotelModel, OfferModel, RoomModel, ReviewModel, BookingClickModel
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database():
    """Check if database tables are populated."""
    db: Session = SessionLocal()
    
    try:
        # Check hotels
        hotel_count = db.query(HotelModel).count()
        
        # Check offers
        offer_count = db.query(OfferModel).count()
        
        # Check rooms
        room_count = db.query(RoomModel).count()
        
        # Check reviews
        review_count = db.query(ReviewModel).count()
        
        # Check booking clicks
        booking_click_count = db.query(BookingClickModel).count()
        
        # Get hotels by city
        hotels_by_city = db.query(
            HotelModel.city,
            HotelModel.country,
            db.func.count(HotelModel.id).label('count')
        ).group_by(
            HotelModel.city,
            HotelModel.country
        ).all()
        
        # Get hotels by provider
        hotels_by_provider = db.query(
            HotelModel.provider,
            db.func.count(HotelModel.id).label('count')
        ).group_by(HotelModel.provider).all()
        
        # Print results
        print("\n" + "="*60)
        print("DATABASE STATUS CHECK")
        print("="*60)
        
        print(f"\n📊 Table Counts:")
        print(f"  Hotels:      {hotel_count}")
        print(f"  Offers:      {offer_count}")
        print(f"  Rooms:       {room_count}")
        print(f"  Reviews:     {review_count}")
        print(f"  Booking Clicks: {booking_click_count}")
        
        if hotel_count > 0:
            print(f"\n📍 Hotels by City:")
            for city, country, count in hotels_by_city:
                print(f"  {city}, {country}: {count} hotels")
            
            print(f"\n🏢 Hotels by Provider:")
            for provider, count in hotels_by_provider:
                print(f"  {provider.value}: {count} hotels")
            
            # Sample hotels
            print(f"\n🏨 Sample Hotels (first 5):")
            sample_hotels = db.query(HotelModel).limit(5).all()
            for hotel in sample_hotels:
                print(f"  - {hotel.name} ({hotel.city}, {hotel.country})")
                print(f"    Stars: {hotel.stars}, Rating: {hotel.rating or 'N/A'}")
                print(f"    Provider: {hotel.provider.value}")
                print()
        else:
            print("\n⚠️  Database is empty. No hotels found.")
            print("   The scheduler should populate it automatically on startup.")
            print("   Or run: python -m search_booking_module.scraping.populate_database")
        
        print("="*60)
        
        return {
            'hotels': hotel_count,
            'offers': offer_count,
            'rooms': room_count,
            'reviews': review_count,
            'booking_clicks': booking_click_count,
            'is_populated': hotel_count > 0
        }
        
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        print(f"\n❌ Error checking database: {e}")
        return None
    finally:
        db.close()


if __name__ == "__main__":
    result = check_database()
    if result:
        sys.exit(0 if result['is_populated'] else 1)

