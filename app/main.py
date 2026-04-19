"""
Hageglede Main Application
FastAPI entry point for the gardening web application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import plants, zones, users, system
from app.database.database import engine, Base
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Hageglede API",
    description="Gardening web application API for plant recommendations based on climate zones",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(zones.router, prefix="/api", tags=["climate-zones"])
app.include_router(plants.router, prefix="/api", tags=["plants"])
app.include_router(users.router, prefix="/api", tags=["users"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Hageglede API")
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Hageglede API")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Hageglede API",
        "version": "1.0.0",
        "description": "Gardening web application for plant recommendations based on climate zones",
        "documentation": "/api/docs",
        "health_check": "/api/health"
    }