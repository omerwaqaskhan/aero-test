"""
Simple hotel data populator - manually add high-quality hotel data to bootstrap the platform.
This bypasses anti-bot issues by using a curated list of real hotels.
"""
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_module.infrastructure.db.database import SessionLocal
from search_booking_module.infrastructure.db.models import HotelModel, RoomModel, ReviewModel
from expanded_hotels_data import EXPANDED_HOTELS
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use expanded hotel dataset
HOTELS_DATA = EXPANDED_HOTELS

# Keep old smaller dataset as backup
HOTELS_DATA_ORIGINAL = [
    # London Hotels
    {
        "name": "The Savoy London",
        "city": "London",
        "country": "United Kingdom",
        "latitude": 51.5102,
        "longitude": -0.1206,
        "description": "An iconic luxury hotel on the Strand featuring Art Deco decor, river views, and world-class dining.",
        "address": "Strand, London WC2R 0EU",
        "star_rating": 5.0,
        "amenities": ["Wi-Fi", "Restaurant", "Bar", "Spa", "Gym", "Pool", "Room Service", "Concierge", "Parking"],
        "images": [
            "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200",
            "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=1200"
        ],
        "rooms": [
            {"type": "Deluxe Room", "price": 450.00, "beds": "King", "max_guests": 2},
            {"type": "River View Suite", "price": 750.00, "beds": "King", "max_guests": 3},
            {"type": "Royal Suite", "price": 1500.00, "beds": "2 Kings", "max_guests": 4}
        ],
        "reviews": [
            {"rating": 9.5, "text": "Absolutely stunning hotel with impeccable service. The afternoon tea was unforgettable!", "author": "Sarah M."},
            {"rating": 9.0, "text": "Perfect location, beautiful rooms, and fantastic staff. Worth every penny.", "author": "John D."},
            {"rating": 9.8, "text": "The pinnacle of luxury. Every detail was perfect.", "author": "Emma W."}
        ]
    },
    {
        "name": "Citizen M Tower of London",
        "city": "London",
        "country": "United Kingdom",
        "latitude": 51.5081,
        "longitude": -0.0759,
        "description": "Modern budget-luxury hotel near Tower of London with stylish rooms and great rooftop bar.",
        "address": "40 Trinity Square, London EC3N 4DJ",
        "star_rating": 4.0,
        "amenities": ["Wi-Fi", "Bar", "24-hour Front Desk", "Luggage Storage"],
        "images": [
            "https://images.unsplash.com/photo-1563911302283-d2bc129e7570?w=1200"
        ],
        "rooms": [
            {"type": "Standard Room", "price": 150.00, "beds": "Queen", "max_guests": 2},
            {"type": "XL Room", "price": 200.00, "beds": "King", "max_guests": 2}
        ],
        "reviews": [
            {"rating": 8.5, "text": "Great value for money! Modern, clean, and perfectly located.", "author": "Mike R."},
            {"rating": 8.0, "text": "Love the rooftop bar. Rooms are compact but well-designed.", "author": "Lisa K."}
        ]
    },
    # Tokyo Hotels
    {
        "name": "Park Hyatt Tokyo",
        "city": "Tokyo",
        "country": "Japan",
        "latitude": 35.6850,
        "longitude": 139.6916,
        "description": "Luxury hotel in Shinjuku with stunning city views, featured in Lost in Translation. Renowned for its New York Bar.",
        "address": "3-7-1-2 Nishi-Shinjuku, Shinjuku-ku, Tokyo 163-1055",
        "star_rating": 5.0,
        "amenities": ["Wi-Fi", "Restaurant", "Bar", "Spa", "Gym", "Pool", "Room Service", "Concierge"],
        "images": [
            "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1200",
            "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=1200"
        ],
        "rooms": [
            {"type": "Park Deluxe", "price": 600.00, "beds": "King", "max_guests": 2},
            {"type": "Park Suite", "price": 1200.00, "beds": "King", "max_guests": 3},
            {"type": "Presidential Suite", "price": 3000.00, "beds": "King + Twin", "max_guests": 4}
        ],
        "reviews": [
            {"rating": 9.7, "text": "Breathtaking views and exceptional service. The New York Bar is a must-visit!", "author": "David L."},
            {"rating": 9.5, "text": "Perfect blend of Japanese hospitality and international luxury.", "author": "Yuki S."},
            {"rating": 9.8, "text": "Simply the best hotel in Tokyo. Every moment was special.", "author": "Robert M."}
        ]
    },
    {
        "name": "The Millennials Shibuya",
        "city": "Tokyo",
        "country": "Japan",
        "latitude": 35.6595,
        "longitude": 139.7004,
        "description": "Modern capsule hotel in Shibuya with smart pods, co-working space, and vibrant social atmosphere.",
        "address": "1-20-13 Jinnan, Shibuya-ku, Tokyo 150-0041",
        "star_rating": 3.0,
        "amenities": ["Wi-Fi", "Co-working Space", "Lockers", "Shared Lounge"],
        "images": [
            "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=1200"
        ],
        "rooms": [
            {"type": "Smart Pod", "price": 45.00, "beds": "Single", "max_guests": 1},
            {"type": "Premium Pod", "price": 60.00, "beds": "Single", "max_guests": 1}
        ],
        "reviews": [
            {"rating": 8.2, "text": "Great for solo travelers! Clean, modern, and well-located.", "author": "Alex T."},
            {"rating": 7.8, "text": "Perfect budget option in expensive Tokyo. Met great people!", "author": "Nina P."}
        ]
    },
    # New York Hotels
    {
        "name": "The Plaza Hotel",
        "city": "New York",
        "country": "United States",
        "latitude": 40.7646,
        "longitude": -73.9743,
        "description": "Iconic luxury hotel overlooking Central Park, featured in countless films. A New York City landmark since 1907.",
        "address": "768 5th Ave, New York, NY 10019",
        "star_rating": 5.0,
        "amenities": ["Wi-Fi", "Restaurant", "Bar", "Spa", "Gym", "Room Service", "Concierge", "Valet Parking"],
        "images": [
            "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1200",
            "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=1200"
        ],
        "rooms": [
            {"type": "Deluxe Room", "price": 800.00, "beds": "King", "max_guests": 2},
            {"type": "Central Park View Suite", "price": 1500.00, "beds": "King", "max_guests": 3},
            {"type": "Royal Plaza Suite", "price": 5000.00, "beds": "2 Kings", "max_guests": 4}
        ],
        "reviews": [
            {"rating": 9.6, "text": "Living the dream! Every corner is Instagram-worthy.", "author": "Jessica B."},
            {"rating": 9.4, "text": "Unmatched elegance and service. Worth the splurge!", "author": "William H."},
            {"rating": 9.7, "text": "Felt like royalty. The Central Park views are magical.", "author": "Sophia L."}
        ]
    },
    {
        "name": "Pod Times Square",
        "city": "New York",
        "country": "United States",
        "latitude": 40.7589,
        "longitude": -73.9883,
        "description": "Budget-friendly micro-hotel in the heart of Times Square with rooftop bar and modern efficient design.",
        "address": "400 W 42nd St, New York, NY 10036",
        "star_rating": 3.0,
        "amenities": ["Wi-Fi", "Rooftop Bar", "24-hour Front Desk", "Luggage Storage"],
        "images": [
            "https://images.unsplash.com/photo-1496417263034-38ec4f0b665a?w=1200"
        ],
        "rooms": [
            {"type": "Pod Queen", "price": 180.00, "beds": "Queen", "max_guests": 2},
            {"type": "Pod Bunk", "price": 150.00, "beds": "Bunk Beds", "max_guests": 2}
        ],
        "reviews": [
            {"rating": 8.0, "text": "Great value for NYC! Clean, modern, perfect location.", "author": "Tom K."},
            {"rating": 7.8, "text": "Small but clever design. Rooftop bar is amazing!", "author": "Rachel G."}
        ]
    },
    # Paris Hotels
    {
        "name": "Hôtel Plaza Athénée",
        "city": "Paris",
        "country": "France",
        "latitude": 48.8663,
        "longitude": 2.3048,
        "description": "Legendary palace hotel on Avenue Montaigne with Haute Couture shopping, Michelin-starred dining, and Eiffel Tower views.",
        "address": "25 Avenue Montaigne, 75008 Paris",
        "star_rating": 5.0,
        "amenities": ["Wi-Fi", "Restaurant", "Bar", "Spa", "Gym", "Room Service", "Concierge", "Valet Parking"],
        "images": [
            "https://images.unsplash.com/photo-1549294413-26f195200c16?w=1200",
            "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=1200"
        ],
        "rooms": [
            {"type": "Superior Room", "price": 900.00, "beds": "King", "max_guests": 2},
            {"type": "Eiffel Tower Suite", "price": 2000.00, "beds": "King", "max_guests": 3},
            {"type": "Royal Suite", "price": 6000.00, "beds": "King + Twin", "max_guests": 4}
        ],
        "reviews": [
            {"rating": 9.8, "text": "Pure Parisian elegance! Every detail is perfection.", "author": "Marie C."},
            {"rating": 9.6, "text": "The best hotel in Paris. Alain Ducasse restaurant is sublime.", "author": "Pierre D."},
            {"rating": 9.9, "text": "A dream come true. Will never forget our stay.", "author": "Isabella R."}
        ]
    },
    {
        "name": "Generator Paris",
        "city": "Paris",
        "country": "France",
        "latitude": 48.8814,
        "longitude": 2.3711,
        "description": "Trendy hostel near Canal Saint-Martin with stylish interiors, bar, and social atmosphere. Perfect for young travelers.",
        "address": "9-11 Place du Colonel Fabien, 75010 Paris",
        "star_rating": 3.0,
        "amenities": ["Wi-Fi", "Bar", "Shared Kitchen", "Lounge", "24-hour Front Desk"],
        "images": [
            "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=1200"
        ],
        "rooms": [
            {"type": "Private Room", "price": 120.00, "beds": "Double", "max_guests": 2},
            {"type": "4-Bed Dorm", "price": 35.00, "beds": "Bunk", "max_guests": 1}
        ],
        "reviews": [
            {"rating": 8.3, "text": "Great vibe and location! Met amazing people.", "author": "Lucas B."},
            {"rating": 8.0, "text": "Perfect budget option. Staff is super friendly.", "author": "Anna S."}
        ]
    }
]


