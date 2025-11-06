# Rate Limiting Explained

## What is Rate Limiting?

**Rate limiting** is a security mechanism that controls how many requests a user or IP address can make to your API within a specific time period. It helps prevent:

- **Brute force attacks** - Hackers trying to guess passwords
- **DDoS attacks** - Overwhelming your server with too many requests
- **API abuse** - Users making excessive requests
- **Resource exhaustion** - Protecting your server from being overloaded

---

## How It Works in This Project

### Example Scenario

Imagine a hacker trying to brute force a login:

1. **Without Rate Limiting:**
   - Hacker tries 10,000 password combinations in 1 minute
   - Server gets overwhelmed
   - Legitimate users can't access the system

2. **With Rate Limiting:**
   - Hacker tries 5 login attempts
   - System blocks further attempts for 1 minute
   - Server stays protected
   - Legitimate users can still access

---

## Rate Limits Configured

### Current Limits

| Endpoint | Limit | Time Window | Purpose |
|----------|-------|-------------|---------|
| **Login** | 5 attempts | 1 minute | Prevent brute force attacks |
| **Registration** | 3 attempts | 1 hour | Prevent spam account creation |
| **Password Reset** | 3 attempts | 1 hour | Prevent email spam |
| **MFA Verification** | 10 attempts | 1 minute | Allow some retries for typos |
| **Token Refresh** | 20 attempts | 1 minute | Allow normal app usage |
| **Tenant Creation** | 5 attempts | 1 hour | Prevent abuse of tenant creation |

### What Happens When Limit is Exceeded?

When a user exceeds the rate limit:

1. **Request is blocked** - Returns HTTP 429 (Too Many Requests)
2. **Error message** - "Rate limit exceeded. Please try again later."
3. **Reset time** - Response headers show when limit resets
4. **Automatic unlock** - After time window expires, user can try again

---

## Technical Implementation

### 1. Rate Limiter Class (`RateLimiter`)

Located in: `backend/auth_module/core/security.py`

**How it works:**
- Uses **Redis** (in-memory database) to track requests
- Implements **sliding window counter** algorithm
- Tracks requests per user/IP address
- Automatically expires old entries

**Key Methods:**
```python
# Check if request is rate limited
is_rate_limited(key, limit, window_seconds)
# Returns: (is_limited, current_count, reset_time)

# Get current rate limit info
get_rate_limit_info(key)
# Returns: current_count, oldest_request, ttl

# Clear rate limit (admin function)
clear_rate_limit(key)
```

### 2. Rate Limit Middleware (`RateLimitMiddleware`)

Located in: `backend/auth_module/api/middleware.py`

**What it does:**
- Intercepts all API requests
- Checks rate limits before processing
- Adds rate limit headers to responses
- Blocks requests that exceed limits

**Response Headers:**
```
X-RateLimit-Limit: 5          # Maximum requests allowed
X-RateLimit-Remaining: 2      # Requests remaining
X-RateLimit-Reset: 1699123456 # Unix timestamp when limit resets
```

### 3. Integration Points

Rate limiting is applied to:

1. **Login endpoint** - Prevents brute force attacks
2. **Registration endpoint** - Prevents spam accounts
3. **Password reset** - Prevents email spam
4. **MFA verification** - Prevents MFA brute force
5. **Token refresh** - Prevents token abuse
6. **Tenant creation** - Prevents tenant spam

---

## Real-World Examples

### Example 1: Login Rate Limiting

**Scenario:** User tries to login

```
Attempt 1: ✅ Success (or fail, but allowed)
Attempt 2: ✅ Allowed
Attempt 3: ✅ Allowed
Attempt 4: ✅ Allowed
Attempt 5: ✅ Allowed
Attempt 6: ❌ BLOCKED - "Rate limit exceeded. Try again in 45 seconds"
```

**After 1 minute:**
```
Attempt 7: ✅ Allowed (limit reset)
```

### Example 2: Registration Rate Limiting

