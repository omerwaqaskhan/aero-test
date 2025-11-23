"""Script to check for duplicate hotels in the database and generate a report."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from auth_module.infrastructure.db.database import SessionLocal
from search_booking_module.infrastructure.db.models import HotelModel
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_duplicate_hotels():
    """Check for duplicate hotels and generate a report."""
    db: Session = SessionLocal()
    
    try:
        logger.info("Checking for duplicate hotels...")
        
        # Method 1: Duplicates by exact name and city
        logger.info("\n" + "="*80)
        logger.info("DUPLICATE HOTELS REPORT")
        logger.info("="*80)
        
        # Find duplicates by name and city
        duplicates_by_name = db.execute(
            text("""
                SELECT name, city, country, COUNT(*) as count, 
                       array_agg(id ORDER BY 
                           (CASE WHEN images IS NOT NULL THEN jsonb_array_length(images::jsonb) ELSE 0 END) DESC,
                           (CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) DESC,
                           (CASE WHEN property_overview IS NOT NULL THEN 1 ELSE 0 END) DESC,
                           updated_at DESC
                       ) as hotel_ids,
                       array_agg(provider_hotel_id ORDER BY updated_at DESC) as provider_ids,
                       array_agg(provider::text ORDER BY updated_at DESC) as providers
                FROM hotels
                GROUP BY name, city, country
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
        ).fetchall()
        
        logger.info(f"\n1. DUPLICATES BY EXACT NAME + CITY: {len(duplicates_by_name)} groups")
        logger.info("-" * 80)
        
        total_duplicates_by_name = 0
        for row in duplicates_by_name:
            name, city, country, count, hotel_ids, provider_ids, providers = row
            total_duplicates_by_name += (count - 1)  # Subtract 1 to get duplicate count
            logger.info(f"\n  Hotel: {name}")
            logger.info(f"  Location: {city}, {country}")
            logger.info(f"  Duplicate Count: {count} hotels")
            logger.info(f"  Hotel IDs: {', '.join([str(hid)[:8] + '...' for hid in hotel_ids])}")
            logger.info(f"  Provider IDs: {', '.join([str(pid) if pid else 'None' for pid in provider_ids])}")
            logger.info(f"  Providers: {', '.join([str(p) for p in providers])}")
        
        # Method 2: Duplicates by normalized name (similar names)
        logger.info(f"\n\n2. CHECKING FOR SIMILAR NAMES (Normalized)...")
        logger.info("-" * 80)
        
        # Get all hotels and check for similar normalized names
        all_hotels = db.query(HotelModel).all()
        
        def normalize_name(name):
            """Normalize hotel name for comparison."""
            if not name:
                return ""
            import re
            normalized = name.lower().strip()
            normalized = re.sub(r'\s*opens?\s*in\s*new\s*window\s*', '', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'[^\w\s-]', '', normalized)
            normalized = re.sub(r'[-\s]+', ' ', normalized)
            suffixes = [' hotel', ' resort', ' inn', ' lodge', ' suites', ' suite']
            for suffix in suffixes:
                if normalized.endswith(suffix):
                    normalized = normalized[:-len(suffix)]
            return normalized.strip()
        
        # Group by normalized name and city
        normalized_groups = {}
        for hotel in all_hotels:
            normalized = normalize_name(hotel.name)
            key = (normalized, hotel.city.lower())
            if key not in normalized_groups:
                normalized_groups[key] = []
            normalized_groups[key].append(hotel)
        
        similar_duplicates = {k: v for k, v in normalized_groups.items() if len(v) > 1}
        
        logger.info(f"  Found {len(similar_duplicates)} groups with similar normalized names")
        total_similar_duplicates = 0
        
        for (normalized_name, city), hotels in list(similar_duplicates.items())[:20]:  # Show first 20
            if len(hotels) > 1:
                total_similar_duplicates += (len(hotels) - 1)
                logger.info(f"\n  Normalized Name: '{normalized_name}'")
                logger.info(f"  City: {city}")
                logger.info(f"  Count: {len(hotels)} hotels")
                for hotel in hotels:
                    logger.info(f"    - {hotel.name} (ID: {str(hotel.id)[:8]}..., Provider: {hotel.provider}, Provider ID: {hotel.provider_hotel_id or 'None'})")
        
        if len(similar_duplicates) > 20:
            logger.info(f"\n  ... and {len(similar_duplicates) - 20} more groups")
        
        # Method 3: Duplicates by coordinates (same location) - but only if names are similar
        logger.info(f"\n\n3. CHECKING FOR DUPLICATES BY LOCATION + SIMILAR NAME...")
        logger.info("-" * 80)
        
        # Get all hotels with same coordinates
        location_groups = db.execute(
            text("""
                SELECT latitude, longitude, city, COUNT(*) as count,
                       array_agg(id ORDER BY updated_at DESC) as hotel_ids,
                       array_agg(name ORDER BY updated_at DESC) as hotel_names
                FROM hotels
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                GROUP BY latitude, longitude, city
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
        ).fetchall()
        
        # Check which ones have similar names (likely true duplicates)
        def normalize_name(name):
            """Normalize hotel name for comparison."""
            if not name:
                return ""
            import re
            normalized = name.lower().strip()
            normalized = re.sub(r'\s*opens?\s*in\s*new\s*window\s*', '', normalized, flags=re.IGNORECASE)
            normalized = re.sub(r'[^\w\s-]', '', normalized)
            normalized = re.sub(r'[-\s]+', ' ', normalized)
            return normalized.strip()
        
        true_location_duplicates = []
        city_center_fallbacks = []
        
        for row in location_groups:
            lat, lon, city, count, hotel_ids, hotel_names = row
            # Check if any hotels have similar names
            has_similar_names = False
            for i, name1 in enumerate(hotel_names):
                norm1 = normalize_name(name1)
                for j, name2 in enumerate(hotel_names[i+1:], i+1):
                    norm2 = normalize_name(name2)
                    if norm1 and norm2:
                        # Check similarity
                        if norm1 == norm2:
                            has_similar_names = True
                            break
                        shorter = min(len(norm1), len(norm2))
                        longer = max(len(norm1), len(norm2))
                        if shorter > 10 and longer > 0:
                            if norm1 in norm2 or norm2 in norm1:
                                if shorter / longer > 0.7:  # 70% similarity
                                    has_similar_names = True
                                    break
                if has_similar_names:
                    break
            
            if has_similar_names:
                true_location_duplicates.append(row)
            else:
                city_center_fallbacks.append(row)
        
        logger.info(f"  Found {len(true_location_duplicates)} locations with similar-named hotels (likely duplicates)")
        logger.info(f"  Found {len(city_center_fallbacks)} locations with different hotels (likely city center geocoding fallback)")
        
        total_location_duplicates = 0
        for row in true_location_duplicates[:10]:  # Show first 10
            lat, lon, city, count, hotel_ids, hotel_names = row
            total_location_duplicates += (count - 1)
            logger.info(f"\n  Location: ({lat}, {lon}) in {city}")
            logger.info(f"  Count: {count} hotels with similar names")
            for i, (hotel_id, hotel_name) in enumerate(zip(hotel_ids, hotel_names)):
                logger.info(f"    {i+1}. {hotel_name} (ID: {str(hotel_id)[:8]}...)")
        
        if len(true_location_duplicates) > 10:
            logger.info(f"\n  ... and {len(true_location_duplicates) - 10} more locations with similar-named hotels")
        
        if city_center_fallbacks:
            logger.info(f"\n  Note: {len(city_center_fallbacks)} locations have multiple different hotels.")
            logger.info(f"        These are likely city center coordinates used as fallback during geocoding.")
            logger.info(f"        They are NOT duplicates - just hotels in the same city.")
        
        # Method 4: Duplicates by provider_hotel_id (same provider ID)
        logger.info(f"\n\n4. CHECKING FOR DUPLICATES BY PROVIDER HOTEL ID...")
        logger.info("-" * 80)
        
        provider_id_duplicates = db.execute(
            text("""
                SELECT provider_hotel_id, provider::text, COUNT(*) as count,
                       array_agg(id ORDER BY updated_at DESC) as hotel_ids,
                       array_agg(name ORDER BY updated_at DESC) as hotel_names
                FROM hotels
                WHERE provider_hotel_id IS NOT NULL AND provider_hotel_id != ''
                GROUP BY provider_hotel_id, provider
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC
            """)
        ).fetchall()
        
        logger.info(f"  Found {len(provider_id_duplicates)} provider IDs with multiple hotels")
        total_provider_duplicates = 0
        
        for row in provider_id_duplicates[:20]:  # Show first 20
            provider_id, provider, count, hotel_ids, hotel_names = row
            total_provider_duplicates += (count - 1)
            logger.info(f"\n  Provider ID: {provider_id}")
            logger.info(f"  Provider: {provider}")
            logger.info(f"  Count: {count} hotels")
            for i, (hotel_id, hotel_name) in enumerate(zip(hotel_ids, hotel_names)):
                logger.info(f"    {i+1}. {hotel_name} (ID: {str(hotel_id)[:8]}...)")
        
        if len(provider_id_duplicates) > 20:
            logger.info(f"\n  ... and {len(provider_id_duplicates) - 20} more provider IDs")
        
        # Summary
        logger.info("\n\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Total hotels in database: {db.query(HotelModel).count()}")
        logger.info(f"\nDuplicate Groups Found:")
        logger.info(f"  1. By exact name + city: {len(duplicates_by_name)} groups ({total_duplicates_by_name} duplicate hotels)")
        logger.info(f"  2. By similar normalized name: {len(similar_duplicates)} groups ({total_similar_duplicates} duplicate hotels)")
        logger.info(f"  3. By same location + similar name: {len(true_location_duplicates)} groups ({total_location_duplicates} duplicate hotels)")
        logger.info(f"  4. By same provider_hotel_id: {len(provider_id_duplicates)} groups ({total_provider_duplicates} duplicate hotels)")
        logger.info(f"\n  Note: {len(city_center_fallbacks)} locations have multiple different hotels with same coordinates.")
        logger.info(f"        These are likely city center fallback coordinates, NOT duplicates.")
        
        # Calculate unique hotels (approximate)
        max_duplicates = max(
            total_duplicates_by_name,
            total_similar_duplicates,
            total_location_duplicates,
            total_provider_duplicates,
            0
        )
        unique_hotels = db.query(HotelModel).count() - max_duplicates
        logger.info(f"\nEstimated unique hotels: ~{unique_hotels} (out of {db.query(HotelModel).count()} total)")
        logger.info(f"Estimated duplicate hotels to remove: ~{max_duplicates}")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        db.close()


if __name__ == "__main__":
    check_duplicate_hotels()

