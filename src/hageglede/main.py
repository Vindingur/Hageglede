"""
FastAPI application factory for Hageglede gardening management system.
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
        root_path="/projects/hageplan",  # Add root path for Traefik routing
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers with API prefix
    app.include_router(plants.router, prefix="/api/v1/plants", tags=["plants"])
    app.include_router(zones.router, prefix="/api/v1/zones", tags=["zones"])
    app.include_router(schedules.router, prefix="/api/v1/schedules", tags=["schedules"])
    
    # Mount frontend static files
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    if frontend_path.exists():
        app.mount(
            "/", 
            StaticFiles(directory=str(frontend_path), html=True), 
            name="frontend"
        )
        print(f"Mounted frontend from {frontend_path}")
    else:
        print(f"Warning: Frontend directory not found at {frontend_path}")
        # Create a simple info endpoint
        @app.get("/")
        async def root():
            return {
                "message": "Hageglede API",
                "status": "running",
                "api_docs": "/projects/hageplan/docs",
                "openapi": "/projects/hageplan/openapi.json"
            }
    
    # Health check endpoint (without path prefix since it's at root of app)
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "hageglede"}
    
    # API info endpoint
    @app.get("/api/info", tags=["info"])
    async def api_info():
        return {
            "name": "Hageglede",
            "version": "0.1.0",
            "description": "Gardening management system",
            "api_prefix": "/api/v1",
            "frontend_available": frontend_path.exists()
        }
    
    return app


# Create the app instance
app = create_app()