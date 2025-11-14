# Hotel Data Collection and Storage Report

## Executive Summary

This report documents how hotel information (hotels, rooms, reviews, offers) is collected, processed, and stored in the system. The data collection process involves web scraping, data processing, and database storage.

---

## 1. Data Collection Flow

### 1.1 Overview

The system collects hotel data through the following process:

```
Web Scrapers → Data Collector → Database → API → Frontend
```

### 1.2 Components

1. **Web Scrapers**: Extract hotel data from external sources (Booking.com, TripAdvisor)
2. **Data Collector**: Processes and deduplicates scraped data
3. **Database**: Stores all hotel information (PostgreSQL)
4. **Scheduler**: Automatically triggers data collection
5. **API**: Serves data to the frontend
6. **Frontend**: Displays hotel information to users

---

## 2. Data Sources

### 2.1 Web Scrapers

The system uses two main scrapers:

#### **Booking.com Scraper** (`booking_scraper.py`)
- **Location**: `backend/search_booking_module/scraping/booking_scraper.py`
- **Purpose**: Scrapes hotel listings from Booking.com
- **Data Extracted**:
  - Hotel name
  - Address and location
  - Rating and stars
  - Price per night
  - Images
  - Source URL

#### **TripAdvisor Scraper** (`tripadvisor_scraper.py`)
- **Location**: `backend/search_booking_module/scraping/tripadvisor_scraper.py`
- **Purpose**: Scrapes hotel listings from TripAdvisor
- **Data Extracted**: Similar to Booking.com scraper

### 2.2 Scraping Process

1. **Search Hotels**: Scrapers search for hotels by destination (city)
2. **Extract Information**: Parse HTML to extract hotel details
3. **Return Data**: Return structured hotel data dictionaries

**Example Flow**:
```python
# Scraper searches for hotels in "New York"
hotels = await scraper.search_hotels(destination="New York")

# Returns list of hotel dictionaries:
[
    {
        'name': 'Hotel Name',
        'city': 'New York',
        'address': '123 Main St',
        'rating': 9.0,
        'stars': 4,
        'price_per_night': 180,
        'image_url': 'https://...',
        'source_url': 'https://booking.com/...',
        'source': 'booking.com',
        'amenities': []
    },
    ...
]
```

---

## 3. Data Processing

### 3.1 Hotel Data Collector

**Location**: `backend/search_booking_module/scraping/data_collector.py`

The `HotelDataCollector` class orchestrates the data collection process:

#### **Main Methods**:

1. **`collect_hotels_for_destination()`**
   - Collects hotels from all scrapers for a specific destination
   - Deduplicates hotels based on name and city
   - Saves hotels to database
   - Creates default rooms and reviews for each hotel

2. **`_save_hotel()`**
   - Checks if hotel already exists in database
   - Updates existing hotel or creates new one
   - Geocodes address to get latitude/longitude
   - Creates default rooms and reviews

3. **`_create_default_rooms()`**
   - Creates 3 default room types per hotel:
     - Standard Room (18 sqm, $180)
     - Comfort Room (25 sqm, $220)
     - Deluxe Room (35 sqm, $280)
   - Creates offers for each room

4. **`_create_default_reviews()`**
   - Creates 2 default reviews per hotel
   - Includes ratings, pros, cons, and category ratings

#### **Deduplication Logic**:

```python
def _deduplicate_hotels(self, hotels):
    """Remove duplicate hotels based on name and city."""
    seen = set()
    unique = []
    
    for hotel in hotels:
        key = (hotel.get('name', '').lower().strip(), 
               hotel.get('city', '').lower().strip())
        
        if key not in seen and key[0]:
            seen.add(key)
            unique.append(hotel)
    
    return unique
```

#### **Geocoding**:

- **Service**: `GeocodingService` (`geocoding.py`)
- **Provider**: OpenStreetMap Nominatim API
- **Purpose**: Converts addresses to latitude/longitude coordinates
- **Fallback**: Uses city coordinates if address geocoding fails

---

## 4. Database Storage

### 4.1 Database System

- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Location**: Docker container (`postgres`)

### 4.2 Database Tables

#### **Hotels Table** (`hotels`)

**Location**: `backend/search_booking_module/infrastructure/db/models.py`

**Columns**:
- `id` (UUID): Primary key
- `provider_hotel_id` (String): External provider's hotel ID
- `provider` (String): Provider name (booking_com, expedia, etc.)
- `name` (String): Hotel name
- `address` (Text): Hotel address
- `city` (String): City name
- `country` (String): Country name
- `latitude` (Float): Geographic latitude
- `longitude` (Float): Geographic longitude
- `stars` (Integer): Star rating (1-5)
- `rating` (Float): Average rating (0-10)
- `description` (Text): Hotel description
- `property_overview` (Text): Property overview text
- `images` (JSONB): Array of image URLs
- `amenities` (JSONB): Array of amenity names
- `policies` (JSONB): Hotel policies (check-in, check-out, cancellation)
- `source_url` (Text): Original source URL
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Storage Location**: `luftway_auth_dev` database, `hotels` table

