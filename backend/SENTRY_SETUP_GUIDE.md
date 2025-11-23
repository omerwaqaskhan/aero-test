# Sentry Error Tracking Setup Guide

This guide explains how to set up Sentry for error tracking and monitoring in the LuftWay platform.

## What is Sentry?

Sentry is an error tracking and performance monitoring platform that helps you:
- Track errors in real-time
- Get alerts when issues occur
- Monitor application performance
- Debug issues with stack traces and context

## Prerequisites

1. Sentry account (sign up at https://sentry.io)
2. Sentry project created
3. DSN (Data Source Name) from your Sentry project

## Quick Setup

### Step 1: Get Your Sentry DSN

1. Go to https://sentry.io and sign in
2. Create a new project (or use existing)
3. Select "FastAPI" as the platform
4. Copy your DSN (looks like: `https://xxxxx@xxxxx.ingest.sentry.io/xxxxx`)

### Step 2: Configure Environment Variables

Add to your `.env` file or `docker-compose.yml`:

```bash
# Enable Sentry
ENABLE_SENTRY=true

# Your Sentry DSN
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx

# Environment name (development, staging, production)
SENTRY_ENVIRONMENT=production

# Performance monitoring (0.0 to 1.0)
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_PROFILES_SAMPLE_RATE=1.0

# Optional: Release version (e.g., git commit hash)
SENTRY_RELEASE=1.0.0
```

### Step 3: Install Dependencies

The Sentry SDK is already in `requirements.txt`. If you need to install manually:

```bash
pip install sentry-sdk[fastapi]
```

### Step 4: Restart Services

```bash
docker compose restart backend
```

## Configuration Details

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENABLE_SENTRY` | Enable/disable Sentry | `false` | No |
| `SENTRY_DSN` | Your Sentry project DSN | None | Yes (if enabled) |
| `SENTRY_ENVIRONMENT` | Environment name | `development` | No |
| `SENTRY_TRACES_SAMPLE_RATE` | Performance trace sampling (0.0-1.0) | `1.0` | No |
| `SENTRY_PROFILES_SAMPLE_RATE` | Profile sampling (0.0-1.0) | `1.0` | No |
| `SENTRY_RELEASE` | Release version | None | No |

### Sample Rates

- **1.0** = 100% of transactions (use for development)
- **0.1** = 10% of transactions (recommended for production)
- **0.0** = Disable performance monitoring

For high-traffic production environments, use lower sample rates (0.1-0.2) to reduce overhead.

## Features Enabled

### 1. Error Tracking
- Automatic exception capture
- Stack traces with context
- Request information (headers, params, body)
- User context (if available)

### 2. Performance Monitoring
- Transaction tracking
- Database query monitoring
- API endpoint performance
- Slow query detection

### 3. Integrations
- **FastAPI Integration**: Automatic error capture
- **SQLAlchemy Integration**: Database query tracking
- **Logging Integration**: Log-based error capture

## Testing Sentry

### Test Error Capture

Create a test endpoint to verify Sentry is working:

```python
@app.get("/test-sentry")
async def test_sentry():
    """Test endpoint to verify Sentry error tracking."""
    try:
        raise ValueError("This is a test error for Sentry")
    except Exception as e:
        # Sentry will automatically capture this
        raise
```

Visit: `http://localhost:8000/test-sentry`

You should see the error appear in your Sentry dashboard within seconds.

### Test Performance Monitoring

Sentry automatically tracks all API endpoints. Check your Sentry dashboard's Performance section to see:
- Endpoint response times
- Database query performance
- Slow transactions

## Production Best Practices

### 1. Use Different Projects per Environment

Create separate Sentry projects for:
- Development
- Staging
- Production

Use different DSNs for each environment.

### 2. Set Appropriate Sample Rates

```bash
# Development
SENTRY_TRACES_SAMPLE_RATE=1.0

# Production (high traffic)
SENTRY_TRACES_SAMPLE_RATE=0.1

# Production (low traffic)
SENTRY_TRACES_SAMPLE_RATE=0.5
```

### 3. Configure Alerts

In Sentry dashboard:
1. Go to Alerts
2. Create alert rules for:
   - Critical errors (new issues)
   - High error rate
   - Slow transactions
   - Failed deployments

### 4. Set Release Versions

Track which version of your code caused errors:

```bash
# In CI/CD pipeline
SENTRY_RELEASE=$(git rev-parse HEAD)
```

### 5. Filter Sensitive Data

Sentry automatically filters common sensitive fields, but you can add custom filters in the Sentry dashboard:
- Settings → Security & Privacy → Data Scrubbing

## Troubleshooting

### Sentry Not Capturing Errors

1. **Check if Sentry is enabled:**
   ```bash
   echo $ENABLE_SENTRY  # Should be "true"
   echo $SENTRY_DSN     # Should have a valid DSN
   ```

2. **Check logs:**
   ```bash
   docker logs luftway-backend | grep -i sentry
   ```

3. **Verify DSN format:**
   - Should start with `https://`
   - Should contain `@` and `.ingest.sentry.io`

### High Overhead

If Sentry is causing performance issues:
- Reduce `SENTRY_TRACES_SAMPLE_RATE` to 0.1 or lower
- Disable `SENTRY_PROFILES_SAMPLE_RATE` (set to 0.0)
- Use Sentry's sampling configuration in dashboard

### Too Many Errors

If you're getting too many errors:
- Set up issue grouping rules in Sentry
- Configure alert thresholds
- Use Sentry's "Ignore" feature for known issues

## Security Considerations

1. **DSN is Public**: Sentry DSNs are safe to expose in frontend code, but keep them in environment variables for backend
2. **PII Filtering**: Sentry automatically filters passwords, tokens, etc.
3. **IP Addresses**: Consider anonymizing IP addresses in Sentry settings
4. **Data Retention**: Configure data retention policies in Sentry (Settings → General)

## Cost Considerations

Sentry offers:
- **Free Tier**: 5,000 errors/month, 1 project
- **Team Tier**: $26/month - 50,000 errors/month, unlimited projects
- **Business Tier**: $80/month - 200,000 errors/month

For production, consider:
- Setting up alert thresholds to avoid spam
- Using appropriate sample rates
- Configuring data retention policies

## Additional Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Alert Configuration](https://docs.sentry.io/product/alerts/)

