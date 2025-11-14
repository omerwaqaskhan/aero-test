# User Features Tests

## Overview
Comprehensive unit tests for all user features including:
- Favorites/Wishlist
- Bookings
- Price Alerts
- Saved Searches
- User Reviews

## Test Files
- `test_user_features.py` - Tests for all user feature endpoints
- `test_hotel_owner_dashboard.py` - Tests for hotel owner dashboard features
- `conftest.py` - Shared test fixtures and database setup

## Running Tests

### Prerequisites
1. PostgreSQL database must be running
2. Database must exist (or tests will create tables)
3. Set `TEST_DATABASE_URL` environment variable if using a different database

### Run All Tests
```bash
docker compose exec backend pytest search_booking_module/tests/test_user_features.py -v
```

### Run Specific Test Class
```bash
docker compose exec backend pytest search_booking_module/tests/test_user_features.py::TestFavorites -v
```

### Run Single Test
```bash
docker compose exec backend pytest search_booking_module/tests/test_user_features.py::TestFavorites::test_create_favorite -v
```

## Test Coverage

### Favorites Tests
- ✅ Create favorite
- ✅ Get all favorites
- ✅ Check favorite status
- ✅ Delete favorite

### Bookings Tests
- ✅ Create booking
- ✅ Get all bookings
- ✅ Update booking status

### Price Alerts Tests
- ✅ Create price alert
- ✅ Get all price alerts
- ✅ Delete price alert

### Saved Searches Tests
- ✅ Create saved search
- ✅ Get all saved searches
- ✅ Delete saved search

### User Reviews Tests
- ✅ Create review
- ✅ Get reviews for hotel
- ✅ Update review
- ✅ Delete review

## Notes

- Tests use PostgreSQL (SQLite doesn't support UUID type)
- Tests create and drop tables automatically
- All tests use JWT authentication
- Test database is isolated from production data

