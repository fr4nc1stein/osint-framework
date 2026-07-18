"""Task queue management"""
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from app.core.config import settings

_redis_pool: ArqRedis = None


async def get_queue() -> ArqRedis:
    """Get arq Redis connection pool"""
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = await create_pool(
            RedisSettings(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                database=settings.REDIS_DB
            )
        )
    
    return _redis_pool


async def close_queue():
    """Close arq connection pool"""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
