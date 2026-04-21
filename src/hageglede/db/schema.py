"""
Unified SQLAlchemy models for gardening.db
Merges tables from hageplan.db, hageglede.db, and other gardening databases
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# Plant data models (from hageplan.db / plants.db)
class Plant(Base):
    """Plant species and metadata"""
    __tablename__ = "plants"
    
    id = Column(Integer, primary_key=True)
    scientific_name = Column(String, nullable=False, index=True)
    norwegian_name = Column(String)
    family = Column(String)
    genus = Column(String)
    species = Column(String)
    subspecies = Column(String)
    variety = Column(String)
    common_name = Column(String)
    growth_form = Column(String)
    is_pollinator_friendly = Column(Boolean, default=False)
    is_deer_resistant = Column(Boolean, default=False)
    is_drought_tolerant = Column(Boolean, default=False)
    min_hardiness_zone = Column(Integer)
    max_hardiness_zone = Column(Integer)
    planting_depth_cm = Column(Float)
    spacing_cm = Column(Float)
    mature_height_cm = Column(Float)
    mature_width_cm = Column(Float)
    sun_requirements = Column(String)  # full_sun, partial_shade, shade
    soil_type = Column(String)  # sandy, clay, loam
    soil_ph_min = Column(Float)
    soil_ph_max = Column(Float)
    water_needs = Column(String)  # low, medium, high
    fertilizer_needs = Column(String)  # low, medium, high
    germination_days = Column(Integer)
    time_to_maturity_days = Column(Integer)
    is_perennial = Column(Boolean, default=False)
    is_annual = Column(Boolean, default=False)
    is_biennial = Column(Boolean, default=False)
    is_vegetable = Column(Boolean, default=False)
    is_fruit = Column(Boolean, default=False)
    is_herb = Column(Boolean, default=False)
    is_flower = Column(Boolean, default=False)
    edible_parts = Column(String)
    harvest_season = Column(String)
    companion_plants = Column(Text)  # JSON list of plant IDs
    antagonistic_plants = Column(Text)  # JSON list of plant IDs
    diseases = Column(Text)
    pests = Column(Text)
    propagation_methods = Column(String)
    pruning_requirements = Column(String)
    notes = Column(Text)
    source = Column(String)  # artsdatabanken, gbif, etc.
    source_id = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    occurrences = relationship("Occurrence", back_populates="plant")
    calendar_entries = relationship("CalendarEntry", back_populates="plant")


class Occurrence(Base):
    """Species occurrence records from GBIF"""
    __tablename__ = "occurrences"
    
    id = Column(Integer, primary_key=True)
    gbif_id = Column(Integer, unique=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String)
    county = Column(String)
    municipality = Column(String)
    locality = Column(String)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    coordinate_uncertainty_m = Column(Float)
    basis_of_record = Column(String)  # HUMAN_OBSERVATION, PRESERVED_SPECIMEN, etc.
    recorded_by = Column(String)
    dataset_name = Column(String)
    institution_code = Column(String)
    collection_code = Column(String)
    catalog_number = Column(String)
    individual_count = Column(Integer)
    occurrence_status = Column(String)  # present, absent
    establishment_means = Column(String)  # native, introduced, cultivated
    georeference_verification_status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    plant = relationship("Plant", back_populates="occurrences")


# Climate data models (from climate.db)
class ClimateZone(Base):
    """Climate and hardiness zone data"""
    __tablename__ = "climate_zones"
    
    id = Column(Integer, primary_key=True)
    zone_code = Column(String, nullable=False, index=True)  # e.g., "5a", "7b"
    zone_number = Column(Integer)
    zone_subtype = Column(String)  # a, b
    min_temperature_c = Column(Float)
    max_temperature_c = Column(Float)
    description = Column(Text)
    region = Column(String)
    country = Column(String)
    source = Column(String)  # met, usda, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WeatherStation(Base):
    """Weather station metadata"""
    __tablename__ = "weather_stations"
    
    id = Column(Integer, primary_key=True)
    station_id = Column(String, unique=True, index=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    elevation_m = Column(Float)
    municipality = Column(String)
    county = Column(String)
    country = Column(String)
    active_from = Column(Date)
    active_to = Column(Date)
    source = Column(String)  # met, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WeatherObservation(Base):
    """Weather observation data"""
    __tablename__ = "weather_observations"
    
    id = Column(Integer, primary_key=True)
    station_id = Column(String, ForeignKey("weather_stations.station_id"))
    observed_at = Column(DateTime, nullable=False, index=True)
    temperature_c = Column(Float)
    precipitation_mm = Column(Float)
    humidity_percent = Column(Float)
    wind_speed_mps = Column(Float)
    wind_direction_deg = Column(Float)
    pressure_hpa = Column(Float)
    cloud_cover_percent = Column(Float)
    sunshine_minutes = Column(Integer)
    snow_depth_cm = Column(Float)
    observation_type = Column(String)  # forecast, historical, etc.
    quality_flag = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    station = relationship("WeatherStation")


# Garden planning models (from hageglede.db)
class CalendarEntry(Base):
    """Gardening calendar entries"""
    __tablename__ = "calendar_entries"
    
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    entry_type = Column(String, nullable=False)  # sowing, planting, harvesting, pruning, fertilizing
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    location = Column(String)  # indoor, outdoor, greenhouse
    notes = Column(Text)
    completed = Column(Boolean, default=False)
    completed_date = Column(Date)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    plant = relationship("Plant", back_populates="calendar_entries")


class Plot(Base):
    """Garden plot/area definitions"""
    __tablename__ = "plots"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    width_m = Column(Float)
    height_m = Column(Float)
    area_m2 = Column(Float)
    soil_type = Column(String)
    sun_exposure = Column(String)  # full_sun, partial_shade, shade
    has_irrigation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Planting(Base):
    """Plantings in garden plots"""
    __tablename__ = "plantings"
    
    id = Column(Integer, primary_key=True)
    plot_id = Column(Integer, ForeignKey("plots.id"))
    plant_id = Column(Integer, ForeignKey("plants.id"))
    x_position_m = Column(Float)
    y_position_m = Column(Float)
    planted_date = Column(Date)
    quantity = Column(Integer, default=1)
    spacing_cm = Column(Float)
    notes = Column(Text)
    status = Column(String)  # planted, germinated, growing, harvested, failed
    harvested_date = Column(Date)
    yield_amount = Column(Float)
    yield_unit = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    plot = relationship("Plot")
    plant = relationship("Plant")


# Gardening recommendations and notes
class Recommendation(Base):
    """Plant recommendations based on conditions"""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    condition_type = Column(String)  # hardiness_zone, soil_type, sun_exposure, companion, etc.
    condition_value = Column(String)
    score = Column(Float)  # 0-1 recommendation score
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    plant = relationship("Plant")


class GardenNote(Base):
    """General garden notes and observations"""
    __tablename__ = "garden_notes"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    note_type = Column(String)  # observation, todo, idea, problem, solution
    priority = Column(String)  # low, medium, high
    related_plant_id = Column(Integer, ForeignKey("plants.id"))
    related_plot_id = Column(Integer, ForeignKey("plots.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    plant = relationship("Plant")
    plot = relationship("Plot")


# Create all tables function
def create_all_tables(engine):
    """Create all tables in the unified database"""
    Base.metadata.create_all(engine)


# Export all models
__all__ = [
    "Base",
    "Plant",
    "Occurrence",
    "ClimateZone",
    "WeatherStation",
    "WeatherObservation",
    "CalendarEntry",
    "Plot",
    "Planting",
    "Recommendation",
    "GardenNote",
    "create_all_tables"
]