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

