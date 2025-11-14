# Search Functionality - Status Check

## ✅ Should Search Work?

**YES**, the search functionality should work and bring up a list of hotels, **IF**:

1. ✅ Backend server is running
2. ✅ Search-booking router is integrated
3. ✅ API URL is correctly configured
4. ✅ CORS is enabled
5. ✅ Mock providers are working

---

## 🔍 How to Verify It's Working

### 1. Check Backend Server
```bash
# Make sure backend is running
docker compose up backend
# OR
cd backend && python -m uvicorn auth_module.main:app --reload
```

### 2. Test API Endpoint Directly
Visit: `http://localhost:8000/docs`

Or test with curl:
```bash
curl "http://localhost:8000/api/v1/search-booking/search?destination=New%20York&check_in=2024-11-15&check_out=2024-11-17&guests=2&rooms=1"
```

### 3. Check Frontend API URL
The frontend should be calling:
- Development: `http://localhost:8000/api/v1/search-booking/search`
- Or via proxy: `/api/v1/search-booking/search`

### 4. Check Browser Console
Open browser DevTools → Console tab
- Look for any errors
- Check Network tab for API calls
- Verify response structure

---

## 🐛 Common Issues & Fixes

### Issue 1: "Network error" or CORS error
**Fix:** Make sure CORS is enabled in backend:
```python
# backend/auth_module/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 2: "404 Not Found"
**Fix:** Check if router is integrated:
```python
# backend/auth_module/main.py should have:
if SEARCH_BOOKING_AVAILABLE:
    app.include_router(search_booking_router)
```

### Issue 3: "500 Internal Server Error"
**Fix:** Check backend logs for errors. Common issues:
- Database connection
- Provider initialization
- Missing dependencies

### Issue 4: Empty results
**Fix:** Mock providers should return 5 hotels each. Check:
- Provider initialization
- Search service logic
- Response conversion

---

## 📋 Expected Response Format

The API should return:
```json
{
  "results": [
    {
      "hotel": {
        "id": "...",
        "name": "Sample Hotel 1 - New York",
        "city": "New York",
        "country": "USA",
        "stars": 3,
        "images": [...],
        "amenities": [...]
      },
      "offers": [
        {
          "id": "...",
          "price": 100.0,
          "currency": "USD",
          ...
        }
      ],
      "best_price": 100.0,
      "average_rating": null,
      "review_count": 0
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

## ✅ Quick Test Steps

1. **Start Backend:**
   ```bash
   docker compose up backend
   ```

2. **Start Frontend:**
   ```bash
   cd frontend/web-vite
   npm run dev
   ```

3. **Test Search:**
   - Go to landing page
   - Fill search form:
     - Destination: "New York"
     - Check-in: Tomorrow
     - Check-out: Day after tomorrow
     - Guests: 2
   - Click "Search Now"
   - Should redirect to `/search` with results

4. **Check Results:**
   - Should see 10 hotels (5 from Booking.com + 5 from Expedia)
   - Each hotel should have offers
   - Prices should be displayed

---

## 🔧 If It's Not Working

### Debug Steps:

1. **Check Browser Console:**
   - Open DevTools (F12)
   - Go to Console tab
   - Look for errors
   - Check Network tab for failed requests

2. **Check Backend Logs:**
   - Look for error messages
   - Check if router is loaded
   - Verify provider initialization

3. **Test API Directly:**
   - Use Postman or curl
   - Test endpoint: `/api/v1/search-booking/search`
   - Verify response structure

4. **Check API URL:**
   - Frontend config: `frontend/web-vite/src/lib/config.js`
   - Should point to backend URL
   - Default: `http://localhost:8000`

---

## 📝 Current Implementation Status

✅ **Backend:**
- Search endpoint implemented
- Mock providers working
- Response format correct
- Router integrated

✅ **Frontend:**
- Search page implemented
- API client configured
- Results display ready
- Error handling in place

⚠️ **Potential Issues:**
- API URL might need configuration
- CORS might need adjustment
- Backend might not be running
- Router might not be loaded

---

## 🚀 Expected Behavior

When you click "Search Now":
1. Form validates input
2. Navigates to `/search?destination=...&check_in=...&check_out=...`
3. SearchPage component loads
4. Calls API: `GET /api/v1/search-booking/search?...`
5. Shows loading spinner
6. Receives response with 10 hotels
7. Displays hotel cards with:
   - Hotel name
   - Location
   - Star rating
   - Price
   - Book buttons

---

**If search is not working, check the browser console and backend logs for specific error messages!**

