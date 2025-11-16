# 🔄 Hybrid Data Source Guide

**Intelligently switch between APIs and scraping based on availability, cost, and performance.**

---

## 📋 Overview

The Hybrid Data Source Manager allows you to:
- ✅ **API-First**: Use official APIs when available (Booking.com, Expedia, etc.)
- ✅ **Scraping Fallback**: Automatically fall back to scraping if API fails
- ✅ **Parallel Mode**: Run both simultaneously and merge results
- ✅ **Dynamic Switching**: Change strategy based on cost, speed, or quality
- ✅ **Smart Limits**: Stop scraping when API provides enough data

---

## 🎯 Available Strategies

| Strategy | When to Use | Cost | Speed | Quality |
|----------|-------------|------|-------|---------|
| **API_FIRST** ⭐ | Production (recommended) | Medium | Fast | High |
| **SCRAPING_FIRST** | When APIs are expensive | Low | Slow | Medium |
| **API_ONLY** | When scraping is blocked | High | Fast | High |
| **SCRAPING_ONLY** | When no API available | Low | Slow | Medium |
| **PARALLEL** | Maximum coverage | High | Fast | Highest |
| **CHEAPEST** | Budget-conscious | Lowest | Varies | Varies |
| **FASTEST** | Real-time needs | Varies | Fastest | High |

---

## 🚀 Quick Start

### 1. Environment Configuration

Add to your `.env` file:

```bash
# ===================================================================
# HYBRID DATA SOURCE CONFIGURATION
# ===================================================================

# Strategy (choose one)
DATA_SOURCE_STRATEGY=api_first  # api_first, scraping_first, api_only, scraping_only, parallel, cheapest, fastest

# Enable/Disable Sources
ENABLE_API=true
ENABLE_SCRAPING=true

# ===================================================================
# API CONFIGURATION (When available)
# ===================================================================

# Booking.com API (when you get it)
BOOKING_COM_API_KEY=your_api_key_here
BOOKING_COM_API_SECRET=your_api_secret_here
BOOKING_COM_RATE_LIMIT=60  # requests per minute
BOOKING_COM_COST_PER_REQUEST=0.01  # $0.01 per request
BOOKING_COM_PRIORITY=1  # Higher = more preferred

# Expedia Rapid API (when you get it)
EXPEDIA_API_KEY=your_expedia_key
EXPEDIA_API_SECRET=your_expedia_secret
EXPEDIA_RATE_LIMIT=300
EXPEDIA_COST_PER_REQUEST=0.015
EXPEDIA_PRIORITY=2

# Agoda API (when you get it)
AGODA_API_KEY=your_agoda_key
AGODA_RATE_LIMIT=100
AGODA_COST_PER_REQUEST=0.02
AGODA_PRIORITY=3

# ===================================================================
# SCRAPING CONFIGURATION
# ===================================================================

ENABLE_SCRAPING=true
SCRAPING_RATE_LIMIT=10  # requests per minute
SCRAPING_COST_PER_REQUEST=0.001  # Proxy cost
SCRAPING_PRIORITY=10  # Lower priority than APIs
SCRAPING_TIMEOUT=60

# ===================================================================
# RECOMMENDED CONFIGURATIONS
# ===================================================================

# Option 1: NO APIs Yet (Current Situation)
# DATA_SOURCE_STRATEGY=scraping_only
# ENABLE_API=false
# ENABLE_SCRAPING=true

# Option 2: Got API, Keep Scraping as Backup
# DATA_SOURCE_STRATEGY=api_first
# ENABLE_API=true
# ENABLE_SCRAPING=true

# Option 3: API Only (Stop Scraping)
# DATA_SOURCE_STRATEGY=api_only
# ENABLE_API=true
# ENABLE_SCRAPING=false

# Option 4: Parallel (Maximum Coverage)
# DATA_SOURCE_STRATEGY=parallel
# ENABLE_API=true
# ENABLE_SCRAPING=true
```

### 2. Basic Usage

```python
from search_booking_module.scraping.hybrid_data_source import (
    HybridDataSourceManager,
    DataSourceStrategy
)
from datetime import date, timedelta

# Initialize with strategy
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.API_FIRST,
    enable_api=True,
    enable_scraping=True
)

# Search hotels
check_in = date.today() + timedelta(days=7)
check_out = check_in + timedelta(days=3)

hotels, source_used = await manager.search_hotels(
    destination="London",
    check_in=check_in,
    check_out=check_out,
    guests=2,
    rooms=1
)

print(f"Found {len(hotels)} hotels via {source_used.value}")

# Get statistics
stats = manager.get_stats()
print(f"API Success Rate: {stats['api']['success_rate']}")
print(f"Scraping Success Rate: {stats['scraping']['success_rate']}")
print(f"Total Cost: API ${stats['api']['total_cost']}, Scraping ${stats['scraping']['total_cost']}")
```