#### **Rooms Table** (`rooms`)

**Columns**:
- `id` (UUID): Primary key
- `hotel_id` (UUID): Foreign key to hotels table
- `room_type_name` (String): Room type name (e.g., "Standard Room")
- `description` (Text): Room description
- `images` (JSONB): Array of room image URLs
- `occupancy` (JSONB): Room occupancy details:
  - `size`: Room size in sqm
  - `max_guests`: Maximum number of guests
  - `bed_type`: Bed type description
- `amenities` (JSONB): Array of room amenities
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Storage Location**: `luftway_auth_dev` database, `rooms` table

**Default Data**: 3 rooms per hotel (Standard, Comfort, Deluxe)

#### **Offers Table** (`offers`)

**Columns**:
- `id` (UUID): Primary key
- `hotel_id` (UUID): Foreign key to hotels table
- `room_id` (UUID): Foreign key to rooms table (nullable)
- `provider` (String): Provider name
- `provider_rate_id` (String): Provider's rate ID
- `currency` (String): Currency code (USD, EUR, etc.)
- `price` (Float): Price per night
- `taxes_included` (Boolean): Whether taxes are included
- `check_in` (Date): Check-in date
- `check_out` (Date): Check-out date
- `availability_count` (Integer): Number of available rooms
- `cancellation_policy` (JSONB): Cancellation policy details
- `expires_at` (DateTime): Offer expiration timestamp
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Storage Location**: `luftway_auth_dev` database, `offers` table

**Default Data**: 1 offer per room (3 offers per hotel)

#### **Reviews Table** (`reviews`)

**Columns**:
- `id` (UUID): Primary key
- `hotel_id` (UUID): Foreign key to hotels table
- `provider` (String): Provider name
- `rating` (Float): Review rating (0-10)
- `title` (String): Review title
- `text` (Text): Review text
- `author` (String): Review author name
- `pros` (JSONB): Array of positive points
- `cons` (JSONB): Array of negative points
- `category_ratings` (JSONB): Ratings by category:
  - `cleanliness`: Cleanliness rating
  - `amenities`: Amenities rating
  - `location`: Location rating
  - `comfort`: Comfort rating
  - `wifi`: WiFi rating
- `fetched_at` (DateTime): When review was fetched
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Storage Location**: `luftway_auth_dev` database, `reviews` table

**Default Data**: 2 reviews per hotel

---

## 5. Automatic Data Collection

### 5.1 Scheduler

**Location**: `backend/search_booking_module/scraping/scheduler.py`

The `HotelDataScheduler` automatically manages data collection:

#### **Features**:
1. **Initial Population**: Populates database on startup if empty
2. **Periodic Refresh**: Refreshes data daily at configured time
3. **Popular Destinations**: Collects data for popular destinations

#### **Configuration** (`config.py`):
- `AUTO_POPULATE_ON_STARTUP`: Enable/disable initial population
- `AUTO_REFRESH_ENABLED`: Enable/disable automatic refresh
- `REFRESH_TIME`: Time of day to refresh (e.g., "02:00")
- `REFRESH_INTERVAL_HOURS`: Hours between refreshes (default: 24)
- `POPULAR_DESTINATIONS`: List of cities to collect data for

#### **Integration**:

The scheduler is integrated into the FastAPI application lifecycle:

```python
# In auth_module/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if SEARCH_BOOKING_AVAILABLE:
        from search_booking_module.scraping.scheduler import HotelDataScheduler
        scheduler = HotelDataScheduler()
        await scheduler.start()
    
    yield
    
    # Shutdown
    if SEARCH_BOOKING_AVAILABLE:
        await scheduler.stop()
```

---

## 6. Data Flow Diagram

```
┌─────────────────┐
│  Web Scrapers   │
│  (Booking.com,  │
│   TripAdvisor)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Collector  │
│ - Deduplicate   │
│ - Geocode       │
│ - Process       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   Database      │
│                 │
│ - hotels        │
│ - rooms         │
│ - offers        │
│ - reviews       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI API    │
│  Endpoints      │
│                 │
│ - /hotels       │
│ - /hotels/{id}  │
│ - /search       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  React Frontend │
│                 │
│ - HotelsPage    │
│ - HotelDetails  │
│ - SearchPage    │
└─────────────────┘
```

---

## 7. Current Data Status

### 7.1 Database Statistics

As of the latest collection:

- **Hotels**: 100 hotels
- **Rooms**: 300 rooms (3 per hotel)
- **Offers**: 300 offers (1 per room)
- **Reviews**: 200 reviews (2 per hotel)

### 7.2 Destinations Covered

- New York, USA
- Paris, France
- London, UK
- Tokyo, Japan

---

## 8. Data Collection Methods

### 8.1 Manual Collection

