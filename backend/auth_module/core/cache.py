"""Redis caching utilities."""

import json
import redis
from typing import Optional, Any, Callable
from functools import wraps
from ..core.config import config
import logging

logger = logging.getLogger(__name__)

# Initialize Redis connection
try:
    cache_client = redis.from_url(config.redis_url, decode_responses=False)
    cache_client.ping()
    cache_available = True
    logger.info("Redis cache initialized successfully")
except Exception as e:
    cache_available = False
    cache_client = None
    logger.warning(f"Redis cache not available: {e}. Caching disabled.")


def get_cache() -> Optional[redis.Redis]:
    """Get Redis cache client."""
    return cache_client if cache_available else None


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments."""
    key_parts = [prefix]
    if args:
        key_parts.extend(str(arg) for arg in args)
    if kwargs:
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def get_cached(key: str) -> Optional[Any]:
    """Get value from cache."""
    if not cache_available:
        return None
    
    try:
        value = cache_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache get error for key {key}: {e}")
    return None


def set_cached(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL."""
    if not cache_available:
        return False
    
    try:
        cache_client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.warning(f"Cache set error for key {key}: {e}")
    return False


def delete_cached(key: str) -> bool:
    """Delete value from cache."""
    if not cache_available:
        return False
    
    try:
        cache_client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete error for key {key}: {e}")
    return False


def cached(ttl: int = 3600, key_prefix: str = "cache"):
    """
    Decorator to cache function results.
    
    Usage:
        @cached(ttl=600, key_prefix="hotel")
        def get_hotel(hotel_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = get_cached(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            set_cached(key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = get_cached(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            set_cached(key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache entries matching pattern."""
    if not cache_available:
        return 0
    
    try:
        keys = cache_client.keys(pattern)
        if keys:
            return cache_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache invalidation error for pattern {pattern}: {e}")
    return 0

