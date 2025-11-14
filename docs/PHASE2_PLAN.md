# Phase 2: Core Platform Features - Implementation Plan

**Date:** November 6, 2024  
**Branch:** `phase2-search-booking`  
**Status:** 🚀 **Starting Implementation**

---

## 📋 Overview

Phase 2 focuses on building the core search and booking platform functionality, including:
- Hotel/stay aggregation from multiple providers
- Advanced search and filtering
- Price comparison
- Booking flow and affiliate tracking

---

## 🎯 Phase 2 Goals

### Core Features
1. **Provider Integration**
   - Provider adapter interface
   - Booking.com integration (mock/real)
   - Expedia integration (mock/real)
   - Real-time availability checking
   - Price aggregation

2. **Search & Discovery**
   - Search API with filters
   - Sorting capabilities (price, rating, distance)
   - Map integration
   - Caching layer

3. **Booking & Tracking**
   - Click tracking
   - Affiliate link generation
   - Booking flow
   - Conversion monitoring

4. **Database Schema**
   - Hotels table
   - Rooms table
   - Offers table
   - Bookings table
   - Reviews table

---

## 🏗️ Architecture

### Module Structure
```
backend/
├── search_booking_module/
│   ├── __init__.py
│   ├── domain/
│   │   ├── models.py          # Hotel, Room, Offer, Booking models
│   │   ├── services.py        # SearchService, BookingService
│   │   └── policies.py        # Booking policies
│   ├── infrastructure/
│   │   ├── providers/          # Provider adapters
│   │   │   ├── base.py        # Base provider interface
│   │   │   ├── booking_com.py # Booking.com adapter
│   │   │   └── expedia.py     # Expedia adapter
│   │   ├── db/
│   │   │   ├── models.py      # SQLAlchemy models
│   │   │   └── repositories.py # Repositories
│   │   └── cache.py           # Caching layer
│   ├── api/
│   │   ├── routers.py         # FastAPI routers
│   │   └── schemas.py         # Pydantic schemas
│   └── main.py               # Module entry point
```

---

## 📊 Database Schema

### Core Tables

#### `hotels`
- `id` (uuid, PK)
- `provider_hotel_id` (string) - ID from provider
- `provider` (enum) - booking_com, expedia, etc.
- `name` (string)
- `address` (json) - Full address
- `city` (string)
- `country` (string)
- `latitude` (float)
- `longitude` (float)
- `stars` (integer)
- `description` (text)
- `images` (json array)
- `amenities` (json array)
- `created_at`, `updated_at` (timestamps)

#### `rooms`
- `id` (uuid, PK)
- `hotel_id` (uuid, FK -> hotels)
- `room_type_name` (string)
- `occupancy` (json) - max_guests, beds, etc.
- `amenities` (json array)
- `created_at`, `updated_at` (timestamps)

#### `offers`
- `id` (uuid, PK)
- `hotel_id` (uuid, FK -> hotels)
- `room_id` (uuid, FK -> rooms, nullable)
- `provider` (enum)
- `provider_rate_id` (string) - Rate ID from provider
- `currency` (string)
- `price` (decimal)
- `taxes_included` (boolean)
- `check_in` (date)
- `check_out` (date)
- `availability_count` (integer)
- `cancellation_policy` (json)
- `raw_response` (json) - Full provider payload
- `fetched_at` (timestamp)
- `expires_at` (timestamp)

#### `bookings_clicks`
- `id` (uuid, PK)
- `user_id` (uuid, FK -> users, nullable)
- `offer_id` (uuid, FK -> offers)
- `provider` (enum)
- `affiliate_link` (string)
- `clicked_at` (timestamp)
- `ip_address` (string)
- `user_agent` (string)
- `converted` (boolean) - Whether booking was completed
- `converted_at` (timestamp, nullable)

#### `reviews`
- `id` (uuid, PK)
- `hotel_id` (uuid, FK -> hotels)
- `provider` (enum)
- `rating` (float)
- `text` (text)
- `author` (string)
- `fetched_at` (timestamp)

---

## 🔧 Implementation Steps

### Step 1: Module Structure ✅ (In Progress)
- [x] Create `search_booking_module` directory
- [ ] Set up domain, infrastructure, api folders
- [ ] Create `__init__.py` files

### Step 2: Database Schema
- [ ] Create Alembic migration for hotels table
- [ ] Create Alembic migration for rooms table
- [ ] Create Alembic migration for offers table
- [ ] Create Alembic migration for bookings_clicks table
- [ ] Create Alembic migration for reviews table

### Step 3: Domain Models
- [ ] Create Hotel domain model
- [ ] Create Room domain model
- [ ] Create Offer domain model
- [ ] Create BookingClick domain model
- [ ] Create Review domain model

### Step 4: Provider Integration
- [ ] Create base Provider interface
- [ ] Implement Booking.com adapter (mock first)
- [ ] Implement Expedia adapter (mock first)
- [ ] Add error handling and retry logic

### Step 5: Search Service
- [ ] Implement SearchService
- [ ] Add filtering logic
- [ ] Add sorting logic
- [ ] Add pagination
- [ ] Integrate caching

### Step 6: API Endpoints
- [ ] `GET /api/v1/search` - Search hotels
- [ ] `GET /api/v1/hotels/{hotel_id}` - Get hotel details
- [ ] `GET /api/v1/hotels/{hotel_id}/offers` - Get offers
- [ ] `POST /api/v1/bookings/click` - Track booking click
- [ ] `GET /api/v1/bookings/history` - Get user bookings

### Step 7: Frontend Components
- [ ] Search form component
- [ ] Hotel list component
- [ ] Hotel card component
- [ ] Filters sidebar
- [ ] Map view component

---

## 🚀 Getting Started

### 1. Create Module Structure
```bash
mkdir -p backend/search_booking_module/{domain,infrastructure/{providers,db},api}
```

### 2. Set Up Database Migrations
```bash
cd backend/search_booking_module
alembic init migrations
```

### 3. Create Initial Models
- Start with domain models
- Then create SQLAlchemy models
- Finally create repositories

---

## 📝 Notes

- Start with mock providers for testing
- Implement caching early for performance
- Use Redis for offer caching (TTL based on expires_at)
- Track all clicks for analytics
- Implement rate limiting for provider APIs

---

## ✅ Success Criteria

- [ ] Can search hotels by location and dates
- [ ] Can compare prices across providers
- [ ] Can track booking clicks
- [ ] Can view hotel details and offers
- [ ] Search results are cached
- [ ] API endpoints are documented
- [ ] Basic frontend search interface works

---

**Status:** 🚀 Ready to start implementation!

