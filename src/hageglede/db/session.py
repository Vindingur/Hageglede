"""
Database session management for unified gardening.db
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# Determine project root and database path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATABASE_DIR = PROJECT_ROOT / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATABASE_DIR / "gardening.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite with multiple threads
    echo=False,  # Set to True for SQL logging
    pool_pre_ping=True,  # Verify connections before using
    # SQLite-specific optimizations
    isolation_level="SERIALIZABLE"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
SessionScoped = scoped_session(SessionLocal)

# Base class for declarative models
Base = declarative_base()

def get_db():
    """
    Dependency function to get database session.
    Use in FastAPI dependencies or other contexts.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_scoped_db():
    """
    Get a scoped database session for thread-safe operations.
    Caller must call session.remove() when done in threaded contexts.
    """
    return SessionScoped()

def init_db():
    """
    Initialize database by creating all tables based on models.
    Should be called during application startup.
    """
    # Ensure database directory exists
    DATABASE_DIR.mkdir(exist_ok=True)
    
    # Import models to ensure they're registered with Base
    from .schema import (
        PlantSpecies, PlantFamily, PlantGenus,
        PlantOccurrence, PlantSynonyms,
        WeatherStation, WeatherObservation, WeatherZone,
        ClimatePrediction, PlantingCalendar,
        GardeningPlot, PlotPlant, PlotObservation,
        UserPreferences, DataSource, MigrationLog
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Log initialization
    print(f"Database initialized at: {DATABASE_URL}")
    print(f"Tables created: {list(Base.metadata.tables.keys())}")
    
    return engine

def drop_db():
    """
    Drop all tables (for testing/reset purposes).
    Use with caution!
    """
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped")

def get_database_stats():
    """
    Get basic database statistics.
    """
    import sqlite3
    
    if not DATABASE_PATH.exists():
        return {"status": "database_not_found", "path": str(DATABASE_PATH)}
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    stats = {
        "database_path": str(DATABASE_PATH),
        "database_size_mb": DATABASE_PATH.stat().st_size / (1024 * 1024),
        "tables": [],
        "row_counts": {}
    }
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    for (table_name,) in tables:
        stats["tables"].append(table_name)
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            stats["row_counts"][table_name] = count
        except:
            stats["row_counts"][table_name] = 0
    
    conn.close()
    return stats

# Context manager for database sessions
class DatabaseSession:
    """
    Context manager for database sessions.
    
    Example usage:
    ```python
    with DatabaseSession() as db:
        plants = db.query(PlantSpecies).all()
    ```
    """
    def __init__(self, scoped=False):
        self.scoped = scoped
        self.session = None
    
    def __enter__(self):
        if self.scoped:
            self.session = get_scoped_db()
        else:
            self.session = SessionLocal()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if self.scoped:
                self.session.remove()
            else:
                self.session.close()

# Create database directory on module import
DATABASE_DIR.mkdir(exist_ok=True)