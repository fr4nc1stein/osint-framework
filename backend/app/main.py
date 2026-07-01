"""FastAPI Application Factory"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.queue import close_queue
from app.core.redis import close_redis
from app.api.v1 import cases, scans, modules, graph, investigations, websocket, scan_graph, scan_templates, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting OSIF v2.0 Backend...")
    print(f"📊 Database: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"🔴 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    # Create tables (in production, use Alembic migrations)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down OSIF v2.0 Backend...")
    await close_queue()
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="OSIF API",
        description="Open Source Intelligence Framework v2.0",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(cases.router, prefix="/api/v1/cases", tags=["Cases"])
    app.include_router(scans.router, prefix="/api/v1/scans", tags=["Scans"])
    app.include_router(scan_graph.router, prefix="/api/v1/scans", tags=["Scans"])
    app.include_router(scan_templates.router, prefix="/api/v1/templates", tags=["Templates"])
    app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
    app.include_router(modules.router, prefix="/api/v1/modules", tags=["Modules"])
    app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])
    app.include_router(investigations.router, prefix="/api/v1/investigations", tags=["Investigations"])
    app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
    
    # Health endpoints
    @app.get("/health")
    async def health():
        """Liveness probe"""
        return {"status": "ok"}
    
    @app.get("/ready")
    async def ready():
        """Readiness probe - checks DB and Redis"""
        from app.core.database import get_db
        from app.core.redis import get_redis
        
        try:
            # Check database
            async for db in get_db():
                await db.execute("SELECT 1")
            
            # Check Redis
            redis = await get_redis()
            await redis.ping()
            
            return {"status": "ready", "database": "ok", "redis": "ok"}
        except Exception as e:
            return {"status": "not_ready", "error": str(e)}, 503
    
    return app


app = create_app()
