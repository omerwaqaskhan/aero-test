"""Simple test script for search-booking API endpoints."""

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from search_booking_module.domain.models import SearchFilters, Provider
from search_booking_module.domain.services import SearchService, BookingService
from search_booking_module.infrastructure.providers.booking_com import BookingComProvider
from search_booking_module.infrastructure.providers.expedia import ExpediaProvider
from search_booking_module.infrastructure.db.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


async def test_search_service():
    """Test search service functionality."""
    print("=" * 60)
    print("Testing Search Service")
    print("=" * 60)
    
    # Create mock providers
    providers = [
        BookingComProvider(api_key="test_key"),
        ExpediaProvider(api_key="test_key")
    ]
    
    # Create in-memory database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Create search service
        search_service = SearchService(providers=providers, db_session=db)
        
        # Create search filters
        check_in = date.today() + timedelta(days=7)
        check_out = check_in + timedelta(days=2)
        
        filters = SearchFilters(
            destination="New York",
            check_in=check_in,
            check_out=check_out,
            guests=2,
            rooms=1,
            min_price=50.0,
            max_price=200.0
        )
        
        print(f"\nSearching for hotels in {filters.destination}")
        print(f"Check-in: {filters.check_in}, Check-out: {filters.check_out}")
        print(f"Guests: {filters.guests}, Rooms: {filters.rooms}")
        print(f"Price range: ${filters.min_price} - ${filters.max_price}")
        
        # Perform search
        results = await search_service.search_hotels(
            filters=filters,
            sort_by="price",
            sort_order="asc",
            page=1,
            page_size=10
        )
        
        print(f"\nFound {len(results)} results:")
        print("-" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.hotel.name}")
            print(f"   Provider: {result.hotel.provider.value}")
            print(f"   Location: {result.hotel.city}, {result.hotel.country}")
            print(f"   Stars: {'⭐' * result.hotel.stars}")
            print(f"   Best Price: ${result.best_price:.2f}/night" if result.best_price else "   No offers available")
            print(f"   Offers: {len(result.offers)}")
            if result.offers:
                print(f"   Lowest: ${min(o.price for o in result.offers):.2f}/night")
                print(f"   Highest: ${max(o.price for o in result.offers):.2f}/night")
        
        print("\n" + "=" * 60)
        print("✅ Search service test passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def test_providers():
    """Test provider adapters."""
    print("\n" + "=" * 60)
    print("Testing Provider Adapters")
    print("=" * 60)
    
    providers = [
        BookingComProvider(api_key="test_key"),
        ExpediaProvider(api_key="test_key")
    ]
    
    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=2)
    
    for provider in providers:
        print(f"\nTesting {provider.provider_name}...")
        try:
            # Test search
            hotels = await provider.search_hotels(
                destination="New York",
                check_in=check_in,
                check_out=check_out,
                guests=2,
                rooms=1
            )
            print(f"  ✅ Found {len(hotels)} hotels")
            
            if hotels:
                # Test hotel details
                hotel = await provider.get_hotel_details(
                    provider_hotel_id=hotels[0].provider_hotel_id,
                    check_in=check_in,
                    check_out=check_out
                )
                print(f"  ✅ Hotel details retrieved: {hotel.name}")
                
                # Test offers
                offers = await provider.get_offers(
                    provider_hotel_id=hotels[0].provider_hotel_id,
                    check_in=check_in,
                    check_out=check_out,
                    guests=2,
                    rooms=1
                )
                print(f"  ✅ Found {len(offers)} offers")
                
                if offers:
                    # Test affiliate link
                    link = provider.generate_affiliate_link(
                        provider_hotel_id=hotels[0].provider_hotel_id,
                        check_in=check_in,
                        check_out=check_out,
                        guests=2,
                        rooms=1
                    )
                    print(f"  ✅ Affiliate link generated: {link[:50]}...")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Provider adapter tests completed!")


async def main():
    """Run all tests."""
    print("\n🚀 Starting Search-Booking Module Tests\n")
    
    await test_providers()
    await test_search_service()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