### 3. Dynamic Strategy Switching

```python
# Start with scraping only (no API yet)
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.SCRAPING_ONLY
)

# ... later, when you get API access ...

# Switch to API-first
manager.switch_strategy(DataSourceStrategy.API_FIRST)

# Or stop scraping entirely when API is sufficient
manager.disable_source(DataSourceType.SCRAPING)
```

---

## 🔄 Strategy Details

### 1. API_FIRST (Recommended) ⭐

**Best for**: Production when you have API access

```python
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.API_FIRST,
    enable_api=True,
    enable_scraping=True
)
```

**How it works**:
1. Try all available APIs first
2. If API fails → automatically fall back to scraping
3. Never completely fails (always has backup)

**Advantages**:
- ✅ Fast response (APIs are quick)
- ✅ High quality data
- ✅ Reliable fallback
- ✅ Lower scraping costs (only when needed)

**Cost**: $0.01-0.02 per search (API) + occasional scraping

---

### 2. SCRAPING_ONLY (Current) 🆓

**Best for**: When you don't have API access yet

```python
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.SCRAPING_ONLY,
    enable_api=False,
    enable_scraping=True
)
```

**How it works**:
1. Only uses web scraping
2. No API calls made
3. Uses anti-bot protection (from previous implementation)

**Advantages**:
- ✅ $0/month (no API costs)
- ✅ Works without API credentials
- ✅ Good for getting started

**Cost**: $0-65/month (proxies only, if needed)

---

### 3. API_ONLY

**Best for**: When scraping is blocked or unreliable

```python
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.API_ONLY,
    enable_api=True,
    enable_scraping=False
)
```

**How it works**:
1. Only uses official APIs
2. Fails if API is unavailable (no fallback)
3. Fastest and most reliable

**Advantages**:
- ✅ Fastest response
- ✅ Never gets blocked
- ✅ Highest quality data
- ✅ Easier to scale

**Cost**: $0.01-0.02 per search

---

### 4. PARALLEL (Maximum Coverage)

**Best for**: Comprehensive data collection

```python
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.PARALLEL,
    enable_api=True,
    enable_scraping=True
)
```

**How it works**:
1. Runs API and scraping simultaneously
2. Merges results (deduplicates)
3. Returns combined data

**Advantages**:
- ✅ Maximum hotel coverage
- ✅ Cross-validation of data
- ✅ Redundancy (if one fails, other succeeds)

**Cost**: Highest (both API + scraping)

---

### 5. CHEAPEST

**Best for**: Budget-conscious operation

```python
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.CHEAPEST
)
```

**How it works**:
1. Compares cost_per_request for each source
2. Chooses the cheapest option
3. Usually selects scraping (unless proxies are expensive)

---

### 6. FASTEST

**Best for**: Real-time search requirements

```python
manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.FASTEST
)
```

**How it works**:
1. Chooses based on response time
2. Usually selects API (faster than scraping)
3. Falls back if fastest option unavailable

---

## 📊 Cost Comparison

| Scenario | API Cost | Scraping Cost | Total/Month | Recommended Strategy |
|----------|----------|---------------|-------------|----------------------|
| **No API Yet** | $0 | $0-65 | **$0-65** | `scraping_only` |
| **Got API, Light Use** | $100 | $0 | **$100** | `api_only` |
| **Got API, Medium Use** | $200 | $50 (backup) | **$250** | `api_first` |
| **Got API, Heavy Use** | $500 | $0 (stopped) | **$500** | `api_only` |
| **Maximum Coverage** | $500 | $200 | **$700** | `parallel` |

---

## 🎯 Real-World Examples

### Example 1: Starting Out (No API)

```python
# You are here! No APIs yet, using scraping only

manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.SCRAPING_ONLY,
    enable_api=False,
    enable_scraping=True
)

# Works with current setup (81 hotels populated)
# Cost: $0/month
```

### Example 2: Got Booking.com API

```python
# Great! Now use API first, keep scraping as backup

import os
os.environ["BOOKING_COM_API_KEY"] = "your_key_here"
os.environ["DATA_SOURCE_STRATEGY"] = "api_first"

manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.API_FIRST,
    enable_api=True,
    enable_scraping=True
)

# API handles 90% of requests
# Scraping handles 10% when API fails
# Cost: ~$200/month (mostly API)
```

### Example 3: Multiple APIs

