"""Cache service for Redis operations."""

import json
import pickle
from typing import Any, Optional, Dict, List
import redis
from ..core.config import config
from ..core.exceptions import SystemError


class CacheService:
    """Redis cache service."""
    
    def __init__(self):
        self.redis_client = redis.from_url(config.redis_url, decode_responses=False)
        self.default_ttl = config.cache_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            # Fail silently for cache operations
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.default_ttl
            
            # Try to serialize as JSON first, then pickle
            try:
                serialized_value = json.dumps(value).encode('utf-8')
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value)
            
            return self.redis_client.setex(key, ttl, serialized_value)
            
        except Exception as e:
            # Fail silently for cache operations
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key."""
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception:
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key."""
        try:
            return self.redis_client.ttl(key)
        except Exception:
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache."""
        try:
            return self.redis_client.incrby(key, amount)
        except Exception:
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement counter in cache."""
        try:
            return self.redis_client.decrby(key, amount)
        except Exception:
            return None
    
    async def get_hash(self, key: str, field: str) -> Optional[str]:
        """Get hash field value."""
        try:
            value = self.redis_client.hget(key, field)
            return value.decode('utf-8') if value else None
        except Exception:
            return None
    
    async def set_hash(self, key: str, field: str, value: str) -> bool:
        """Set hash field value."""
        try:
            return bool(self.redis_client.hset(key, field, value))
        except Exception:
            return False
    
    async def get_all_hash(self, key: str) -> Dict[str, str]:
        """Get all hash fields."""
        try:
            hash_data = self.redis_client.hgetall(key)
            return {k.decode('utf-8'): v.decode('utf-8') for k, v in hash_data.items()}
        except Exception:
            return {}
    
    async def delete_hash_field(self, key: str, field: str) -> bool:
        """Delete hash field."""
        try:
            return bool(self.redis_client.hdel(key, field))
        except Exception:
            return False
    
    async def add_to_set(self, key: str, *values: str) -> int:
        """Add values to set."""
        try:
            return self.redis_client.sadd(key, *values)
        except Exception:
            return 0
    
    async def remove_from_set(self, key: str, *values: str) -> int:
        """Remove values from set."""
        try:
            return self.redis_client.srem(key, *values)
        except Exception:
            return 0
    
    async def is_in_set(self, key: str, value: str) -> bool:
        """Check if value is in set."""
        try:
            return bool(self.redis_client.sismember(key, value))
        except Exception:
            return False
    
    async def get_set_members(self, key: str) -> List[str]:
        """Get all set members."""
        try:
            members = self.redis_client.smembers(key)
            return [m.decode('utf-8') for m in members]
        except Exception:
            return []
    
    async def push_to_list(self, key: str, *values: str) -> int:
        """Push values to list."""
        try:
            return self.redis_client.lpush(key, *values)
        except Exception:
            return 0
    
    async def pop_from_list(self, key: str) -> Optional[str]:
        """Pop value from list."""
        try:
            value = self.redis_client.rpop(key)
            return value.decode('utf-8') if value else None
        except Exception:
            return None
    
    async def get_list_length(self, key: str) -> int:
        """Get list length."""
        try:
            return self.redis_client.llen(key)
        except Exception:
            return 0
    
    async def get_list_range(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get list range."""
        try:
            values = self.redis_client.lrange(key, start, end)
            return [v.decode('utf-8') for v in values]
        except Exception:
            return []
    
    async def flush_all(self) -> bool:
        """Flush all cache data."""
        try:
            return self.redis_client.flushall()
        except Exception:
            return False
    
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server info."""
        try:
            info = self.redis_client.info()
            return {
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses")
            }
        except Exception:
            return {}
    
    def get_tenant_key(self, tenant_id: str, key: str) -> str:
        """Get tenant-scoped cache key."""
        return f"tenant:{tenant_id}:{key}"
    
    def get_user_key(self, user_id: str, key: str) -> str:
        """Get user-scoped cache key."""
        return f"user:{user_id}:{key}"
    
    def get_session_key(self, session_id: str) -> str:
        """Get session cache key."""
        return f"session:{session_id}"
    
    def get_rate_limit_key(self, identifier: str, action: str) -> str:
        """Get rate limit cache key."""
        return f"rate_limit:{action}:{identifier}"