**Scenario:** Someone tries to create multiple accounts

```
Registration 1: ✅ Allowed
Registration 2: ✅ Allowed
Registration 3: ✅ Allowed
Registration 4: ❌ BLOCKED - "Rate limit exceeded. Try again in 1 hour"
```

### Example 3: Password Reset Rate Limiting

**Scenario:** User forgot password and requests reset

```
Request 1: ✅ Email sent
Request 2: ✅ Email sent (maybe first email didn't arrive)
Request 3: ✅ Email sent
Request 4: ❌ BLOCKED - "Too many password reset requests. Try again in 1 hour"
```

---

## Configuration

### Environment Variables

You can configure rate limits in `docker-compose.yml` or `.env`:

```bash
# Login rate limit
RATE_LIMIT_LOGIN=5/minute

# Registration rate limit
RATE_LIMIT_REGISTER=3/hour

# Password reset rate limit
RATE_LIMIT_FORGOT_PASSWORD=3/hour

# MFA verification rate limit
RATE_LIMIT_MFA_VERIFY=10/minute

# Token refresh rate limit
RATE_LIMIT_REFRESH_TOKEN=20/minute

# Tenant creation rate limit
RATE_LIMIT_TENANT_CREATION=5/hour
```

### Format

Rate limits use the format: `{number}/{time_unit}`

- `5/minute` = 5 requests per minute
- `3/hour` = 3 requests per hour
- `100/day` = 100 requests per day

---

## How It's Tracked

### Redis Storage

Rate limits are tracked in Redis using **sorted sets**:

```
Key: "rate_limit:login:user@example.com"
Value: Sorted set of timestamps
```

**Example:**
```
Key: "rate_limit:login:john@example.com"
Timestamps: [1699123400, 1699123405, 1699123410, 1699123415, 1699123420]
Count: 5
```

When a new request comes in:
1. Remove timestamps older than 1 minute
2. Count remaining timestamps
3. If count < limit, add new timestamp
4. If count >= limit, block request

---

## Benefits

### Security Benefits
- ✅ Prevents brute force attacks
- ✅ Protects against DDoS attacks
- ✅ Reduces spam and abuse
- ✅ Protects server resources

### User Experience
- ✅ Legitimate users rarely hit limits
- ✅ Clear error messages
- ✅ Automatic reset
- ✅ Headers show remaining attempts

### Performance
- ✅ Fast Redis lookups
- ✅ Minimal overhead
- ✅ Automatic cleanup of old data
- ✅ Fail-open (if Redis is down, allow requests)

---

## Error Response

When rate limit is exceeded, API returns:

```json
{
  "error": {
    "message": "Rate limit exceeded",
    "code": "RATE_LIMIT_EXCEEDED",
    "details": {
      "limit": "5/minute",
      "reset_time": 1699123456,
      "reset_in_seconds": 45
    }
  }
}
```

**HTTP Status:** `429 Too Many Requests`

**Response Headers:**
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699123456
Retry-After: 45
```

---

## Testing

Rate limiting is tested in the unit tests:

```python
# Test: Registration when rate limited
async def test_register_user_rate_limited(self, auth_service):
    # Setup: Mock rate limiter to return "limited"
    auth_service.rate_limiter.is_rate_limited = Mock(return_value=(True, 3, 3600))
    
    # Execute: Try to register
    with pytest.raises(RateLimitExceededError):
        await auth_service.register_user(...)
```

---

## Summary

**Rate limiting is a security feature that:**
- Limits how many requests users can make
- Prevents brute force and DDoS attacks
- Uses Redis for fast tracking
- Automatically resets after time window
- Provides clear error messages

**In this project:**
- Login: 5 attempts per minute
- Registration: 3 attempts per hour
- Password reset: 3 attempts per hour
- MFA: 10 attempts per minute
- Token refresh: 20 attempts per minute

This protects your authentication system from abuse while allowing legitimate users to use the system normally.

