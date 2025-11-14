"""Configuration for hotel data collection."""

import os
from typing import List, Dict

# Scheduler configuration
AUTO_POPULATE_ON_STARTUP = os.getenv("AUTO_POPULATE_ON_STARTUP", "true").lower() == "true"
AUTO_REFRESH_ENABLED = os.getenv("AUTO_REFRESH_ENABLED", "true").lower() == "true"
REFRESH_TIME = os.getenv("REFRESH_TIME", "02:00")  # Default: 2 AM daily
REFRESH_INTERVAL_HOURS = int(os.getenv("REFRESH_INTERVAL_HOURS", "24"))

# Scraping configuration
MAX_HOTELS_PER_DESTINATION = int(os.getenv("MAX_HOTELS_PER_DESTINATION", "50"))
SCRAPING_DELAY_SECONDS = float(os.getenv("SCRAPING_DELAY_SECONDS", "1.0"))
SCRAPER_RATE_LIMIT = float(os.getenv("SCRAPER_RATE_LIMIT", "2.0"))  # requests per second
SCRAPER_MAX_CONCURRENT = int(os.getenv("SCRAPER_MAX_CONCURRENT", "5"))
SCRAPER_MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "30"))

# Proxy configuration
SCRAPER_PROXIES = os.getenv("SCRAPER_PROXIES", "").split(",") if os.getenv("SCRAPER_PROXIES") else []
SCRAPER_PROXIES = [p.strip() for p in SCRAPER_PROXIES if p.strip()]  # Clean and filter empty

# Monitoring configuration
MONITORING_RETENTION_HOURS = int(os.getenv("MONITORING_RETENTION_HOURS", "24"))
MONITORING_SUCCESS_RATE_MIN = float(os.getenv("MONITORING_SUCCESS_RATE_MIN", "0.8"))  # 80%
MONITORING_RESPONSE_TIME_MAX = float(os.getenv("MONITORING_RESPONSE_TIME_MAX", "10.0"))  # 10 seconds
MONITORING_ERROR_RATE_MAX = float(os.getenv("MONITORING_ERROR_RATE_MAX", "0.2"))  # 20%
MONITORING_CONSECUTIVE_FAILURES_MAX = int(os.getenv("MONITORING_CONSECUTIVE_FAILURES_MAX", "5"))

# Alerting configuration
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "")
ALERT_EMAIL_ENABLED = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
ALERT_MAX_ALERTS = int(os.getenv("ALERT_MAX_ALERTS", "1000"))

# Price checking configuration
PRICE_CHECK_ENABLED = os.getenv("PRICE_CHECK_ENABLED", "true").lower() == "true"
PRICE_CHECK_INTERVAL_HOURS = int(os.getenv("PRICE_CHECK_INTERVAL_HOURS", "6"))
PRICE_CHECK_MAX_CONCURRENT = int(os.getenv("PRICE_CHECK_MAX_CONCURRENT", "10"))
PRICE_CHECK_MAX_AGE_HOURS = int(os.getenv("PRICE_CHECK_MAX_AGE_HOURS", "24"))

# Proxy pool configuration
PROXY_POOL_HEALTH_CHECK_INTERVAL = int(os.getenv("PROXY_POOL_HEALTH_CHECK_INTERVAL", "300"))  # 5 minutes
PROXY_POOL_MAX_CONSECUTIVE_FAILURES = int(os.getenv("PROXY_POOL_MAX_CONSECUTIVE_FAILURES", "3"))
PROXY_POOL_MIN_SUCCESS_RATE = float(os.getenv("PROXY_POOL_MIN_SUCCESS_RATE", "0.5"))  # 50%

# Popular destinations for initial population
POPULAR_DESTINATIONS = [
    {"city": "New York", "country": "USA"},
    {"city": "Paris", "country": "France"},
    {"city": "London", "country": "UK"},
    {"city": "Tokyo", "country": "Japan"},
    {"city": "Dubai", "country": "UAE"},
    {"city": "Barcelona", "country": "Spain"},
    {"city": "Rome", "country": "Italy"},
    {"city": "Amsterdam", "country": "Netherlands"},
    {"city": "Bangkok", "country": "Thailand"},
    {"city": "Singapore", "country": "Singapore"},
    {"city": "Sydney", "country": "Australia"},
    {"city": "Los Angeles", "country": "USA"},
    {"city": "Berlin", "country": "Germany"},
    {"city": "Vienna", "country": "Austria"},
    {"city": "Prague", "country": "Czech Republic"},
    {"city": "Istanbul", "country": "Turkey"},
    {"city": "Cairo", "country": "Egypt"},
    {"city": "Mumbai", "country": "India"},
    {"city": "Shanghai", "country": "China"},
    {"city": "Hong Kong", "country": "China"},
]

