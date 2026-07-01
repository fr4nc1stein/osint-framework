"""arq Worker Configuration"""
import os
from arq import create_pool
from arq.connections import RedisSettings
import httpx

from app.tasks.scan_tasks import run_scan_task


async def startup(ctx):
    """Worker startup - initialize shared resources"""
    print("🔧 Initializing worker resources...")
    ctx['http_client'] = httpx.AsyncClient(timeout=30.0)
    print("✅ Worker startup complete")


async def shutdown(ctx):
    """Worker shutdown - cleanup"""
    print("🛑 Shutting down worker...")
    await ctx['http_client'].aclose()
    print("✅ Worker shutdown complete")


class WorkerSettings:
    """arq worker settings"""
    
    redis_settings = RedisSettings(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        database=int(os.getenv('REDIS_DB', 0))
    )
    
    # Task functions
    functions = [run_scan_task]
    
    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown
    
    # Worker configuration
    max_jobs = int(os.getenv('WORKER_CONCURRENCY', 4))
    job_timeout = 300  # 5 minutes per module
    keep_result = 3600  # Keep results for 1 hour
    
    # Logging
    log_results = True
