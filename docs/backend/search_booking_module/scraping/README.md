# Hotel Data Scraping Module

This module handles web scraping to collect hotel data from various sources and store it in our database.

## Structure

```
scraping/
├── __init__.py
├── base_scraper.py          # Base class for all scrapers
├── booking_scraper.py       # Booking.com scraper
├── tripadvisor_scraper.py   # TripAdvisor scraper
├── geocoding.py             # Geocoding service for addresses
├── data_collector.py        # Service to collect and store data
└── populate_database.py     # Script to populate database
```

## Usage

### Populate Database with Hotel Data

```bash
# Populate with default popular destinations
python -m search_booking_module.scraping.populate_database

# Populate specific destinations
python -m search_booking_module.scraping.populate_database \
    --destinations "New York,USA" "Paris,France" "Tokyo,Japan" \
    --max-hotels 50
```

### Using Data Collector Programmatically

```python
from sqlalchemy.orm import Session
from search_booking_module.scraping.data_collector import HotelDataCollector

# Create database session
db = SessionLocal()

# Create collector
collector = HotelDataCollector(db_session=db)

# Collect hotels for a destination
count = await collector.collect_hotels_for_destination(
    destination="New York",
    country="USA",
    max_hotels=50
)

print(f"Collected {count} hotels")
```

## Data Sources

Currently scraping from:
- **Booking.com** - Hotel listings, prices, ratings
- **TripAdvisor** - Hotel reviews and ratings

## Features

- ✅ Async web scraping with rate limiting
- ✅ Geocoding addresses to coordinates
- ✅ Deduplication of hotels
- ✅ Database storage with proper relationships
- ✅ Error handling and logging
- ✅ Respectful scraping (delays between requests)

## Adding New Scrapers

1. Create a new scraper class inheriting from `BaseScraper`
2. Implement `search_hotels()` and `get_hotel_details()` methods
3. Add to `HotelDataCollector.scrapers` list

Example:
```python
from .base_scraper import BaseScraper

class MyScraper(BaseScraper):
    async def search_hotels(self, destination, ...):
        # Your scraping logic
        pass
```

## Notes

- Scrapers respect rate limits with delays between requests
- Uses OpenStreetMap Nominatim for free geocoding
- Hotels are deduplicated by name and city
- Existing hotels are updated, not duplicated

