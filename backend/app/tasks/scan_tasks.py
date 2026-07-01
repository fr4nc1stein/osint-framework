"""Scan execution tasks for arq worker"""
import json
from datetime import datetime
from typing import Optional
from arq import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.modules.registry import get_module_class
from app.services.graph_service import GraphService
from app.services.cache_service import CacheService
from app.services.rate_limiter import check_api_rate_limit
from app.services.auto_linker import AutoLinkerService


async def get_db_session() -> AsyncSession:
    """Create database session for worker"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    return async_session()


async def publish_event(redis: ArqRedis, scan_id: str, event: dict):
    """Publish event to Redis Stream for WebSocket broadcast"""
    stream_key = f"scan:{scan_id}:events"
    event_data = json.dumps(event)
    
    # Add to Redis Stream
    await redis.xadd(
        stream_key,
        {"data": event_data},
        maxlen=1000  # Keep last 1000 events
    )


async def run_scan_task(
    ctx,
    scan_id: str,
    module_id: str,
    target: str,
    kind: str
) -> dict:
    """
    Execute a single OSINT module
    
    Args:
        ctx: arq context with shared resources
        scan_id: UUID of the scan
        module_id: ID of the module to run
        target: Target value to investigate
        kind: Indicator kind (domain, ip, email, etc.)
    
    Returns:
        dict with execution results
    """
    
    db: Optional[AsyncSession] = None
    redis: ArqRedis = await ctx['redis']
    
    try:
        # Get database session
        db = await get_db_session()
        
        # Publish start event
        await publish_event(redis, scan_id, {
            "type": "module_start",
            "module_id": module_id,
            "target": target,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Load module class
        module_class = get_module_class(module_id)
        if not module_class:
            raise ValueError(f"Module {module_id} not found")
        
        # Instantiate module
        module = module_class()
        
        # Check rate limit if module has API rate limiting
        if hasattr(module, 'RATE_LIMIT_API') and module.RATE_LIMIT_API:
            allowed, limit_info = await check_api_rate_limit(module.RATE_LIMIT_API)
            if not allowed:
                raise Exception(
                    f"Rate limit exceeded for {module.RATE_LIMIT_API}. "
                    f"Retry after {limit_info.get('retry_after', 'unknown')} seconds"
                )
        
        # Initialize cache service
        cache_service = CacheService()
        
        # Execute module with caching
        if hasattr(module, 'execute_with_cache'):
            discoveries = await module.execute_with_cache(
                target=target,
                kind=kind,
                http_client=ctx['http_client'],
                config={},
                cache_service=cache_service,
                use_cache=True
            )
        else:
            # Fallback to regular execute
            discoveries = await module.execute(
                target=target,
                kind=kind,
                http_client=ctx['http_client'],
                config={}
            )
        
        # Process discoveries and build graph
        graph_service = GraphService(db)
        edges_created = []
        
        for discovery in discoveries:
            try:
                edge = await graph_service.add_discovery(scan_id, discovery)
                edges_created.append(str(edge.id))
                
                # Publish discovery event
                await publish_event(redis, scan_id, {
                    "type": "discovery",
                    "module_id": module_id,
                    "discovery": {
                        "src_value": discovery.src_value,
                        "src_kind": discovery.src_kind,
                        "dst_value": discovery.dst_value,
                        "dst_kind": discovery.dst_kind,
                        "relationship": discovery.relationship,
                        "confidence": discovery.confidence
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"Error processing discovery: {e}")
                continue
        
        # Update scan progress
        from app.models.scan import Scan
        from sqlalchemy import select, update
        
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        
        if scan:
            # Increment progress
            new_progress = scan.progress + 1
            await db.execute(
                update(Scan)
                .where(Scan.id == scan_id)
                .values(progress=new_progress)
            )
            await db.commit()
            
            # Check if scan is complete
            if new_progress >= scan.total_modules:
                # Run auto-linker for cross-correlation
                try:
                    auto_linker = AutoLinkerService(db)
                    
                    # Find corroborations
                    corr_edges = await auto_linker.find_corroborations(scan_id)
                    
                    # Infer relationships
                    inferred_edges = await auto_linker.infer_relationships(scan_id)
                    
                    # Get stats
                    stats = await auto_linker.get_correlation_stats(scan_id)
                    
                    # Publish auto-linker event
                    await publish_event(redis, scan_id, {
                        "type": "auto_linker_complete",
                        "corroborations": len(corr_edges),
                        "inferred": len(inferred_edges),
                        "stats": stats,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    print(f"Auto-linker error: {e}")
                
                # Mark scan as completed
                await db.execute(
                    update(Scan)
                    .where(Scan.id == scan_id)
                    .values(
                        status="completed",
                        finished_at=datetime.utcnow()
                    )
                )
                await db.commit()
                
                # Publish completion event
                await publish_event(redis, scan_id, {
                    "type": "scan_complete",
                    "total_discoveries": len(edges_created),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Publish module completion
        await publish_event(redis, scan_id, {
            "type": "module_complete",
            "module_id": module_id,
            "discoveries_count": len(discoveries),
            "edges_created": len(edges_created),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "status": "success",
            "module_id": module_id,
            "discoveries": len(discoveries),
            "edges_created": len(edges_created)
        }
        
    except Exception as e:
        # Publish error event
        await publish_event(redis, scan_id, {
            "type": "module_error",
            "module_id": module_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update scan with error
        if db:
            from app.models.scan import Scan
            from sqlalchemy import update
            
            await db.execute(
                update(Scan)
                .where(Scan.id == scan_id)
                .values(
                    status="error",
                    error_message=str(e),
                    finished_at=datetime.utcnow()
                )
            )
            await db.commit()
        
        raise
        
    finally:
        if db:
            await db.close()
