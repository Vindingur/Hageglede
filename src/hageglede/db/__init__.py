"""Database package for unified gardening.db."""

from .schema import Base, Plant, ClimateZone, WeatherStation, WeatherObservation, CalendarEntry, Plot, Planting, Recommendation, GardenNote, create_all_tables
from .session import engine, SessionLocal, get_db

__all__ = [
    "Base",
    "Plant",
    "ClimateZone",
    "WeatherStation", 
    "WeatherObservation",
    "CalendarEntry",
    "Plot",
    "Planting",
    "Recommendation",
    "GardenNote",
    "create_all_tables",
    "engine",
    "SessionLocal",
    "get_db",
]