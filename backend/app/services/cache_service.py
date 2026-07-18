"""Cache Service - Redis-based caching for module results"""
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta

from app.core.redis import get_redis


class CacheService:
    """Service for caching module results in Redis"""
    
    def __init__(self):
        self.default_ttl = 3600  # 1 hour default
        self.prefix = "osif:cache:"
    
    def _generate_key(self, module_id: str, target: str, kind: str) -> str:
        """Generate cache key from module and target"""
        # Create deterministic hash
        data = f"{module_id}:{kind}:{target.lower().strip()}"
        hash_key = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"{self.prefix}{module_id}:{hash_key}"
    
    async def get(
        self,
        module_id: str,
        target: str,
        kind: str
    ) -> Optional[list]:
        """Get cached module results"""
        
        redis = await get_redis()
        key = self._generate_key(module_id, target, kind)
        
        cached = await redis.get(key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                # Invalid cache, delete it
                await redis.delete(key)
                return None
        
        return None
    
    async def set(
        self,
        module_id: str,
        target: str,
        kind: str,
        results: list,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache module results"""
        
        redis = await get_redis()
        key = self._generate_key(module_id, target, kind)
        
        try:
            serialized = json.dumps(results, default=str)
            await redis.setex(
                key,
                ttl or self.default_ttl,
                serialized
            )
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def invalidate(
        self,
        module_id: str,
        target: str,
        kind: str
    ) -> bool:
        """Invalidate cached results"""
        
        redis = await get_redis()
        key = self._generate_key(module_id, target, kind)
        
        deleted = await redis.delete(key)
        return deleted > 0
    
    async def clear_module_cache(self, module_id: str) -> int:
        """Clear all cache entries for a module"""
        
        redis = await get_redis()
        pattern = f"{self.prefix}{module_id}:*"
        
        # Find all keys matching pattern
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        
        # Delete all found keys
        if keys:
            return await redis.delete(*keys)
        return 0
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        
        redis = await get_redis()
        
        # Count total cached items
        total_keys = 0
        async for _ in redis.scan_iter(match=f"{self.prefix}*"):
            total_keys += 1
        
        # Get Redis info
        info = await redis.info()
        
        return {
            "total_cached_items": total_keys,
            "redis_memory_used": info.get("used_memory_human", "unknown"),
            "redis_connected_clients": info.get("connected_clients", 0),
            "cache_hit_rate": "N/A"  # Would need to track hits/misses
        }
