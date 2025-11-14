# Hotel Data Collection - Implementation Plan

## Overview

We're implementing a web scraping system to collect hotel data from the internet and store it in our own database, replacing the mock data system.

## Architecture

```
┌─────────────────┐
│  Web Scrapers   │
│  - Booking.com  │
│  - TripAdvisor  │
│  - (More...)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Collector  │
│ - Aggregates    │
│ - Deduplicates  │
│ - Geocodes      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Database      │
│   - Hotels      │
│   - Offers      │
│   - Reviews     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Search Service │
│  - Queries DB   │
│  - Returns      │
│    Results      │
└─────────────────┘
```

## Implementation Status

### ✅ Completed

1. **Database Models**
   - ✅ HotelModel with all required fields
   - ✅ OfferModel for pricing
   - ✅ ReviewModel for ratings
   - ✅ Added `rating` and `source_url` fields

2. **Scraping Infrastructure**
   - ✅ BaseScraper abstract class
   - ✅ BookingScraper implementation
   - ✅ TripAdvisorScraper implementation
   - ✅ GeocodingService for coordinates
   - ✅ HotelDataCollector service

3. **Data Collection Script**
   - ✅ populate_database.py script
   - ✅ Popular destinations list
   - ✅ Command-line arguments

4. **Search Service Update**
   - ✅ Updated to query database instead of providers
   - ✅ Backward compatible (can still use providers)
   - ✅ Proper filtering and sorting

### 🔄 In Progress

1. **Testing Scrapers**
   - Need to test actual scraping
   - Handle website structure changes
   - Error handling improvements

2. **Database Migration**
   - Add rating and source_url fields
   - Run migration

### 📋 TODO

1. **Additional Scrapers**
   - [ ] Expedia scraper
   - [ ] Agoda scraper
   - [ ] Hotels.com scraper

2. **Data Quality**
   - [ ] Data validation
   - [ ] Image URL validation
   - [ ] Price normalization

3. **Scheduling**
   - [ ] Periodic data refresh
   - [ ] Update existing hotels
   - [ ] Remove outdated data

4. **Performance**
   - [ ] Database indexing
   - [ ] Caching
   - [ ] Batch processing

## Usage

### Initial Data Population

```bash
# Populate database with popular destinations
cd backend
python -m search_booking_module.scraping.populate_database
```

### Add Specific Destinations

```bash
python -m search_booking_module.scraping.populate_database \
    --destinations "New York,USA" "Paris,France" \
    --max-hotels 100
```

### Search from Database

The search service now queries the database by default:

```python
# In routers.py
search_service = SearchService(
    providers=providers,
    db_session=db,
    use_database=True  # Use database instead of providers
)
```

## Data Flow

1. **Collection Phase**
   - Scrapers fetch hotel data from websites
   - Data is parsed and normalized
   - Addresses are geocoded to coordinates

2. **Storage Phase**
   - Hotels are deduplicated (by name + city)
   - Existing hotels are updated
   - New hotels are inserted
   - Offers are created for each hotel

3. **Search Phase**
   - Search service queries database
   - Filters by destination, price, rating, etc.
   - Returns results with offers

## Database Schema

### Hotels Table
- `id` - UUID primary key
- `name` - Hotel name
- `city`, `country` - Location
- `latitude`, `longitude` - Coordinates
- `stars` - Star rating (0-5)
- `rating` - Average rating (0-5)
- `images` - JSON array of image URLs
- `amenities` - JSON array of amenities
- `source_url` - URL where scraped from
- `created_at`, `updated_at` - Timestamps

### Offers Table
- `id` - UUID primary key
- `hotel_id` - Foreign key to hotels
- `price` - Price per night
- `currency` - Currency code
- `check_in`, `check_out` - Date range
- `availability_count` - Number of rooms
- `cancellation_policy` - JSON policy details

## Popular Destinations

Default list includes:
- New York, USA
- Paris, France
- London, UK
- Tokyo, Japan
- Dubai, UAE
- Barcelona, Spain
- Rome, Italy
- Amsterdam, Netherlands
- Bangkok, Thailand
- Singapore, Singapore
- And more...

## Next Steps

1. **Run Initial Population**
   ```bash
   python -m search_booking_module.scraping.populate_database
   ```

2. **Test Search**
   - Search should now return real hotel data
   - Verify results are from database

3. **Add More Destinations**
   - Expand popular destinations list
   - Add user-requested cities

4. **Schedule Updates**
   - Set up periodic data refresh
   - Update prices and availability

5. **Monitor & Improve**
   - Track scraping success rate
   - Handle website changes
   - Improve data quality

## Notes

- Scrapers respect rate limits (delays between requests)
- Uses OpenStreetMap Nominatim for free geocoding
- Hotels are deduplicated to avoid duplicates
- Existing hotels are updated, not recreated
- Search service can fall back to providers if database is empty

