# Scraper Configuration Guide

## Environment Variables

All scraper-related configuration is done through environment variables. Update `docker-compose.yml` or set them in your environment.

### Proxy Configuration

To use proxies for scraping, set the `SCRAPER_PROXIES` environment variable:

```yaml
# In docker-compose.yml
SCRAPER_PROXIES: "http://proxy1.example.com:8080,http://proxy2.example.com:8080,http://user:pass@proxy3.example.com:8080"
```

**Format**: Comma-separated list of proxy URLs
- HTTP proxies: `http://proxy:port`
- HTTPS proxies: `https://proxy:port`
- Authenticated proxies: `http://username:password@proxy:port`

**Example**:
```bash
SCRAPER_PROXIES=http://proxy1:8080,http://proxy2:8080,http://user:pass@proxy3:3128
```

### Webhook URL for Alerts

To receive alerts via webhook:

```yaml
# In docker-compose.yml
ALERT_WEBHOOK_URL: "https://your-webhook-url.com/alerts"
```

The webhook will receive POST requests with alert data in JSON format:
```json
{
  "id": "alert_id",
  "severity": "warning",
  "title": "Alert Title",
  "message": "Alert message",
  "source": "scraper_name",
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {}
}
```

### Monitoring Thresholds

Adjust monitoring thresholds to match your requirements:

```yaml
# Success rate threshold (0.0 to 1.0)
MONITORING_SUCCESS_RATE_MIN: 0.8  # Alert if success rate < 80%

# Response time threshold (seconds)
MONITORING_RESPONSE_TIME_MAX: 10.0  # Alert if avg response time > 10s

# Error rate threshold (0.0 to 1.0)
MONITORING_ERROR_RATE_MAX: 0.2  # Alert if error rate > 20%

# Consecutive failures threshold
MONITORING_CONSECUTIVE_FAILURES_MAX: 5  # Alert after 5 consecutive failures
```

### Price Checking Configuration

```yaml
# Enable/disable price checking
PRICE_CHECK_ENABLED: true

# Hours between price checks
PRICE_CHECK_INTERVAL_HOURS: 6

# Maximum concurrent price checks
PRICE_CHECK_MAX_CONCURRENT: 10

# Maximum age of price data before checking (hours)
PRICE_CHECK_MAX_AGE_HOURS: 24
```

### Proxy Pool Configuration

```yaml
# Health check interval (seconds)
PROXY_POOL_HEALTH_CHECK_INTERVAL: 300  # 5 minutes

# Max consecutive failures before deactivating proxy
PROXY_POOL_MAX_CONSECUTIVE_FAILURES: 3

# Minimum success rate to keep proxy active (0.0 to 1.0)
PROXY_POOL_MIN_SUCCESS_RATE: 0.5  # 50%
```

### Scraping Configuration

```yaml
# Rate limit (requests per second)
SCRAPER_RATE_LIMIT: 2.0

# Maximum concurrent scraping tasks
SCRAPER_MAX_CONCURRENT: 5

# Maximum retry attempts
SCRAPER_MAX_RETRIES: 3

# Request timeout (seconds)
SCRAPER_TIMEOUT: 30
```

## Complete Configuration Example

Add to `docker-compose.yml` under `backend.environment`:

```yaml
# Scraping Configuration
SCRAPER_RATE_LIMIT: 2.0
SCRAPER_MAX_CONCURRENT: 5
SCRAPER_MAX_RETRIES: 3
SCRAPER_TIMEOUT: 30

# Proxy Configuration
SCRAPER_PROXIES: "http://proxy1:8080,http://proxy2:8080"

# Monitoring Configuration
MONITORING_RETENTION_HOURS: 24
MONITORING_SUCCESS_RATE_MIN: 0.8
MONITORING_RESPONSE_TIME_MAX: 10.0
MONITORING_ERROR_RATE_MAX: 0.2
MONITORING_CONSECUTIVE_FAILURES_MAX: 5

# Alerting Configuration
ALERT_WEBHOOK_URL: "https://your-webhook-url.com/alerts"
ALERT_EMAIL_ENABLED: false
ALERT_MAX_ALERTS: 1000

# Price Checking Configuration
PRICE_CHECK_ENABLED: true
PRICE_CHECK_INTERVAL_HOURS: 6
PRICE_CHECK_MAX_CONCURRENT: 10
PRICE_CHECK_MAX_AGE_HOURS: 24

# Proxy Pool Configuration
PROXY_POOL_HEALTH_CHECK_INTERVAL: 300
PROXY_POOL_MAX_CONSECUTIVE_FAILURES: 3
PROXY_POOL_MIN_SUCCESS_RATE: 0.5
```

## How It Works

### Automatic Configuration Loading

All services automatically load configuration from environment variables:
- **Data Collector**: Uses `SCRAPER_PROXIES`, `SCRAPER_RATE_LIMIT`, `SCRAPER_MAX_CONCURRENT`
- **Monitoring**: Uses `MONITORING_*` variables for thresholds
- **Alerting**: Uses `ALERT_*` variables for webhook/email
- **Price Checker**: Uses `PRICE_CHECK_*` variables
- **Proxy Pool**: Uses `PROXY_POOL_*` variables

### Price Monitoring Service

The price monitoring service:
- Starts automatically when the scheduler starts (if `PRICE_CHECK_ENABLED=true`)
- Checks prices every `PRICE_CHECK_INTERVAL_HOURS` hours
- Updates prices for hotels with data older than `PRICE_CHECK_MAX_AGE_HOURS` hours
- Runs in the background without blocking other operations

### Proxy Pool

The proxy pool:
- Automatically rotates proxies
- Monitors proxy health every `PROXY_POOL_HEALTH_CHECK_INTERVAL` seconds
- Deactivates unhealthy proxies
- Reactivates proxies when they recover
- Selects proxies based on health scores

## Testing Configuration

After updating configuration, restart the services:

```bash
docker compose restart backend
```

Check logs to verify configuration:
```bash
docker compose logs backend | grep -i "proxy\|monitoring\|price"
```

## Verification

1. **Check Proxy Pool**: Visit `/api/v1/monitoring/proxies` (when implemented)
2. **Check Monitoring**: Visit `/api/v1/monitoring/dashboard`
3. **Check Alerts**: Visit `/api/v1/monitoring/alerts`
4. **Check Price Service**: Check logs for "Price monitor service started"

## Notes

- Proxies are optional - if not configured, scrapers use direct connections
- Webhook URL is optional - if not configured, alerts are only logged
- Price monitoring runs automatically in the background
- All thresholds can be adjusted based on your needs