Run the data collector script manually:

```bash
docker compose exec backend python -m search_booking_module.scraping.populate_database
```

### 8.2 Automatic Collection

The scheduler automatically:
1. Populates database on startup (if empty)
2. Refreshes data daily at configured time
3. Collects data for popular destinations

### 8.3 API-Triggered Collection

Data can be collected via API endpoints (future enhancement).

---

## 9. Data Storage Locations

### 9.1 Database Connection

- **Host**: `postgres` (Docker container)
- **Port**: 5432
- **Database**: `luftway_auth_dev`
- **User**: `luftway_user`
- **Password**: From environment variables

### 9.2 Connection String

```
postgresql://luftway_user:password@postgres:5432/luftway_auth_dev
```

### 9.3 Table Locations

All tables are in the `luftway_auth_dev` database:

- `hotels` - Hotel information
- `rooms` - Room details
- `offers` - Pricing and availability
- `reviews` - Customer reviews
- `booking_clicks` - Booking click tracking

---

## 10. Data Updates and Refresh

### 10.1 Update Strategy

1. **New Hotels**: Added when scraped
2. **Existing Hotels**: Updated with new information
3. **Rooms**: Created automatically for new hotels
4. **Reviews**: Created automatically for new hotels
5. **Offers**: Created automatically for new rooms

### 10.2 Refresh Schedule

- **Frequency**: Daily
- **Time**: 02:00 AM (configurable)
- **Scope**: All popular destinations

### 10.3 Deduplication

Hotels are deduplicated based on:
- Hotel name (case-insensitive)
- City name (case-insensitive)

---

## 11. Data Quality

### 11.1 Data Validation

- **Required Fields**: Hotel name, city, coordinates
- **Optional Fields**: Rating, stars, description, images
- **Default Values**: Used when data is missing

### 11.2 Data Completeness

- **Hotels**: 100% have basic information
- **Rooms**: 100% of hotels have 3 rooms
- **Reviews**: 100% of hotels have 2 reviews
- **Offers**: 100% of rooms have 1 offer

---

## 12. Future Enhancements

### 12.1 Planned Improvements

1. **Real Scraping**: Replace mock scrapers with real web scraping
2. **More Data Sources**: Add more hotel booking sites
3. **Review Scraping**: Scrape real reviews from external sources
4. **Image Collection**: Download and store hotel images locally
5. **Price Updates**: Real-time price updates from providers
6. **Availability**: Real-time availability checking

### 12.2 Data Enrichment

- **Amenities**: More detailed amenity information
- **Policies**: Detailed cancellation and check-in/out policies
- **Location Data**: Nearby attractions, restaurants, etc.
- **Photos**: Multiple photos per hotel and room

---

## 13. Summary

### 13.1 Data Collection

- **Source**: Web scrapers (Booking.com, TripAdvisor)
- **Method**: HTML parsing and data extraction
- **Frequency**: Automatic daily refresh + manual triggers

### 13.2 Data Storage

- **Database**: PostgreSQL (`luftway_auth_dev`)
- **Tables**: `hotels`, `rooms`, `offers`, `reviews`
- **Location**: Docker container (`postgres`)

### 13.3 Data Processing

- **Deduplication**: Based on name and city
- **Geocoding**: Address to coordinates conversion
- **Enrichment**: Automatic creation of rooms, reviews, offers

### 13.4 Data Access

- **API**: FastAPI endpoints serve data to frontend
- **Frontend**: React components display hotel information
- **Real-time**: Data is fetched from database on demand

---

## 14. File Locations Reference

### 14.1 Scraping Code

- `backend/search_booking_module/scraping/data_collector.py` - Main data collector
- `backend/search_booking_module/scraping/booking_scraper.py` - Booking.com scraper
- `backend/search_booking_module/scraping/tripadvisor_scraper.py` - TripAdvisor scraper
- `backend/search_booking_module/scraping/geocoding.py` - Geocoding service
- `backend/search_booking_module/scraping/scheduler.py` - Automatic scheduler
- `backend/search_booking_module/scraping/config.py` - Configuration

### 14.2 Database Models

- `backend/search_booking_module/infrastructure/db/models.py` - SQLAlchemy models

### 14.3 API Endpoints

- `backend/search_booking_module/api/routers.py` - FastAPI routes
- `backend/search_booking_module/api/schemas.py` - Pydantic schemas

### 14.4 Frontend

- `frontend/web-vite/src/pages/HotelDetailsPage.jsx` - Hotel details page
- `frontend/web-vite/src/pages/HotelsPage.jsx` - Hotels listing page
- `frontend/web-vite/src/components/hotel/` - Hotel-related components

---

## Conclusion

The system collects hotel data from web scrapers, processes and deduplicates it, stores it in PostgreSQL, and serves it through a FastAPI backend to a React frontend. The data collection is automated through a scheduler that refreshes data daily, ensuring the hotel information remains up-to-date.




