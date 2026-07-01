"""Rate Limiter Service - Per-API rate limiting using Redis"""
from typing import Optional
from datetime import datetime, timedelta

from app.core.redis import get_redis


class RateLimiter:
    """
    Token bucket rate limiter using Redis
    
    Limits requests per API key/module to prevent hitting external API limits
    """
    
    def __init__(self):
        self.prefix = "osif:ratelimit:"
    
    async def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit
        
        Args:
            key: Unique identifier (e.g., "shodan:api", "virustotal:api")
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            (allowed, info) where info contains current count and reset time
        """
        
        redis = await get_redis()
        redis_key = f"{self.prefix}{key}"
        
        # Get current count
        current = await redis.get(redis_key)
        
        if current is None:
            # First request in window
            await redis.setex(redis_key, window_seconds, 1)
            return True, {
                "allowed": True,
                "current": 1,
                "limit": max_requests,
                "remaining": max_requests - 1,
                "reset_at": datetime.utcnow() + timedelta(seconds=window_seconds)
            }
        
        current_count = int(current)
        
        if current_count >= max_requests:
            # Rate limit exceeded
            ttl = await redis.ttl(redis_key)
            return False, {
                "allowed": False,
                "current": current_count,
                "limit": max_requests,
                "remaining": 0,
                "reset_at": datetime.utcnow() + timedelta(seconds=ttl),
                "retry_after": ttl
            }
        
        # Increment counter
        await redis.incr(redis_key)
        ttl = await redis.ttl(redis_key)
        
        return True, {
            "allowed": True,
            "current": current_count + 1,
            "limit": max_requests,
            "remaining": max_requests - current_count - 1,
            "reset_at": datetime.utcnow() + timedelta(seconds=ttl)
        }
    
    async def reset_limit(self, key: str) -> bool:
        """Reset rate limit for a key"""
        
        redis = await get_redis()
        redis_key = f"{self.prefix}{key}"
        
        deleted = await redis.delete(redis_key)
        return deleted > 0
    
    async def get_limit_info(self, key: str) -> Optional[dict]:
        """Get current rate limit info without incrementing"""
        
        redis = await get_redis()
        redis_key = f"{self.prefix}{key}"
        
        current = await redis.get(redis_key)
        if current is None:
            return None
        
        ttl = await redis.ttl(redis_key)
        
        return {
            "current": int(current),
            "reset_at": datetime.utcnow() + timedelta(seconds=ttl),
            "reset_in_seconds": ttl
        }


# Predefined rate limits for common APIs
API_RATE_LIMITS = {
    "shodan": {"max_requests": 1, "window_seconds": 1},  # 1 req/sec
    "virustotal": {"max_requests": 4, "window_seconds": 60},  # 4 req/min (free tier)
    "abuseipdb": {"max_requests": 1000, "window_seconds": 86400},  # 1000 req/day
    "tomba": {"max_requests": 50, "window_seconds": 3600},  # 50 req/hour
    "urlscan": {"max_requests": 1, "window_seconds": 2},  # 1 req/2sec
    "securitytrails": {"max_requests": 50, "window_seconds": 3600},  # 50 req/hour
}


async def check_api_rate_limit(api_name: str) -> tuple[bool, dict]:
    """
    Convenience function to check rate limit for a known API
    
    Args:
        api_name: Name of the API (e.g., "shodan", "virustotal")
    
    Returns:
        (allowed, info) tuple
    """
    
    if api_name not in API_RATE_LIMITS:
        # Unknown API, allow by default
        return True, {"allowed": True, "message": "No rate limit configured"}
    
    limits = API_RATE_LIMITS[api_name]
    limiter = RateLimiter()
    
    return await limiter.check_limit(
        key=f"{api_name}:api",
        max_requests=limits["max_requests"],
        window_seconds=limits["window_seconds"]
    )
