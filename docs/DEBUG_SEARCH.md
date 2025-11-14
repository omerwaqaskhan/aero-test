# Debugging Search Functionality

## Common Issues & Solutions

### Issue 1: API Endpoint Not Found (404)

**Symptoms:**
- Browser console shows 404 error
- Network tab shows failed request

**Check:**
1. Is backend running? `docker compose ps` or check `http://localhost:8000/docs`
2. Is router integrated? Check backend logs for "Search-booking module loaded"
3. Is the URL correct? Should be `/api/v1/search-booking/search`

**Fix:**
```bash
# Make sure backend is running
docker compose up backend

# Check if router is loaded (should see in logs):
# "Search-booking module loaded"
```

### Issue 2: CORS Error

**Symptoms:**
- Browser console shows CORS error
- "Access-Control-Allow-Origin" error

**Fix:**
Backend already has CORS enabled, but verify:
```python
# backend/auth_module/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be enabled
    ...
)
```

### Issue 3: Network Error

**Symptoms:**
- "Network error" message
- Request fails immediately

**Check:**
1. Is backend running on port 8000?
2. Is frontend proxy configured correctly?
3. Check `vite.config.ts` proxy settings

**Fix:**
```typescript
// frontend/web-vite/vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

### Issue 4: Empty Results

**Symptoms:**
- API call succeeds but no results shown
- Response has empty results array

**Check:**
1. Check browser console for response data
2. Verify mock providers are returning data
3. Check search filters (dates must be valid)

**Fix:**
- Make sure check-in is before check-out
- Dates should be in future
- Destination should not be empty

### Issue 5: Import Error in Backend

**Symptoms:**
- Backend won't start
- "ModuleNotFoundError" in logs

**Fix:**
```bash
# Make sure all dependencies are installed
cd backend
pip install -r requirements.txt

# Or in Docker:
docker compose exec backend pip install -r requirements.txt
```

---

## Step-by-Step Debugging

### 1. Check Backend Status
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check if search endpoint exists
curl http://localhost:8000/docs
# Should show search-booking endpoints
```

### 2. Test API Directly
```bash
curl "http://localhost:8000/api/v1/search-booking/search?destination=New%20York&check_in=2024-11-15&check_out=2024-11-17&guests=2&rooms=1"
```

Expected response:
```json
{
  "results": [...],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

### 3. Check Frontend Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for errors
4. Check Network tab for API calls
5. Verify request URL and response

### 4. Check Backend Logs
```bash
# Docker logs
docker compose logs backend

# Look for:
# - "Search-booking module loaded"
# - Any error messages
# - Request logs
```

---

## Quick Fixes

### Fix 1: Restart Services
```bash
# Stop everything
docker compose down

# Start again
docker compose up -d

# Check logs
docker compose logs -f backend
```

### Fix 2: Clear Browser Cache
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Or clear browser cache

### Fix 3: Check Environment Variables
```bash
# Frontend
cd frontend/web-vite
# Check .env file or vite.config.ts

# Backend
# Check docker-compose.yml for environment variables
```

---

## Expected Behavior

When search works correctly:

1. **User fills form:**
   - Destination: "New York"
   - Check-in: Tomorrow
   - Check-out: Day after tomorrow
   - Guests: 2

2. **Clicks "Search Now":**
   - Navigates to `/search?destination=New%20York&check_in=...`
   - Shows loading spinner

3. **API Call:**
   - Request: `GET /api/v1/search-booking/search?...`
   - Response: JSON with 10 hotels

4. **Results Display:**
   - 10 hotel cards
   - Each with name, location, price
   - Book buttons for each offer

---

## Test Commands

### Test Backend API
```bash
# Health check
curl http://localhost:8000/api/v1/search-booking/health

# Search test
curl "http://localhost:8000/api/v1/search-booking/search?destination=New%20York&check_in=2024-11-15&check_out=2024-11-17&guests=2&rooms=1" | jq
```

### Test Frontend
1. Open `http://localhost:3000`
2. Open DevTools (F12)
3. Go to Network tab
4. Fill search form
5. Click "Search Now"
6. Check for `/api/v1/search-booking/search` request
7. Check response

---

## Common Error Messages

### "Failed to search hotels"
- Generic error - check console for details
- Usually means API call failed

### "Network error"
- Backend not running
- Wrong API URL
- CORS issue

### "404 Not Found"
- Endpoint doesn't exist
- Router not integrated
- Wrong URL path

### "500 Internal Server Error"
- Backend error
- Check backend logs
- Usually provider or database issue

---

**If still not working, check browser console and backend logs for specific error messages!**

