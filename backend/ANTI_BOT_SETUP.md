# 🛡️ Anti-Bot Protection Setup Guide

Complete guide to implementing proxy rotation, CAPTCHA solving, and anti-detection for production scraping.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features Implemented](#features-implemented)
3. [Quick Start](#quick-start)
4. [Proxy Services](#proxy-services)
5. [CAPTCHA Services](#captcha-services)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Cost Estimates](#cost-estimates)
9. [Best Practices](#best-practices)

---

## Overview

The anti-bot system provides three layers of protection:

1. **Proxy Rotation** - Route requests through residential/datacenter proxies
2. **CAPTCHA Solving** - Automatically solve reCAPTCHA v2/v3, hCaptcha, etc.
3. **Anti-Detection** - Stealth mode, fingerprint randomization, human-like behavior

---

## Features Implemented

### ✅ Proxy Manager (`proxy_manager.py`)
- **Automatic proxy rotation** with health-based selection
- **Health monitoring** - tracks success rate, response time, failures
- **Intelligent failover** - automatically removes bad proxies
- **Geographic targeting** - prefer proxies from specific countries
- **Session management** - rotating and sticky session support
- **Statistics tracking** - detailed metrics per proxy

### ✅ CAPTCHA Solver (`captcha_solver.py`)
- **Multi-service support**: 2Captcha, Anti-Captcha, CapMonster
- **reCAPTCHA v2/v3** solving
- **hCaptcha** support
- **Automatic retry** with timeout handling
- **Balance checking** and cost tracking

### ✅ Anti-Detection (`anti_detection.py`)
- **User-agent rotation** - 15+ realistic browser user agents
- **Browser fingerprinting** - randomized navigator properties
- **Stealth mode** - hide automation detection
- **Canvas fingerprint randomization**
- **WebGL vendor spoofing**
- **Human-like delays** - random timing between requests

---

## Quick Start

### 1. Install Dependencies

Already included in `requirements.txt`:
```
aiohttp>=3.9.0
playwright>=1.40.0
```

### 2. Environment Variables

Add to your `.env` file:

```bash
# Proxy Configuration
ENABLE_PROXIES=true
PROXY_SERVICE=brightdata  # or oxylabs, smartproxy, geonode, proxyrack
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
PROXY_HOST=brd.superproxy.io
PROXY_PORT=22225

# CAPTCHA Configuration
ENABLE_CAPTCHA=true
CAPTCHA_SERVICE=2captcha  # or anticaptcha, capmonster
CAPTCHA_API_KEY=your_api_key_here

# Anti-Detection
ENABLE_STEALTH=true
ROTATE_USER_AGENTS=true
MAX_CONCURRENT_REQUESTS=10
REQUESTS_PER_MINUTE=60
```

### 3. Basic Usage

```python
from search_booking_module.scraping.proxy_manager import ProxyManager
from search_booking_module.scraping.captcha_solver import CaptchaSolver
from search_booking_module.scraping.anti_detection import AntiDetectionManager
from search_booking_module.scraping.anti_bot_config import get_config

# Load configuration
config = get_config("production_full")

# Initialize components
proxy_manager = ProxyManager(
    proxies=[config.get_proxy_url()],
    enable_health_checks=True
)

captcha_solver = CaptchaSolver(
    service=config.captcha_service,
    api_key=config.captcha_api_key
)

anti_detection = AntiDetectionManager()

# Start proxy health monitoring
await proxy_manager.start()

# Get a proxy for your request
proxy = await proxy_manager.get_proxy()

# Get stealth headers
headers = anti_detection.get_request_headers()

# Make your request with proxy
async with aiohttp.ClientSession() as session:
    async with session.get(
        url,
        proxy=proxy.url if proxy else None,
        headers=headers
    ) as response:
        html = await response.text()

# Record result
if proxy:
    await proxy_manager.record_result(
        proxy,
        success=response.status == 200,
        response_time=response.elapsed.total_seconds()
    )
```

---

## Proxy Services

### Recommended Services

#### 1. **Bright Data (formerly Luminati)** 💎
- **Best for**: Enterprise, high-volume scraping
- **Network**: 72M+ residential IPs, all countries
- **Pricing**: $15/GB residential, $500/month unlimited datacenter
- **Setup**:
  ```bash
  PROXY_SERVICE=brightdata
  PROXY_USERNAME=your-customer-id
  PROXY_PASSWORD=your-zone-password
  PROXY_HOST=brd.superproxy.io
  PROXY_PORT=22225
  ```

#### 2. **Oxylabs** 🚀
- **Best for**: Professional scraping, good balance
- **Network**: 100M+ residential IPs
- **Pricing**: $8/GB residential, $300/month datacenter
- **Setup**:
  ```bash
  PROXY_SERVICE=oxylabs
  PROXY_USERNAME=your-username
  PROXY_PASSWORD=your-password
  PROXY_HOST=pr.oxylabs.io
  PROXY_PORT=7777
  ```

#### 3. **SmartProxy** 💰
- **Best for**: Budget-friendly, good reliability
- **Network**: 40M+ residential IPs
- **Pricing**: $12.50/GB, volume discounts
- **Setup**:
  ```bash
  PROXY_SERVICE=smartproxy
  PROXY_USERNAME=your-username
  PROXY_PASSWORD=your-password
  PROXY_HOST=gate.smartproxy.com
  PROXY_PORT=7000
  ```

#### 4. **GeoNode** 🌍
- **Best for**: Cheapest residential proxies
- **Network**: 2M+ residential IPs
- **Pricing**: $3/GB residential
- **Setup**:
  ```bash
  PROXY_SERVICE=geonode
  PROXY_USERNAME=your-username
  PROXY_PASSWORD=your-password
  PROXY_HOST=premium-residential.geonode.com
  PROXY_PORT=9000
  ```

#### 5. **ProxyRack** 🔥
- **Best for**: Unlimited scraping
- **Network**: 5M+ residential IPs
- **Pricing**: $65/month UNLIMITED residential
- **Setup**:
  ```bash
  PROXY_SERVICE=proxyrack
  PROXY_USERNAME=your-username
  PROXY_PASSWORD=your-password
  PROXY_HOST=residential.proxyrack.net
  PROXY_PORT=10000
  ```

---

## CAPTCHA Services

### Supported Services

#### 1. **2Captcha** (Recommended) 💯
- **Website**: https://2captcha.com
- **Pricing**: 
  - reCAPTCHA v2: $2.99/1000
  - reCAPTCHA v3: $3.00/1000
  - hCaptcha: $2.99/1000
- **Pros**: Most popular, excellent documentation, reliable
- **Setup**:
  ```bash
  CAPTCHA_SERVICE=2captcha
  CAPTCHA_API_KEY=your_api_key_from_2captcha
  ```

#### 2. **Anti-Captcha** 🏃
- **Website**: https://anti-captcha.com
- **Pricing**: $1.80-$2.00/1000 reCAPTCHA
- **Pros**: Fastest solving, good API
- **Setup**:
  ```bash
  CAPTCHA_SERVICE=anticaptcha
  CAPTCHA_API_KEY=your_api_key_from_anticaptcha
  ```

#### 3. **CapMonster Cloud** 💵
- **Website**: https://capmonster.cloud
- **Pricing**: $0.60-$2.40/1000 (cheapest!)
- **Pros**: Best prices, good speed
- **Setup**:
  ```bash
  CAPTCHA_SERVICE=capmonster
  CAPTCHA_API_KEY=your_api_key_from_capmonster
  ```

### CAPTCHA Solving Example

```python
from search_booking_module.scraping.captcha_solver import CaptchaSolver

solver = CaptchaSolver(service="2captcha", api_key="YOUR_API_KEY")

# Solve reCAPTCHA v2
token = await solver.solve_recaptcha_v2(
    site_key="6Le-wvkSAAAAAPBMRTvw0Q...",
    page_url="https://www.booking.com/hotel/..."
)

# Use token in your request or browser
await page.evaluate(f"""
    document.getElementById('g-recaptcha-response').innerHTML = '{token}';
""")
```

---

## Configuration

### Configuration Profiles

We provide 4 pre-configured profiles:

#### 1. **Development** (No cost)
```python
config = get_config("development")
# - No proxies
# - No CAPTCHA solving
# - Stealth mode enabled
# - 2 concurrent, 10 req/min
```

#### 2. **Production Light** ($50-100/month)
```python
config = get_config("production_light")
# - Cheap proxies (GeoNode)
# - No CAPTCHA solving
# - Full stealth mode
# - 5 concurrent, 30 req/min
```

#### 3. **Production Full** ($200-500/month)
```python
config = get_config("production_full")
# - Premium proxies (Bright Data)
# - CAPTCHA solving (2Captcha)
# - Full anti-detection
# - 10 concurrent, 60 req/min
```

#### 4. **Aggressive** ($500-1000/month)
```python
config = get_config("aggressive")
# - Premium proxies (SmartProxy)
# - Fast CAPTCHA solving (Anti-Captcha)
# - Maximum stealth
# - 20 concurrent, 120 req/min
```

---

## Usage Examples

### Example 1: Simple Proxy Rotation

```python
from search_booking_module.scraping.proxy_manager import ProxyManager

# Initialize with multiple proxies
proxies = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
    "http://user:pass@proxy3.example.com:8080",
]

proxy_manager = ProxyManager(proxies=proxies)
await proxy_manager.start()

# Get best proxy
proxy = await proxy_manager.get_proxy()

# Use in request
response = await fetch_with_proxy(url, proxy.url)

# Record result
await proxy_manager.record_result(
    proxy,
    success=True,
    response_time=1.5
)
```

### Example 2: Full Anti-Bot Protection

```python
import asyncio
from playwright.async_api import async_playwright

async def scrape_with_full_protection(url):
    # Initialize all components
    config = get_config("production_full")
    proxy_manager = ProxyManager([config.get_proxy_url()])
    captcha_solver = CaptchaSolver(
        service=config.captcha_service,
        api_key=config.captcha_api_key
    )
    anti_detection = AntiDetectionManager()
    
    await proxy_manager.start()
    
    # Get proxy and fingerprint
    proxy = await proxy_manager.get_proxy()
    fingerprint = anti_detection.get_browser_fingerprint()
    
    async with async_playwright() as p:
        # Launch with proxy
        browser = await p.chromium.launch(
            proxy={"server": proxy.url} if proxy else None
        )
        
        # Create context with fingerprint
        context = await browser.new_context(
            **fingerprint.playwright_context_options
        )
        
        page = await context.new_page()
        
        # Apply stealth mode
        await anti_detection.apply_stealth_mode(page)
        
        # Navigate
        await page.goto(url)
        
        # Check for CAPTCHA
        if await page.locator("#g-recaptcha").is_visible():
            site_key = await page.get_attribute("#g-recaptcha", "data-sitekey")
            token = await captcha_solver.solve_recaptcha_v2(site_key, url)
            
            if token:
                await page.evaluate(f"""
                    document.getElementById('g-recaptcha-response').innerHTML = '{token}';
                """)
        
        # Extract data
        content = await page.content()
        
        await browser.close()
    
    await proxy_manager.stop()
    return content
```

---

## Cost Estimates

### Monthly Cost Breakdown

| **Scenario** | **Proxies** | **CAPTCHA** | **Total/Month** |
|--------------|-------------|-------------|-----------------|
| **Development** | $0 | $0 | **$0** |
| **Small Scale** (10K requests) | $30 | $0 | **$30** |
| **Medium Scale** (100K requests) | $150 | $20 | **$170** |
| **Large Scale** (1M requests) | $500 | $100 | **$600** |
| **Enterprise** (10M+ requests) | $2,000 | $500 | **$2,500** |

### Cost Optimization Tips

1. **Use datacenter proxies** for less protected sites (5x cheaper)
2. **Avoid CAPTCHA** by better stealth techniques (save 90%)
3. **Rotate proxies** less frequently (reduce bandwidth costs)
4. **Cache aggressively** (reduce total requests by 50-80%)
5. **Use ProxyRack** unlimited plan for high-volume ($65/month flat)

---

## Best Practices

### ✅ DO

1. **Start without proxies** in development
2. **Test with small batches** before scaling
3. **Monitor proxy health** regularly
4. **Rotate sessions** every 50-100 requests
5. **Add random delays** (1-3 seconds) between requests
6. **Respect robots.txt** and rate limits
7. **Handle errors gracefully** with retries
8. **Use residential proxies** for protected sites
9. **Cache responses** to reduce requests
10. **Monitor costs** daily

### ❌ DON'T

1. **Don't hammer** sites with 100s of concurrent requests
2. **Don't use the same** proxy for all requests
3. **Don't skip** anti-detection techniques
4. **Don't ignore** 429 (rate limit) responses
5. **Don't scrape** without permission on sensitive sites
6. **Don't use free proxies** in production (unreliable)
7. **Don't forget** to rotate user agents
8. **Don't keep** dead proxies in the pool
9. **Don't solve CAPTCHAs** if you can avoid them
10. **Don't exceed** your proxy bandwidth limits

---

## Testing

Test your anti-bot setup:

```bash
# Test proxy connectivity
docker compose exec backend python -c "
from search_booking_module.scraping.proxy_manager import ProxyManager
import asyncio

async def test():
    pm = ProxyManager(['YOUR_PROXY_URL'])
    await pm.start()
    proxy = await pm.get_proxy()
    result = await pm.check_proxy_health(proxy)
    print(f'Proxy working: {result}')
    print(pm.get_stats())
    await pm.stop()

asyncio.run(test())
"

# Test CAPTCHA solver
docker compose exec backend python -c "
from search_booking_module.scraping.captcha_solver import CaptchaSolver
import asyncio

async def test():
    solver = CaptchaSolver('2captcha', 'YOUR_API_KEY')
    # Test with a demo site
    result = await solver.solve_recaptcha_v2(
        '6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',
        'https://www.google.com/recaptcha/api2/demo'
    )
    print(f'CAPTCHA solved: {result is not None}')

asyncio.run(test())
"
```

---

## Support

For issues or questions:
1. Check proxy service documentation
2. Verify API keys are correct
3. Test with a single request first
4. Check proxy manager statistics
5. Enable debug logging

---

**🎉 You're now ready to scrape at scale with full anti-bot protection!**

