#!/bin/bash

# Quick status check script

echo "=========================================="
echo "📊 LuftWay Database Status"
echo "=========================================="
echo ""

docker compose exec backend python -c "
from search_booking_module.infrastructure.db.models import HotelModel, RoomModel, ReviewModel, OfferModel
from revenue_module.infrastructure.db.models import LeadModel, SubscriptionModel, HotelListingModel
from auth_module.infrastructure.db.models import UserModel
from auth_module.infrastructure.db.database import SessionLocal

db = SessionLocal()

hotels_total = db.query(HotelModel).count()
rooms_total = db.query(RoomModel).count()
reviews_total = db.query(ReviewModel).count()
offers_total = db.query(OfferModel).count()
hotels_with_rooms = db.query(HotelModel).join(RoomModel).distinct().count()
hotels_with_reviews = db.query(HotelModel).join(ReviewModel).distinct().count()

print('=== CORE DATA ===')
print(f'✅ Users: {db.query(UserModel).count()}')
print(f'✅ Hotels: {hotels_total}')
print(f'📦 Rooms: {rooms_total}')
print(f'💰 Offers: {offers_total}')
print(f'⭐ Reviews: {reviews_total}')
print()
print('=== REVENUE MODULE ===')
print(f'📧 Leads: {db.query(LeadModel).count()}')
print(f'💳 Subscriptions: {db.query(SubscriptionModel).count()}')
print(f'🏨 Hotel Listings: {db.query(HotelListingModel).count()}')
print()
print('=== COMPLETION ===')
print(f'Hotels with rooms: {hotels_with_rooms} / {hotels_total} ({int(hotels_with_rooms/hotels_total*100) if hotels_total > 0 else 0}%)')
print(f'Hotels with reviews: {hotels_with_reviews} / {hotels_total} ({int(hotels_with_reviews/hotels_total*100) if hotels_total > 0 else 0}%)')
print()

# Check scraper status
import subprocess
try:
    result = subprocess.run(['pgrep', '-f', 'rescrape_hotels'], capture_output=True, text=True)
    if result.returncode == 0:
        print('🔄 Scraper Status: RUNNING ✅')
    else:
        print('⏸️  Scraper Status: NOT RUNNING')
except:
    print('❓ Scraper Status: UNKNOWN')

db.close()
" 2>&1

echo ""
echo "=========================================="

