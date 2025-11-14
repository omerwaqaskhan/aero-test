# Search Data Flow - Where Data Comes From

## 📊 Current Data Source

**Status:** Using **MOCK DATA** from mock providers

---

## 🔄 Data Flow Diagram

```
User Search Form
    ↓
Frontend: SearchPage.jsx
    ↓
API Call: GET /api/v1/search-booking/search
    ↓
Backend: routers.py → search_hotels()
    ↓
SearchService.search_hotels()
    ↓
Provider Adapters (Mock)
    ├── BookingComProvider → Returns 5 mock hotels
    └── ExpediaProvider → Returns 5 mock hotels
    ↓
Aggregated Results (10 hotels total)
    ↓
Response to Frontend
    ↓
Displayed in SearchPage
```

---

## 📍 Where Data is Generated

### 1. **Mock Providers** (Current Implementation)

#### Booking.com Provider
**File:** `backend/search_booking_module/infrastructure/providers/booking_com.py`

**Method:** `search_hotels()`
- **Returns:** 5 mock hotels
- **Data:** Hardcoded sample hotels with:
  - Names: "Sample Hotel 1 - {destination}", etc.
  - Locations: Based on destination parameter
  - Prices: $100, $120, $140 per night
  - Coordinates: Incremental lat/lng
  - Images: Placeholder URLs
  - Amenities: ["WiFi", "Parking", "Breakfast", "Pool"]

#### Expedia Provider
**File:** `backend/search_booking_module/infrastructure/providers/expedia.py`

**Method:** `search_hotels()`
- **Returns:** 5 mock hotels
- **Data:** Similar to Booking.com but with different names
  - Names: "Expedia Hotel 1 - {destination}", etc.
  - Prices: $90, $105, $120 per night
  - Different amenities

---

## 🔧 How It Works

### Step 1: User Searches
```javascript
// Frontend: SearchPage.jsx
const response = await apiClient.get(`/v1/search-booking/search?${params}`);
```

### Step 2: Backend Receives Request
```python
# Backend: routers.py
@router.get("/search")
async def search_hotels(...):
    # Creates SearchService with providers
    search_service = SearchService(providers=providers, db_session=db)
    
    # Calls search service
    results = await search_service.search_hotels(...)
```

### Step 3: Search Service Aggregates
```python
# Backend: domain/services.py
async def search_hotels(self, filters, ...):
    # Loops through all providers
    for provider in self.providers:
        # Calls provider's search_hotels method
        hotels = await provider.search_hotels(
            destination=filters.destination,
            check_in=filters.check_in,
            check_out=filters.check_out,
            guests=filters.guests,
            rooms=filters.rooms
        )
        
        # Gets offers for each hotel
        offers = await provider.get_offers(...)
        
        # Adds to results
        all_hotels[key] = hotel
        all_offers[key] = offers
```

### Step 4: Provider Returns Mock Data
```python
# Backend: providers/booking_com.py
async def search_hotels(self, destination, check_in, check_out, ...):
    # Creates 5 mock hotels
    hotels = []
    for i in range(5):
        hotel = Hotel(
            name=f"Sample Hotel {i+1} - {destination}",
            city=destination,
            price=100.0 + (i * 20),  # $100, $120, $140, etc.
            stars=3 + (i % 3),
            ...
        )
        hotels.append(hotel)
    return hotels
```

---

## 📦 Current Data Structure

### Mock Hotel Data
Each provider returns hotels with:
- **ID:** Generated UUID
- **Name:** "Sample Hotel X - {destination}"
- **Location:** Uses destination parameter
- **Coordinates:** Incremental lat/lng (40.7128 + i*0.01)
- **Stars:** 3-5 stars (varies)
- **Price:** $100-$200 range
- **Images:** Placeholder URLs
- **Amenities:** ["WiFi", "Parking", "Breakfast", "Pool"]

### Mock Offer Data
Each hotel has 3 offers:
- **Price:** Base price + increment
- **Availability:** 5, 4, 3 rooms
- **Cancellation:** Free, moderate, non-refundable
- **Currency:** USD
- **Dates:** Uses check-in/check-out from search

---

## 🔄 To Use Real Data

### Option 1: Replace Mock Providers with Real APIs

**Booking.com:**
1. Get API credentials from Booking.com
2. Replace mock implementation with real API calls
3. Parse real API responses

**Expedia:**
1. Get API credentials from Expedia
2. Replace mock implementation with real API calls
3. Parse real API responses

### Option 2: Use Database (Future)
1. Store hotels in database
2. Fetch from database instead of providers
3. Update database periodically from providers

---

## 📂 Files Involved

### Data Generation
- `backend/search_booking_module/infrastructure/providers/booking_com.py`
  - Line 20-80: `search_hotels()` - Generates 5 mock hotels
  - Line 90-120: `get_offers()` - Generates 3 mock offers per hotel

- `backend/search_booking_module/infrastructure/providers/expedia.py`
  - Line 20-80: `search_hotels()` - Generates 5 mock hotels
  - Line 90-120: `get_offers()` - Generates 3 mock offers per hotel

### Data Aggregation
- `backend/search_booking_module/domain/services.py`
  - Line 28-150: `SearchService.search_hotels()` - Aggregates results from all providers

### API Endpoint
- `backend/search_booking_module/api/routers.py`
  - Line 52-185: `search_hotels()` endpoint - Receives request and returns results

### Frontend Display
- `frontend/web-vite/src/pages/SearchPage.jsx`
  - Line 38-100: `performSearch()` - Calls API and displays results

---

## 🎯 Summary

**Current State:**
- ✅ Data comes from **mock providers** (hardcoded sample data)
- ✅ Booking.com provider returns 5 hotels
- ✅ Expedia provider returns 5 hotels
- ✅ Total: **10 hotels** per search
- ✅ Each hotel has **3 offers** (different prices)

**Future State:**
- 🔄 Replace mock providers with real API integrations
- 🔄 Connect to Booking.com API
- 🔄 Connect to Expedia API
- 🔄 Store results in database
- 🔄 Cache results for performance

---

## 🔍 Where to Find the Code

1. **Mock Hotel Generation:**
   - `backend/search_booking_module/infrastructure/providers/booking_com.py`
   - `backend/search_booking_module/infrastructure/providers/expedia.py`

2. **Data Aggregation:**
   - `backend/search_booking_module/domain/services.py` → `SearchService`

3. **API Endpoint:**
   - `backend/search_booking_module/api/routers.py` → `search_hotels()`

4. **Frontend Display:**
   - `frontend/web-vite/src/pages/SearchPage.jsx` → `performSearch()`

---

**Current Data Source:** Mock/Test Data (Hardcoded in Provider Classes)  
**Future Data Source:** Real Provider APIs (Booking.com, Expedia, etc.)

