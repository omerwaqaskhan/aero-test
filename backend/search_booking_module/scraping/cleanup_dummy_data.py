"""Script to clean up dummy and duplicate data from the database."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
from auth_module.infrastructure.db.database import SessionLocal
from search_booking_module.infrastructure.db.models import (
    HotelModel, RoomModel, OfferModel, ReviewModel
)
from search_booking_module.domain.models import Provider
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_dummy_and_duplicate_data():
    """Remove dummy and duplicate data from the database."""
    db: Session = SessionLocal()
    
    try:
        logger.info("Starting cleanup of dummy and duplicate data...")
        
        # 1. Remove dummy offers (those with "default_" prefix in provider_rate_id)
        logger.info("Removing dummy offers...")
        dummy_offers = db.query(OfferModel).filter(
            OfferModel.provider_rate_id.like('default_%')
        ).all()
        dummy_offer_count = len(dummy_offers)
        for offer in dummy_offers:
            db.delete(offer)
        db.commit()
        logger.info(f"  ✓ Removed {dummy_offer_count} dummy offers")
        
        # 2. Remove dummy rooms (those with default descriptions or default amenities)
        logger.info("Removing dummy rooms...")
        # Use raw SQL to find dummy rooms
        dummy_room_ids = db.execute(
            text("""
                SELECT id FROM rooms 
                WHERE LOWER(description) LIKE '%comfortable%with modern amenities%'
                   OR LOWER(description) LIKE '%standard room with%'
                   OR LOWER(description) LIKE '%default room%'
                   OR (amenities::jsonb = '["WiFi", "TV", "Air conditioning", "Private bathroom"]'::jsonb
                       AND occupancy::jsonb->>'size' IN ('18', '20', '25')
                       AND occupancy::jsonb->>'max_guests' IN ('2', '3'))
            """)
        ).fetchall()
        
        dummy_room_count = 0
        for row in dummy_room_ids:
            room_id = row[0]
            # Delete associated offers first
            db.execute(text("DELETE FROM offers WHERE room_id = :room_id"), {"room_id": room_id})
            db.execute(text("DELETE FROM rooms WHERE id = :room_id"), {"room_id": room_id})
            dummy_room_count += 1
        
        db.commit()
        logger.info(f"  ✓ Removed {dummy_room_count} dummy rooms")
        
        # 3. Remove test hotels (use raw SQL to avoid enum issues)
        logger.info("Removing test hotels...")
        test_hotel_ids = db.execute(
            text("SELECT id FROM hotels WHERE LOWER(name) LIKE '%test%' OR LOWER(name) LIKE '%dummy%' OR LOWER(name) LIKE '%example%'")
        ).fetchall()
        test_hotel_count = 0
        for row in test_hotel_ids:
            hotel_id = row[0]
            # Delete associated data
            db.execute(text("DELETE FROM offers WHERE hotel_id = :hotel_id"), {"hotel_id": hotel_id})
            db.execute(text("DELETE FROM rooms WHERE hotel_id = :hotel_id"), {"hotel_id": hotel_id})
            db.execute(text("DELETE FROM reviews WHERE hotel_id = :hotel_id"), {"hotel_id": hotel_id})
            db.execute(text("DELETE FROM hotels WHERE id = :hotel_id"), {"hotel_id": hotel_id})
            test_hotel_count += 1
        db.commit()
        logger.info(f"  ✓ Removed {test_hotel_count} test hotels")
        
        # 4. Fix hotels with invalid provider values
        logger.info("Fixing hotels with invalid provider values...")
        invalid_providers = ['test', 'TEST', 'Test', 'unknown', 'UNKNOWN']
        fixed_count = 0
        for provider_str in invalid_providers:
            # Use raw SQL to update provider values
            result = db.execute(
                text("UPDATE hotels SET provider = 'BOOKING_COM' WHERE provider::text = :provider_val"),
                {"provider_val": provider_str}
            )
            fixed_count += result.rowcount
        db.commit()
        logger.info(f"  ✓ Fixed {fixed_count} hotels with invalid provider values")
        
        # 5. Remove duplicate hotels (same name and city, keep the one with most data)
        logger.info("Removing duplicate hotels...")
        # Find duplicates using raw SQL to avoid enum issues
        duplicates = db.execute(
            text("""
                SELECT name, city, COUNT(*) as count, array_agg(id ORDER BY 
                    (CASE WHEN images IS NOT NULL THEN jsonb_array_length(images::jsonb) ELSE 0 END) DESC,
                    (CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) DESC,
                    (CASE WHEN property_overview IS NOT NULL THEN 1 ELSE 0 END) DESC,
                    updated_at DESC
                ) as hotel_ids
                FROM hotels
                GROUP BY name, city
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        
        duplicate_hotel_count = 0
        for row in duplicates:
            name, city, count, hotel_ids = row
            if len(hotel_ids) > 1:
                # Keep the first one (already sorted by data richness), delete the rest
                for hotel_id in hotel_ids[1:]:
                    # Delete associated data
                    db.execute(text("DELETE FROM offers WHERE hotel_id = :hotel_id"), {"hotel_id": hotel_id})
                    db.execute(text("DELETE FROM rooms WHERE hotel_id = :hotel_id"), {"hotel_id": hotel_id})
                    db.execute(text("DELETE FROM reviews WHERE hotel_id = :hotel_id"), {"hotel_id": hotel_id})
                    db.execute(text("DELETE FROM hotels WHERE id = :hotel_id"), {"hotel_id": hotel_id})
                    duplicate_hotel_count += 1
        
        db.commit()
        logger.info(f"  ✓ Removed {duplicate_hotel_count} duplicate hotels")
        
        # 6. Remove duplicate rooms (same hotel_id and room_type_name, keep the one with most data)
        logger.info("Removing duplicate rooms...")
        # Use raw SQL to find duplicates
        duplicate_rooms_query = db.execute(
            text("""
                SELECT hotel_id, LOWER(room_type_name) as room_type_lower, 
                       COUNT(*) as count,
                       array_agg(id ORDER BY 
                           (CASE WHEN images IS NOT NULL THEN jsonb_array_length(images::jsonb) ELSE 0 END) DESC,
                           (CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) DESC,
                           updated_at DESC
                       ) as room_ids
                FROM rooms
                GROUP BY hotel_id, LOWER(room_type_name)
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        
        duplicate_room_count = 0
        for row in duplicate_rooms_query:
            hotel_id, room_type_lower, count, room_ids = row
            if len(room_ids) > 1:
                # Keep the first one, delete the rest
                for room_id in room_ids[1:]:
                    # Delete associated offers
                    db.execute(text("DELETE FROM offers WHERE room_id = :room_id"), {"room_id": room_id})
                    db.execute(text("DELETE FROM rooms WHERE id = :room_id"), {"room_id": room_id})
                    duplicate_room_count += 1
        
        db.commit()
        logger.info(f"  ✓ Removed {duplicate_room_count} duplicate rooms")
        
        # 7. Remove duplicate offers (same hotel_id, room_id, provider, check_in, check_out)
        logger.info("Removing duplicate offers...")
        # Use raw SQL to find duplicates
        duplicate_offers_query = db.execute(
            text("""
                SELECT hotel_id, room_id, provider::text, check_in, check_out, COUNT(*) as count,
                       array_agg(id ORDER BY id DESC) as offer_ids
                FROM offers
                GROUP BY hotel_id, room_id, provider, check_in, check_out
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        
        duplicate_offer_count = 0
        for row in duplicate_offers_query:
            hotel_id, room_id, provider, check_in, check_out, count, offer_ids = row
            if len(offer_ids) > 1:
                # Keep the first one (most recent), delete the rest
                for offer_id in offer_ids[1:]:
                    db.execute(text("DELETE FROM offers WHERE id = :offer_id"), {"offer_id": offer_id})
                    duplicate_offer_count += 1
        
        db.commit()
        logger.info(f"  ✓ Removed {duplicate_offer_count} duplicate offers")
        
        # 8. Remove rooms without any offers (optional - comment out if you want to keep rooms without offers)
        logger.info("Removing rooms without offers (optional cleanup)...")
        orphan_room_ids = db.execute(
            text("""
                SELECT r.id FROM rooms r
                LEFT JOIN offers o ON r.id = o.room_id
                WHERE o.id IS NULL
            """)
        ).fetchall()
        
        orphan_room_count = 0
        for row in orphan_room_ids:
            room_id = row[0]
            db.execute(text("DELETE FROM rooms WHERE id = :room_id"), {"room_id": room_id})
            orphan_room_count += 1
        
        db.commit()
        logger.info(f"  ✓ Removed {orphan_room_count} rooms without offers")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("CLEANUP SUMMARY")
        logger.info("="*60)
        logger.info(f"  Dummy offers removed:     {dummy_offer_count}")
        logger.info(f"  Dummy rooms removed:      {dummy_room_count}")
        logger.info(f"  Test hotels removed:      {test_hotel_count}")
        logger.info(f"  Invalid providers fixed: {fixed_count}")
        logger.info(f"  Duplicate hotels removed: {duplicate_hotel_count}")
        logger.info(f"  Duplicate rooms removed:  {duplicate_room_count}")
        logger.info(f"  Duplicate offers removed: {duplicate_offer_count}")
        logger.info(f"  Orphan rooms removed:     {orphan_room_count}")
        logger.info("="*60)
        logger.info("Cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cleanup_dummy_and_duplicate_data()

