# Scraping Issues Analysis and Fixes

## Issues Identified

1. **Playwright Browser Not Installed for Non-Root User**
   - Error: `Executable doesn't exist at /home/appuser/.cache/ms-playwright/chromium-1091/chrome-linux/chrome`
   - Cause: Playwright browsers were installed as root (`/root/.cache/ms-playwright`) but the app runs as `appuser` (`/home/appuser/.cache/ms-playwright`)
   - Fix: Updated Dockerfile to copy Playwright browsers from root's cache to appuser's cache before switching to non-root user

2. **Missing Brotli Package**
   - Error: `Can not decode content-encoding: brotli (br). Please install 'Brotli'`
   - Cause: Booking.com uses Brotli compression, but the `brotli` package wasn't installed
   - Fix: Added `brotli==1.1.0` to `requirements.txt`

3. **Enhanced Scraper Failing Silently**
   - Issue: When browser failed to launch, scraper fell back to basic scraping which also failed
   - Cause: No proper error handling and browser path not set correctly
   - Fix: Updated `enhanced_booking_scraper.py` to:
     - Set `PLAYWRIGHT_BROWSERS_PATH` environment variable
     - Add better error logging
     - Add `--disable-dev-shm-usage` flag for Docker compatibility

4. **Existing Hotels Not Re-Scraped**
   - Issue: Scheduler only runs initial population if database is empty
   - Cause: Existing hotels with default rooms weren't being re-scraped to get real data
   - Solution: Created `rescrape_hotels.py` script to re-scrape existing hotels

## Fixes Applied

### 1. Dockerfile Updates
- **Production stage**: Install Playwright as root, then copy to appuser's home directory
- **Development stage**: Same fix applied
- **Both stages**: Ensure proper permissions for Playwright cache directory

### 2. Requirements.txt
- Added `brotli==1.1.0` for Brotli compression support

### 3. Enhanced Scraper
- Set `PLAYWRIGHT_BROWSERS_PATH` environment variable
- Added `--disable-dev-shm-usage` flag for Docker
- Improved error logging

## Next Steps

1. **Rebuild Docker Container**
   ```bash
   docker compose build backend
   docker compose up -d
   ```

2. **Re-Scrape Existing Hotels**
   ```bash
   docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels 10
   ```
   This will re-scrape the first 10 hotels to get real room and review data.

3. **Verify Data**
   ```bash
   docker compose exec postgres psql -U luftway_user -d luftway_auth_dev -c "SELECT COUNT(*) FROM rooms WHERE hotel_id IN (SELECT id FROM hotels WHERE source_url IS NOT NULL LIMIT 1);"
   ```

## Expected Results

After these fixes:
- Playwright browser should launch successfully
- Enhanced scraper should fetch real hotel details
- Real room data should be extracted from Booking.com
- Real review data should be extracted
- Hotels should display with actual room cards instead of defaults

