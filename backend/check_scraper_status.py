"""Quick script to check scraping status."""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_module.infrastructure.db.database import SessionLocal
from search_booking_module.infrastructure.db.models import HotelModel, RoomModel, ReviewModel
from sqlalchemy import func

PROGRESS_FILE = "/tmp/scraper_progress.json"

def check_status():
    """Check current scraping status."""
    print("\n" + "="*80)
    print("📊 SCRAPER STATUS CHECK")
    print("="*80)
    
    # Check progress file
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            
            print(f"\n🔄 SCRAPER PROGRESS:")
            print(f"   Hotels Scraped: {progress.get('hotels_scraped', 0)}")
            print(f"   Destinations Completed: {len(progress.get('destinations_completed', []))}")
            if progress.get('destinations_completed'):
                print(f"   Completed: {', '.join(progress['destinations_completed'])}")
            print(f"   Last Destination: {progress.get('last_destination', 'None')}")
            print(f"   Hotels Failed: {len(progress.get('hotels_failed', []))}")
            print(f"   Updated: {progress.get('updated_at', 'Unknown')}")
        except Exception as e:
            print(f"   ⚠️  Could not read progress file: {e}")
    else:
        print("\n⚠️  No progress file found (scraper not started or completed)")
    
    # Check database
    db = SessionLocal()
    try:
        total_hotels = db.query(HotelModel).count()
        total_rooms = db.query(RoomModel).count()
        total_reviews = db.query(ReviewModel).count()
        
        # Hotels with rooms
        hotels_with_rooms = db.query(HotelModel).join(RoomModel).distinct().count()
        
        # Hotels with reviews
        hotels_with_reviews = db.query(HotelModel).join(ReviewModel).distinct().count()
        
        # Recent hotels (last 10)
        recent_hotels = db.query(HotelModel).order_by(HotelModel.created_at.desc()).limit(10).all()
        
        print(f"\n💾 DATABASE STATUS:")
        print(f"   Total Hotels: {total_hotels}")
        print(f"   Total Rooms: {total_rooms}")
        print(f"   Total Reviews: {total_reviews}")
        print(f"   Hotels with Rooms: {hotels_with_rooms}")
        print(f"   Hotels with Reviews: {hotels_with_reviews}")
        
        if recent_hotels:
            print(f"\n📋 RECENTLY ADDED HOTELS:")
            for i, hotel in enumerate(recent_hotels[:5], 1):
                rooms = db.query(RoomModel).filter(RoomModel.hotel_id == hotel.id).count()
                reviews = db.query(ReviewModel).filter(ReviewModel.hotel_id == hotel.id).count()
                print(f"   {i}. {hotel.name} ({hotel.city}) - {rooms} rooms, {reviews} reviews")
        
    finally:
        db.close()
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_status()

