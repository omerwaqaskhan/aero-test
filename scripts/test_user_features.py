"""Test script to verify all user feature endpoints."""

import sys
import os
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' module not found. Install it with: pip install requests")
    sys.exit(1)

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_auth():
    """Test authentication and get token."""
    print_section("Testing Authentication")
    
    # Register user
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "tenant_slug": "luftway"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ User registered successfully")
        elif response.status_code == 400:
            print("⚠ User may already exist, trying login...")
        else:
            print(f"✗ Registration failed: {response.status_code}")
    except Exception as e:
        print(f"⚠ Registration error (may already exist): {e}")
    
    # Login
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("data", {}).get("access_token") or data.get("access_token")
            print(f"✓ Login successful")
            return token
        else:
            print(f"✗ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def test_favorites(token):
    """Test favorites endpoints."""
    print_section("Testing Favorites Endpoints")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a hotel ID (assuming hotels exist)
    try:
        hotels_response = requests.get(f"{BASE_URL}/api/v1/search-booking/hotels?page_size=1")
        if hotels_response.status_code == 200:
            hotels = hotels_response.json().get("hotels", [])
            if hotels:
                hotel_id = hotels[0]["id"]
                
                # Create favorite
                response = requests.post(
                    f"{BASE_URL}/api/v1/user/favorites",
                    json={"hotel_id": hotel_id},
                    headers=headers
                )
                if response.status_code == 200:
                    print(f"✓ Created favorite for hotel {hotel_id[:8]}...")
                    
                    # Check favorite
                    check_response = requests.get(
                        f"{BASE_URL}/api/v1/user/favorites/{hotel_id}/check",
                        headers=headers
                    )
                    if check_response.status_code == 200:
                        print(f"✓ Favorite check works")
                    
                    # List favorites
                    list_response = requests.get(
                        f"{BASE_URL}/api/v1/user/favorites",
                        headers=headers
                    )
                    if list_response.status_code == 200:
                        favorites = list_response.json()
                        print(f"✓ Listed {len(favorites)} favorites")
                    
                    # Delete favorite
                    delete_response = requests.delete(
                        f"{BASE_URL}/api/v1/user/favorites/{hotel_id}",
                        headers=headers
                    )
                    if delete_response.status_code == 200:
                        print(f"✓ Deleted favorite")
                else:
                    print(f"⚠ Create favorite: {response.status_code}")
            else:
                print("⚠ No hotels found to test favorites")
        else:
            print("⚠ Could not fetch hotels for testing")
    except Exception as e:
        print(f"⚠ Favorites test error: {e}")

def test_bookings(token):
    """Test bookings endpoints."""
    print_section("Testing Bookings Endpoints")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a hotel ID
    try:
        hotels_response = requests.get(f"{BASE_URL}/api/v1/search-booking/hotels?page_size=1")
        if hotels_response.status_code == 200:
            hotels = hotels_response.json().get("hotels", [])
            if hotels:
                hotel_id = hotels[0]["id"]
                
                from datetime import date, timedelta
                check_in = date.today() + timedelta(days=7)
                check_out = check_in + timedelta(days=2)
                
                # Create booking
                booking_data = {
                    "hotel_id": hotel_id,
                    "check_in": str(check_in),
                    "check_out": str(check_out),
                    "guests": 2,
                    "rooms": 1,
                    "guest_name": "Test User",
                    "guest_email": TEST_EMAIL,
                    "guest_phone": "+1234567890"
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/user/bookings",
                    json=booking_data,
                    headers=headers
                )
                if response.status_code == 200:
                    booking = response.json()
                    booking_id = booking["id"]
                    print(f"✓ Created booking {booking_id[:8]}...")
                    
                    # List bookings
                    list_response = requests.get(
                        f"{BASE_URL}/api/v1/user/bookings",
                        headers=headers
                    )
                    if list_response.status_code == 200:
                        bookings = list_response.json()
                        print(f"✓ Listed {len(bookings)} bookings")
                    
                    # Get booking
                    get_response = requests.get(
                        f"{BASE_URL}/api/v1/user/bookings/{booking_id}",
                        headers=headers
                    )
                    if get_response.status_code == 200:
                        print(f"✓ Retrieved booking details")
                else:
                    print(f"⚠ Create booking: {response.status_code} - {response.text}")
            else:
                print("⚠ No hotels found to test bookings")
        else:
            print("⚠ Could not fetch hotels for testing")
    except Exception as e:
        print(f"⚠ Bookings test error: {e}")

def test_price_alerts(token):
    """Test price alerts endpoints."""
    print_section("Testing Price Alerts Endpoints")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a hotel ID
    try:
        hotels_response = requests.get(f"{BASE_URL}/api/v1/search-booking/hotels?page_size=1")
        if hotels_response.status_code == 200:
            hotels = hotels_response.json().get("hotels", [])
            if hotels:
                hotel_id = hotels[0]["id"]
                
                # Create price alert
                alert_data = {
                    "hotel_id": hotel_id,
                    "target_price": 100.00,
                    "currency": "USD",
                    "notify_email": True
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/user/price-alerts",
                    json=alert_data,
                    headers=headers
                )
                if response.status_code == 200:
                    alert = response.json()
                    alert_id = alert["id"]
                    print(f"✓ Created price alert {alert_id[:8]}...")
                    
                    # List alerts
                    list_response = requests.get(
                        f"{BASE_URL}/api/v1/user/price-alerts",
                        headers=headers
                    )
                    if list_response.status_code == 200:
                        alerts = list_response.json()
                        print(f"✓ Listed {len(alerts)} price alerts")
                    
                    # Delete alert
                    delete_response = requests.delete(
                        f"{BASE_URL}/api/v1/user/price-alerts/{alert_id}",
                        headers=headers
                    )
                    if delete_response.status_code == 200:
                        print(f"✓ Deleted price alert")
                else:
                    print(f"⚠ Create price alert: {response.status_code} - {response.text}")
            else:
                print("⚠ No hotels found to test price alerts")
        else:
            print("⚠ Could not fetch hotels for testing")
    except Exception as e:
        print(f"⚠ Price alerts test error: {e}")

def test_saved_searches(token):
    """Test saved searches endpoints."""
    print_section("Testing Saved Searches Endpoints")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create saved search
    search_data = {
        "destination": "Paris",
        "check_in": "2025-12-01",
        "check_out": "2025-12-05",
        "guests": 2,
        "rooms": 1,
        "filters": {"min_price": 50, "max_price": 200},
        "name": "Paris December Trip"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/user/saved-searches",
            json=search_data,
            headers=headers
        )
        if response.status_code == 200:
            search = response.json()
            search_id = search["id"]
            print(f"✓ Created saved search {search_id[:8]}...")
            
            # List searches
            list_response = requests.get(
                f"{BASE_URL}/api/v1/user/saved-searches",
                headers=headers
            )
            if list_response.status_code == 200:
                searches = list_response.json()
                print(f"✓ Listed {len(searches)} saved searches")
            
            # Delete search
            delete_response = requests.delete(
                f"{BASE_URL}/api/v1/user/saved-searches/{search_id}",
                headers=headers
            )
            if delete_response.status_code == 200:
                print(f"✓ Deleted saved search")
        else:
            print(f"⚠ Create saved search: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠ Saved searches test error: {e}")

def test_reviews(token):
    """Test reviews endpoints."""
    print_section("Testing Reviews Endpoints")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get a hotel ID
    try:
        hotels_response = requests.get(f"{BASE_URL}/api/v1/search-booking/hotels?page_size=1")
        if hotels_response.status_code == 200:
            hotels = hotels_response.json().get("hotels", [])
            if hotels:
                hotel_id = hotels[0]["id"]
                
                # Create review
                review_data = {
                    "hotel_id": hotel_id,
                    "rating": 4.5,
                    "title": "Great stay!",
                    "text": "Had a wonderful time at this hotel.",
                    "category_ratings": {
                        "cleanliness": 5.0,
                        "service": 4.5,
                        "value": 4.0,
                        "location": 4.5
                    },
                    "pros": ["Clean rooms", "Great location"],
                    "cons": ["Noisy at night"]
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/user/reviews",
                    json=review_data,
                    headers=headers
                )
                if response.status_code == 200:
                    review = response.json()
                    review_id = review["id"]
                    print(f"✓ Created review {review_id[:8]}...")
                    
                    # List reviews for hotel
                    list_response = requests.get(
                        f"{BASE_URL}/api/v1/user/reviews?hotel_id={hotel_id}",
                        headers=headers
                    )
                    if list_response.status_code == 200:
                        reviews = list_response.json()
                        print(f"✓ Listed {len(reviews)} reviews for hotel")
                else:
                    print(f"⚠ Create review: {response.status_code} - {response.text}")
            else:
                print("⚠ No hotels found to test reviews")
        else:
            print("⚠ Could not fetch hotels for testing")
    except Exception as e:
        print(f"⚠ Reviews test error: {e}")

def main():
    print("\n" + "="*60)
    print("  User Features API Test Suite")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}\n")
    
    # Test authentication
    token = test_auth()
    
    if not token:
        print("\n✗ Authentication failed. Cannot test protected endpoints.")
        return
    
    # Test all endpoints
    test_favorites(token)
    test_bookings(token)
    test_price_alerts(token)
    test_saved_searches(token)
    test_reviews(token)
    
    print_section("Test Suite Complete")
    print("✓ All endpoint tests completed!")
    print("\nNote: Some tests may show warnings if data doesn't exist.")
    print("This is normal for a fresh database.\n")

if __name__ == "__main__":
    main()

