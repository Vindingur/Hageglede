# PURPOSE: Define database schema with SQLAlchemy models for weather, plant, and garden data
# CONSUMED BY: scripts/loaders/weather_loader.py, scripts/loaders/plant_loader.py, scripts/loaders/garden_loader.py
# DEPENDS ON: sqlalchemy
# TEST: tests/test_schema.py

from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class WeatherStation(Base):
    """Weather station metadata."""
    __tablename__ = 'weather_stations'
    
    id = Column(Integer, primary_key=True)
    station_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(200))
    latitude = Column(Float)
    longitude = Column(Float)
    elevation = Column(Float)
    source = Column(String(100))
    country = Column(String(100))
    
    # Relationships
    observations = relationship('WeatherObservation', back_populates='station', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<WeatherStation(id={self.id}, station_id='{self.station_id}', name='{self.name}')>"


class WeatherObservation(Base):
    """Weather observations from weather stations."""
    __tablename__ = 'weather_observations'
    __table_args__ = (
        UniqueConstraint('station_id', 'date', name='_station_date_uc'),
    )
    
    id = Column(Integer, primary_key=True)
    station_id = Column(String(50), ForeignKey('weather_stations.station_id'), nullable=False)
    date = Column(Date, nullable=False)
    temp_mean = Column(Float)
    temp_min = Column(Float)
    temp_max = Column(Float)
    precipitation = Column(Float)
    snow_depth = Column(Float)
    wind_speed = Column(Float)
    sunshine = Column(Float)
    created_at = Column(DateTime)
    
    # Relationships
    station = relationship('WeatherStation', back_populates='observations')
    
    def __repr__(self):
        return f"<WeatherObservation(id={self.id}, station_id='{self.station_id}', date={self.date})>"


class Plant(Base):
    """Plant species and metadata."""
    __tablename__ = 'plants'
    
    id = Column(Integer, primary_key=True)
    species = Column(String(200), nullable=False)
    variety = Column(String(200))
    family = Column(String(100))
    optimal_temp_min = Column(Float)
    optimal_temp_max = Column(Float)
    frost_tolerance = Column(String(50))
    water_needs = Column(String(50))
    sun_needs = Column(String(50))
    soil_preference = Column(String(100))
    days_to_maturity = Column(Integer)
    planting_depth_cm = Column(Float)
    spacing_cm = Column(Float)
    
    # Relationships
    garden_plants = relationship('GardenPlant', back_populates='plant', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Plant(id={self.id}, species='{self.species}', variety='{self.variety}')>"


class Garden(Base):
    """Garden location and metadata."""
    __tablename__ = 'gardens'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    elevation = Column(Float)
    soil_type = Column(String(100))
    size_sqm = Column(Float)
    notes = Column(String(500))
    created_at = Column(DateTime)
    
    # Relationships
    plants = relationship('GardenPlant', back_populates='garden', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Garden(id={self.id}, name='{self.name}')>"


class GardenPlant(Base):
    """Plants in gardens."""
    __tablename__ = 'garden_plants'
    
    id = Column(Integer, primary_key=True)
    garden_id = Column(Integer, ForeignKey('gardens.id'), nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id'), nullable=False)
    planting_date = Column(Date)
    harvest_date = Column(Date)
    yield_amount = Column(Float)
    yield_unit = Column(String(50))
    notes = Column(String(500))
    created_at = Column(DateTime)
    
    # Relationships
    garden = relationship('Garden', back_populates='plants')
    plant = relationship('Plant', back_populates='garden_plants')
    
    def __repr__(self):
        return f"<GardenPlant(id={self.id}, garden_id={self.garden_id}, plant_id={self.plant_id})>"