```python
# Even better! Multiple API sources

os.environ["BOOKING_COM_API_KEY"] = "booking_key"
os.environ["EXPEDIA_API_KEY"] = "expedia_key"
os.environ["DATA_SOURCE_STRATEGY"] = "parallel"

manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.PARALLEL,
    enable_api=True,
    enable_scraping=False  # Don't need scraping anymore
)

# APIs handle everything
# Cost: ~$400-600/month (multiple APIs)
```

### Example 4: API Rate Limits Hit

```python
# Temporarily switch when you hit API limits

manager = HybridDataSourceManager(
    strategy=DataSourceStrategy.API_FIRST
)

# Normal operation: uses API
hotels, source = await manager.search_hotels(...)

# API rate limit hit? Automatically switches to scraping!
# No manual intervention needed
```

---

## 🔧 Advanced Configuration

### Prioritizing Providers

```bash
# Lower number = higher priority
BOOKING_COM_PRIORITY=1  # Use first
EXPEDIA_PRIORITY=2      # Use second
AGODA_PRIORITY=3        # Use third
SCRAPING_PRIORITY=10    # Use last
```

### Cost-Based Decisions

```bash
# Set actual costs for optimization
BOOKING_COM_COST_PER_REQUEST=0.01  # $0.01 per request
EXPEDIA_COST_PER_REQUEST=0.015     # $0.015 per request
SCRAPING_COST_PER_REQUEST=0.001    # $0.001 per request (proxies)

# Use CHEAPEST strategy to auto-select
DATA_SOURCE_STRATEGY=cheapest
```

### Rate Limiting

```bash
# Prevent hitting API limits
BOOKING_COM_RATE_LIMIT=60   # 60 requests/minute
EXPEDIA_RATE_LIMIT=300      # 300 requests/minute
SCRAPING_RATE_LIMIT=10      # 10 requests/minute
```

---

## 📈 Monitoring & Stats

```python
# Get real-time statistics
stats = manager.get_stats()

print(f"""
API:
  Enabled: {stats['api']['enabled']}
  Providers: {stats['api']['providers']}
  Success Rate: {stats['api']['success_rate']}
  Total Cost: {stats['api']['total_cost']}

Scraping:
  Enabled: {stats['scraping']['enabled']}
  Scrapers: {stats['scraping']['scrapers']}
  Success Rate: {stats['scraping']['success_rate']}
  Total Cost: {stats['scraping']['total_cost']}

Strategy: {stats['strategy']}
""")
```

---

## 🎉 Migration Path

### Phase 1: Now (No API)
```python
strategy=DataSourceStrategy.SCRAPING_ONLY
enable_api=False
enable_scraping=True
# Cost: $0-65/month
```

### Phase 2: Got API (Use Both)
```python
strategy=DataSourceStrategy.API_FIRST
enable_api=True
enable_scraping=True  # Keep as backup
# Cost: $100-300/month
```

### Phase 3: API Stable (Stop Scraping)
```python
strategy=DataSourceStrategy.API_ONLY
enable_api=True
enable_scraping=False  # Save $65/month on proxies
# Cost: $200-500/month
```

### Phase 4: Multiple APIs (Maximum Quality)
```python
strategy=DataSourceStrategy.PARALLEL
enable_api=True
enable_scraping=False
# Cost: $400-800/month
```

---

## 🆘 Troubleshooting

### Issue 1: "No API providers configured"

**Solution**: Add API keys to `.env`:
```bash
BOOKING_COM_API_KEY=your_key_here
```

### Issue 2: "API rate limit exceeded"

**Solution**: Manager automatically falls back to scraping (if `api_first`) or wait for rate limit to reset

### Issue 3: "Both API and scraping failed"

**Solution**: Check:
- API credentials valid?
- Scrapers configured properly?
- Network connectivity?
- Rate limits not exceeded?

---

## 📚 API Provider Resources

### Getting API Access:

1. **Booking.com Affiliate Partner API**
   - Apply: https://www.booking.com/affiliate-program
   - Free for affiliates
   - Commission-based revenue

2. **Expedia Rapid API**
   - Apply: https://rapidapi.com/apidojo/api/hotels4
   - $0-500/month depending on volume
   - 500 requests/month free tier

3. **Agoda Affiliate API**
   - Apply: https://www.agoda.com/partners
   - Free for affiliates
   - Commission-based

---

## 🎯 Recommended Setup

### For You (Right Now):
```python
# No API yet, use scraping
strategy=DataSourceStrategy.SCRAPING_ONLY
enable_api=False
enable_scraping=True
```

### When You Get API:
```python
# API first, scraping as backup
strategy=DataSourceStrategy.API_FIRST
enable_api=True
enable_scraping=True
```

### When API is Reliable:
```python
# API only, stop scraping costs
strategy=DataSourceStrategy.API_ONLY
enable_api=True
enable_scraping=False
```

---

**🎉 You're ready! The system adapts as your data sources evolve!**
