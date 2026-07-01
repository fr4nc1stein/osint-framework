"""Redis connection management"""
import redis.asyncio as redis
from app.core.config import settings

_redis_pool = None


async def get_redis() -> redis.Redis:
    """Get Redis connection from pool"""
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=True
        )
    
    return redis.Redis(connection_pool=_redis_pool)


async def close_redis():
    """Close Redis connection pool"""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