def populate_hotels():
    """Populate database with curated hotel data."""
    db = SessionLocal()
    
    try:
        logger.info("=" * 80)
        logger.info("🏨 LUFTWAY HOTEL DATA POPULATOR")
        logger.info("=" * 80)
        
        added_count = 0
        
        for hotel_data in HOTELS_DATA:
            # Check if hotel already exists
            existing = db.query(HotelModel).filter(
                HotelModel.name == hotel_data["name"],
                HotelModel.city == hotel_data["city"]
            ).first()
            
            if existing:
                logger.info(f"⏭️  Skipping {hotel_data['name']} (already exists)")
                continue
            
            logger.info(f"\n📍 Adding: {hotel_data['name']}, {hotel_data['city']}")
            
            # Create hotel
            from search_booking_module.domain.models import Provider
            
            hotel_id = uuid.uuid4()
            hotel = HotelModel(
                id=hotel_id,
                provider_hotel_id=f"manual_{hotel_id.hex[:16]}",  # Generate unique provider ID
                name=hotel_data["name"],
                city=hotel_data["city"],
                country=hotel_data["country"],
                latitude=hotel_data["latitude"],
                longitude=hotel_data["longitude"],
                description=hotel_data["description"],
                address=hotel_data.get("address"),
                rating=hotel_data.get("star_rating"),  # Using rating field for stars
                amenities=hotel_data.get("amenities", []),
                images=hotel_data.get("images", []),
                provider=Provider.DIRECT,
                source_url="https://luftway.com"
            )
            
            db.add(hotel)
            db.flush()  # Get hotel ID
            
            # Add rooms and offers
            from datetime import date, timedelta
            from search_booking_module.infrastructure.db.models import OfferModel
            from search_booking_module.domain.models import Provider
            
            today = date.today()
            next_week = today + timedelta(days=7)
            
            for room_data in hotel_data.get("rooms", []):
                room_id = uuid.uuid4()
                room = RoomModel(
                    id=room_id,
                    hotel_id=hotel.id,
                    room_type_name=room_data["type"],
                    description=f"Comfortable {room_data['type']}",
                    occupancy={
                        "max_guests": room_data.get("max_guests", 2),
                        "bed_type": room_data.get("beds", "Queen")
                    }
                )
                db.add(room)
                
                # Create an offer for this room
                offer = OfferModel(
                    id=uuid.uuid4(),
                    hotel_id=hotel.id,
                    room_id=room_id,
                    provider=Provider.DIRECT,
                    provider_rate_id=f"manual_{room_id.hex[:12]}",
                    currency="USD",
                    price=room_data["price"],
                    taxes_included=False,
                    check_in=today,
                    check_out=next_week,
                    availability_count=10
                )
                db.add(offer)
            
            logger.info(f"   ✅ Added {len(hotel_data.get('rooms', []))} rooms")
            
            # Add reviews
            for review_data in hotel_data.get("reviews", []):
                review = ReviewModel(
                    id=uuid.uuid4(),
                    hotel_id=hotel.id,
                    provider=Provider.DIRECT,
                    rating=review_data["rating"],
                    text=review_data["text"],
                    author=review_data.get("author", "Anonymous")
                )
                db.add(review)
            
            logger.info(f"   ✅ Added {len(hotel_data.get('reviews', []))} reviews")
            
            added_count += 1
        
        # Commit all changes
        db.commit()
        
        # Final stats
        total_hotels = db.query(HotelModel).count()
        total_rooms = db.query(RoomModel).count()
        total_reviews = db.query(ReviewModel).count()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ POPULATION COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Added: {added_count} new hotels")
        logger.info(f"\n📊 DATABASE TOTALS:")
        logger.info(f"   Hotels: {total_hotels}")
        logger.info(f"   Rooms: {total_rooms}")
        logger.info(f"   Reviews: {total_reviews}")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_hotels()

