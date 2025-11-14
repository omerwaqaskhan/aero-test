# Automatic Hotel Data Collection

## ✅ Implementation Complete

The system now **automatically** collects and refreshes hotel data! No manual intervention needed.

## 🚀 How It Works

### 1. **Automatic Startup Population**
When the backend server starts:
- ✅ Checks if database is empty
- ✅ If empty, automatically populates with 10 popular destinations
- ✅ Collects 30 hotels per destination (to avoid long startup)
- ✅ Runs in background, doesn't block server startup

### 2. **Automatic Daily Refresh**
- ✅ Scheduled to run daily at **2:00 AM** (configurable)
- ✅ Refreshes hotel data for all destinations in database
- ✅ Updates existing hotels with new information
- ✅ Adds new hotels found

### 3. **Background Processing**
- ✅ Uses APScheduler for task scheduling
- ✅ Runs asynchronously, doesn't block API requests
- ✅ Graceful error handling
- ✅ Logs all activities

## ⚙️ Configuration

### Environment Variables

```bash
# Enable/disable automatic population on startup
AUTO_POPULATE_ON_STARTUP=true  # Default: true

# Enable/disable automatic daily refresh
AUTO_REFRESH_ENABLED=true  # Default: true

# Time for daily refresh (24-hour format)
REFRESH_TIME=02:00  # Default: 2:00 AM

# Hours between refreshes (if using interval)
REFRESH_INTERVAL_HOURS=24  # Default: 24 hours

# Maximum hotels per destination
MAX_HOTELS_PER_DESTINATION=50  # Default: 50

# Delay between scraping requests (seconds)
SCRAPING_DELAY_SECONDS=1.0  # Default: 1.0
```

### Default Behavior

- ✅ **Startup**: Automatically populates if database is empty
- ✅ **Daily**: Refreshes all destinations at 2:00 AM
- ✅ **Background**: Runs asynchronously, doesn't block API

## 📊 What Happens

### On Server Startup

1. Server starts
2. Scheduler initializes
3. Checks database for hotels
4. If empty → Starts background population
5. Collects hotels for 10 popular destinations
6. Server continues to serve API requests

### Daily Refresh (2:00 AM)

1. Scheduler triggers refresh
2. Gets all unique destinations from database
3. Refreshes hotel data for each destination
4. Updates existing hotels
5. Adds new hotels found
6. Logs results

## 🔧 Manual Control

### Disable Automatic Population

```bash
# In .env or environment
AUTO_POPULATE_ON_STARTUP=false
```

### Disable Automatic Refresh

```bash
# In .env or environment
AUTO_REFRESH_ENABLED=false
```

### Change Refresh Time

```bash
# In .env or environment
REFRESH_TIME=03:00  # Change to 3:00 AM
```

## 📝 Logs

The scheduler logs all activities:

```
INFO - Starting hotel data scheduler...
INFO - Database already has 150 hotels. Skipping initial population.
INFO - Scheduled daily refresh at 02:00
INFO - Hotel data scheduler started
```

Daily refresh logs:
```
INFO - Refreshing hotel data for 10 destinations...
INFO - Refreshing hotels for New York, USA...
INFO - ✓ Refreshed 45 hotels for New York, USA
...
INFO - Hotel data refresh completed
```

## 🎯 Benefits

1. **Zero Manual Work**: Data collection happens automatically
2. **Always Fresh**: Daily updates keep data current
3. **Non-Blocking**: Runs in background, doesn't affect API
4. **Configurable**: Easy to adjust via environment variables
5. **Resilient**: Graceful error handling, continues on failures

## 🚀 Next Steps

1. **Start Server**: Just start the backend server!
   ```bash
   docker compose up backend
   # OR
   python -m uvicorn auth_module.main:app --reload
   ```

2. **Check Logs**: Watch for scheduler messages
   ```
   INFO - Hotel data scheduler started
   INFO - Database is empty. Starting initial population...
   ```

3. **Wait for Population**: Initial population takes a few minutes
   - Collects 10 destinations
   - 30 hotels per destination
   - Runs in background

4. **Daily Updates**: Automatic refresh runs at 2:00 AM daily

## ⚠️ Notes

- **Initial Population**: Takes 5-10 minutes (runs in background)
- **Daily Refresh**: Takes 10-20 minutes (runs at 2 AM)
- **Rate Limiting**: Scrapers include delays to be respectful
- **Error Handling**: Failures don't stop the process

## 🔍 Monitoring

Check scheduler status:
- Look for "Hotel data scheduler started" in logs
- Check database for hotels after startup
- Monitor daily refresh logs at 2 AM

---

**Status**: ✅ **Fully Automatic - No Manual Steps Required!**

Just start the server and the system will:
1. ✅ Populate database if empty
2. ✅ Refresh data daily at 2 AM
3. ✅ Keep data fresh automatically

