"""Scan execution tasks for arq worker"""
import json
from datetime import datetime
from typing import Optional
from arq import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, update

from app.core.config import settings
from app.modules.registry import get_module_class
from app.services.graph_service import GraphService
from app.services.cache_service import CacheService
from app.services.rate_limiter import check_api_rate_limit
from app.services.auto_linker import AutoLinkerService
from app.services.credentials import get_api_key


async def get_db_session() -> AsyncSession:
    """Create database session for ad hoc task execution outside arq worker."""
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


def _module_error_status(error: Exception) -> str:
    """Classify module failures without expanding the public event contract."""
    if "rate limit" in str(error).lower():
        return "rate_limited"
    return "failed"


async def update_module_status(
    db: AsyncSession,
    scan_id: str,
    module_id: str,
    status: str,
    **extra
):
    """Update one module entry under a row lock to avoid progress races."""
    from app.models.scan import Scan

    result = await db.execute(
        select(Scan).where(Scan.id == scan_id).with_for_update()
    )
    scan = result.scalar_one_or_none()
    if not scan:
        return None

    module_statuses = dict(scan.module_statuses or {})
    module_state = dict(module_statuses.get(module_id, {}))
    module_state.update({
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        **extra
    })
    module_statuses[module_id] = module_state

    terminal_statuses = {"completed", "failed", "skipped", "rate_limited"}
    terminal_modules = [
        state for state in module_statuses.values()
        if state.get("status") in terminal_statuses
    ]
    failed_modules = [
        state for state in module_statuses.values()
        if state.get("status") in {"failed", "rate_limited"}
    ]
    completed_modules = [
        state for state in module_statuses.values()
        if state.get("status") == "completed"
    ]

    values = {
        "module_statuses": module_statuses,
        "progress": min(len(terminal_modules), scan.total_modules),
    }

    finalized = False
    if scan.total_modules and len(terminal_modules) >= scan.total_modules:
        finalized = True
        values["finished_at"] = datetime.utcnow()
        if completed_modules and failed_modules:
            values["status"] = "partial"
            values["error_message"] = f"{len(failed_modules)} module(s) failed"
        elif completed_modules:
            values["status"] = "completed"
            values["error_message"] = None
        else:
            values["status"] = "failed"
            values["error_message"] = "All modules failed"

    await db.execute(
        update(Scan)
        .where(Scan.id == scan_id)
        .values(**values)
    )
    await db.commit()

    total_edges_created = sum(
        int(state.get("edges_created") or 0)
        for state in module_statuses.values()
    )

    return {
        "finalized": finalized,
        "scan_status": values.get("status", scan.status),
        "module_statuses": module_statuses,
        "completed_modules": len(completed_modules),
        "failed_modules": len(failed_modules),
        "total_edges_created": total_edges_created,
    }


async def finalize_scan_side_effects(
    db: AsyncSession,
    redis: ArqRedis,
    scan_id: str,
    final_state: dict,
):
    """Run scan-level completion work after the last module attempt finishes."""
    if final_state["completed_modules"] > 0:
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

    # Publish completion event
    await publish_event(redis, scan_id, {
        "type": "scan_complete",
        "status": final_state["scan_status"],
        "total_discoveries": final_state["total_edges_created"],
        "timestamp": datetime.utcnow().isoformat()
    })


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
        if 'db_sessionmaker' in ctx:
            db = ctx['db_sessionmaker']()
        else:
            db = await get_db_session()

        await update_module_status(
            db,
            scan_id,
            module_id,
            "running",
            started_at=datetime.utcnow().isoformat()
        )
        
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
        
        # Build credential config — DB first, env fallback handled inside get_api_key
        cred_config = {}
        provider_id = getattr(module, 'PROVIDER_ID', None)
        if provider_id:
            api_key = await get_api_key(provider_id, db)
            if api_key:
                cred_config['api_key'] = api_key
            # Tomba also needs a secret key
            if provider_id == 'tomba':
                import os
                secret = os.getenv('TOMBA_SECRET_KEY')
                if secret:
                    cred_config['secret_key'] = secret

        # Initialize cache service
        cache_service = CacheService()

        # Execute module with caching
        if hasattr(module, 'execute_with_cache'):
            discoveries = await module.execute_with_cache(
                target=target,
                kind=kind,
                http_client=ctx['http_client'],
                config=cred_config,
                cache_service=cache_service,
                use_cache=True
            )
        else:
            discoveries = await module.execute(
                target=target,
                kind=kind,
                http_client=ctx['http_client'],
                config=cred_config
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
        
        final_state = await update_module_status(
            db,
            scan_id,
            module_id,
            "completed",
            discoveries_count=len(discoveries),
            edges_created=len(edges_created),
            finished_at=datetime.utcnow().isoformat()
        )

        if final_state and final_state["finalized"]:
            await finalize_scan_side_effects(
                db,
                redis,
                scan_id,
                final_state
            )
        
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
        
        # Record the module failure, but leave the scan running while other
        # module jobs can still complete successfully.
        final_state = None
        if db:
            await db.rollback()
            final_state = await update_module_status(
                db,
                scan_id,
                module_id,
                _module_error_status(e),
                error=str(e),
                finished_at=datetime.utcnow().isoformat()
            )

        if final_state and final_state["finalized"]:
            await finalize_scan_side_effects(
                db,
                redis,
                scan_id,
                final_state
            )

        return {
            "status": "failed",
            "module_id": module_id,
            "error": str(e)
        }
        
    finally:
        if db:
            await db.close()
