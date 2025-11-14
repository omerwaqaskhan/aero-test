# Why Only 3 Rooms? - Explanation and Solution

## The Problem

You're seeing only 3 rooms per hotel because:

1. **Existing hotels were created with default rooms** - The hotels in your database were created before the enhanced scraping system was fully implemented. They have 3 default room types (Standard, Comfort, Deluxe) that were automatically created.

2. **Enhanced scraper needs to be tested** - The enhanced scraper with Playwright support was just implemented, but:
   - Playwright browsers need to be installed in the Docker container
   - The room extraction selectors need to match Booking.com's actual HTML structure
   - The hotels need to be re-scraped to get real room data

3. **Room extraction might not be finding rooms** - Booking.com's HTML structure is complex and may require:
   - Better selectors
   - JavaScript rendering (which Playwright handles)
   - Multiple extraction strategies

## The Solution

### Step 1: Rebuild Docker Container

The Docker container needs to be rebuilt to install Playwright browsers:

```bash
docker compose build backend
docker compose up -d backend
```

### Step 2: Re-scrape Existing Hotels

I've created a script to re-scrape existing hotels and get real room data:

```bash
# Re-scrape all hotels (limit to 10 for testing)
docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels 10

# Re-scrape specific hotels
docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels hotel_id1,hotel_id2
```

### Step 3: Verify Room Extraction

The enhanced scraper now uses multiple strategies to find rooms:
1. Look for `data-testid` attributes with "room" or "accommodation"
2. Look for room type sections
3. Look for accommodation cards
4. Look for divs with room-related classes
5. Look for table rows with room data
6. Look for list items with room data
7. Extract from JSON-LD structured data

## What's Been Improved

1. **Enhanced Room Extraction** - Multiple strategies to find rooms on Booking.com
2. **Better Room Name Extraction** - Tries multiple selectors to find room names
3. **Re-scraping Script** - Script to update existing hotels with real data
4. **Better Logging** - More detailed logging to debug room extraction

## Next Steps

1. **Rebuild the container** to install Playwright browsers
2. **Run the re-scraping script** to update existing hotels
3. **Check the logs** to see if rooms are being extracted
4. **Verify in database** that hotels now have real room data

## Expected Results

After re-scraping, hotels should have:
- **Real room types** (not just Standard, Comfort, Deluxe)
- **Room descriptions** from Booking.com
- **Room images** from Booking.com
- **Real occupancy details** (size, max guests, bed type)
- **Room-specific amenities**

The number of rooms will vary by hotel - some may have 5-10+ room types, not just 3.




