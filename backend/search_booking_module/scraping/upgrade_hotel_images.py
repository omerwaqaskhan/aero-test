"""Script to upgrade existing hotel images to high quality."""

import sys
import os
import re
import asyncio
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from auth_module.infrastructure.db.database import SessionLocal
from search_booking_module.infrastructure.db.models import HotelModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade_image_url(url: str) -> str:
    """Upgrade image URL to high quality."""
    if not url or not isinstance(url, str):
        return url
    
    original_url = url
    
    try:
        # Upgrade Booking.com images
        if 'bstatic.com' in url:
            # Replace max300, max500, etc. with max1920x1080
            url = re.sub(r'/max\d+x?\d*/', '/max1920x1080/', url)
            url = re.sub(r'/square\d+/', '/max1920x1080/', url)
            url = re.sub(r'/max\d+/', '/max1920x1080/', url)
            
            # Clean query string - keep only hash parameter
            if '?' in url:
                base_url, query = url.split('?', 1)
                params = query.split('&')
                hash_param = [p for p in params if p.startswith('k=')]
                if hash_param:
                    url = f"{base_url}?{hash_param[0]}"
        
        # Upgrade Expedia images
        elif 'expedia.com' in url or 'media.expedia.com' in url:
            url = re.sub(r'[?&]w=\d+', '?w=1920', url)
            url = re.sub(r'[?&]h=\d+', '&h=1080', url)
            if '?' not in url:
                url += '?w=1920&h=1080'
            elif 'w=' not in url:
                url += '&w=1920&h=1080'
        
        # Upgrade Hotels.com images
        elif 'hotels.com' in url or 'media.hotels.com' in url:
            url = re.sub(r'[?&]size=\w+', '?size=large', url)
            if '?' not in url:
                url += '?size=large'
            elif 'size=' not in url:
                url += '&size=large'
        
        # Upgrade Agoda images
        elif 'agoda.net' in url or 'agoda.com' in url:
            url = re.sub(r'[?&]s=\w+', '?s=1920x1080', url)
            if '?' not in url:
                url += '?s=1920x1080'
            elif 's=' not in url:
                url += '&s=1920x1080'
        
        if url != original_url:
            logger.debug(f"Upgraded: {original_url[:80]}... -> {url[:80]}...")
        
        return url
    except Exception as e:
        logger.warning(f"Error upgrading image URL {url[:80]}: {e}")
        return original_url


def upgrade_hotel_images():
    """Upgrade all hotel images in database to high quality."""
    db: Session = SessionLocal()
    try:
        hotels = db.query(HotelModel).all()
        logger.info(f"Found {len(hotels)} hotels to upgrade")
        
        upgraded_count = 0
        for hotel in hotels:
            if not hotel.images:
                continue
            
            original_images = hotel.images.copy() if isinstance(hotel.images, list) else []
            upgraded_images = []
            changed = False
            
            for img_url in original_images:
                upgraded_url = upgrade_image_url(img_url)
                upgraded_images.append(upgraded_url)
                if upgraded_url != img_url:
                    changed = True
            
            if changed:
                hotel.images = upgraded_images
                upgraded_count += 1
                logger.info(f"Upgraded images for: {hotel.name}")
        
        if upgraded_count > 0:
            db.commit()
            logger.info(f"✓ Successfully upgraded images for {upgraded_count} hotels")
        else:
            logger.info("No hotels needed image upgrades")
        
    except Exception as e:
        logger.error(f"Error upgrading hotel images: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Hotel Image Quality Upgrade Script")
    print("=" * 60)
    print()
    
    try:
        upgrade_hotel_images()
        print()
        print("=" * 60)
        print("✓ Image upgrade completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

