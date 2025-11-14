# How to Get Real Room Data Instead of 3 Default Rooms

## Current Situation

**Problem:** All hotels have exactly 3 rooms (Standard Room, Comfort Room, Deluxe Room) - these are default/mock rooms created automatically.

**Why:** The hotels were created before the enhanced scraping system was implemented. The enhanced scraper can extract real room data from Booking.com, but existing hotels haven't been re-scraped yet.

## Solution: Re-scrape Existing Hotels

### Step 1: Rebuild Docker Container (Required)

The Docker container needs Playwright browsers installed:

```bash
docker compose build backend
docker compose up -d backend
```

### Step 2: Re-scrape Hotels

I've created a script to re-scrape existing hotels and get real room data:

```bash
# Re-scrape first 10 hotels (for testing)
docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels 10

# Re-scrape all hotels (this will take time)
docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels

# Re-scrape specific hotels by ID
docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels hotel_id1,hotel_id2
```

### Step 3: Verify Results

After re-scraping, check the database:

```bash
docker compose exec postgres psql -U luftway_user -d luftway_auth_dev -c "
SELECT h.name, COUNT(r.id) as room_count, 
       STRING_AGG(DISTINCT r.room_type_name, ', ') as room_types
FROM hotels h 
LEFT JOIN rooms r ON h.id = r.hotel_id 
GROUP BY h.id, h.name 
LIMIT 10;
"
```

## What Will Change

### Before Re-scraping:
- 3 rooms per hotel (Standard, Comfort, Deluxe)
- Default descriptions
- Default prices
- No real room data

### After Re-scraping:
- **Real room types** from Booking.com (e.g., "Superior Double Room", "Deluxe Suite", "Family Room", etc.)
- **Real room descriptions** from Booking.com
- **Real room images** from Booking.com
- **Real occupancy details** (actual size, max guests, bed types)
- **Room-specific amenities**
- **Variable number of rooms** (some hotels may have 5-10+ room types)

## Enhanced Room Extraction

The enhanced scraper now uses **6 different strategies** to find rooms:

1. **data-testid attributes** - Looks for `data-testid` with "room" or "accommodation"
2. **Room type sections** - Finds dedicated room type sections
3. **Accommodation cards** - Finds room/accommodation card elements
4. **Div elements** - Searches for divs with room-related classes
5. **Table rows** - Looks for table rows with room data
6. **List items** - Finds list items with room information
7. **JSON-LD data** - Extracts from structured JSON data

## Important Notes

1. **Time Required:** Re-scraping all 100 hotels will take time (2-3 seconds per hotel = ~5-10 minutes)

2. **Rate Limiting:** The script includes delays between requests to respect Booking.com's rate limits

3. **Browser Required:** Playwright browsers must be installed in the Docker container

4. **Selectors May Need Updates:** Booking.com's HTML structure may change, requiring selector updates

5. **Not All Hotels May Have Rooms:** Some hotels might not have room data available on Booking.com

## Troubleshooting

If rooms are still not being extracted:

1. **Check Playwright Installation:**
   ```bash
   docker compose exec backend playwright --version
   ```

2. **Check Logs:**
   ```bash
   docker compose logs backend | grep -i "room\|extract"
   ```

3. **Test Single Hotel:**
   ```bash
   docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels 1
   ```

4. **Verify Source URLs:**
   ```bash
   docker compose exec postgres psql -U luftway_user -d luftway_auth_dev -c "
   SELECT name, source_url FROM hotels WHERE source_url IS NOT NULL LIMIT 5;
   "
   ```

## Next Steps

1. **Rebuild container** with Playwright support
2. **Run re-scraping script** for a few hotels first (test)
3. **Verify results** in database
4. **Run full re-scraping** if test is successful
5. **Monitor logs** for any extraction issues

After re-scraping, hotels will have real room data from Booking.com instead of the 3 default rooms!




