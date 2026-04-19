"""
FastAPI application factory for Hageglede gardening management system.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .database import engine
from .routers import plants, zones, schedules


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database connection management."""
    # Startup: Create database tables (in production, use migrations)
    async with engine.begin() as conn:
        # Import here to avoid circular imports
        from . import models
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    # Shutdown: Dispose of database engine
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = config.get_settings()
    
    app = FastAPI(
        title="Hageglede API",
        description="Gardening management system API",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(plants.router, prefix="/api/v1/plants", tags=["plants"])
    app.include_router(zones.router, prefix="/api/v1/zones", tags=["zones"])
    app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "hageglede"}
    
    return app


# Create the app instance
app = create_app()