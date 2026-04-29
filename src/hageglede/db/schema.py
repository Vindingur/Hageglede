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
    plantings = relationship('Planting', back_populates='plant', cascade='all, delete-orphan')
    recommendations = relationship('Recommendation', back_populates='plant', cascade='all, delete-orphan')
    
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
    plots = relationship('Plot', back_populates='garden', cascade='all, delete-orphan')
    notes_rel = relationship('GardenNote', back_populates='garden', cascade='all, delete-orphan')
    
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


class Zone(Base):
    """Hardiness zone or microclimate zone within a garden."""
    __tablename__ = 'zones'
    
    id = Column(Integer, primary_key=True)
    garden_id = Column(Integer, ForeignKey('gardens.id'), nullable=False)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50))  # 'hardiness', 'microclimate', 'sun_exposure'
    description = Column(String(500))
    hardiness_zone = Column(String(10))
    sun_exposure = Column(String(50))  # 'full_sun', 'partial_shade', 'full_shade'
    soil_type = Column(String(100))
    created_at = Column(DateTime)
    
    # Relationships
    garden = relationship('Garden', back_populates='plots')
    plots = relationship('Plot', back_populates='zone', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Zone(id={self.id}, garden_id={self.garden_id}, name='{self.name}')>"


class Plot(Base):
    """Individual planting plot/area within a garden zone."""
    __tablename__ = 'plots'
    
    id = Column(Integer, primary_key=True)
    garden_id = Column(Integer, ForeignKey('gardens.id'), nullable=False)
    zone_id = Column(Integer, ForeignKey('zones.id'))
    name = Column(String(100), nullable=False)
    size_sqm = Column(Float)
    plot_type = Column(String(50))  # 'raised_bed', 'ground', 'container', 'greenhouse'
    soil_ph = Column(Float)
    soil_moisture = Column(String(50))
    notes = Column(String(500))
    created_at = Column(DateTime)
    
    # Relationships
    garden = relationship('Garden', back_populates='plots')
    zone = relationship('Zone', back_populates='plots')
    plantings = relationship('Planting', back_populates='plot', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Plot(id={self.id}, garden_id={self.garden_id}, name='{self.name}')>"


class Planting(Base):
    """Specific planting instance of a plant in a plot."""
    __tablename__ = 'plantings'
    __table_args__ = (
        UniqueConstraint('plot_id', 'plant_id', 'planting_date', name='_plot_plant_date_uc'),
    )
    
    id = Column(Integer, primary_key=True)
    plot_id = Column(Integer, ForeignKey('plots.id'), nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id'), nullable=False)
    planting_date = Column(Date, nullable=False)
    quantity = Column(Integer, default=1)
    spacing_cm = Column(Float)
    depth_cm = Column(Float)
    status = Column(String(50), default='active')  # 'active', 'harvested', 'failed'
    harvest_date = Column(Date)
    yield_amount = Column(Float)
    yield_unit = Column(String(50))
    notes = Column(String(500))
    created_at = Column(DateTime)
    
    # Relationships
    plot = relationship('Plot', back_populates='plantings')
    plant = relationship('Plant', back_populates='plantings')
    
    def __repr__(self):
        return f"<Planting(id={self.id}, plot_id={self.plot_id}, plant_id={self.plant_id}, planting_date={self.planting_date})>"


class CalendarEntry(Base):
    """Calendar entries for garden tasks, events, and reminders."""
    __tablename__ = 'calendar_entries'
    
    id = Column(Integer, primary_key=True)
    garden_id = Column(Integer, ForeignKey('gardens.id'), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    entry_type = Column(String(50), nullable=False)  # 'task', 'event', 'reminder', 'observation'
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    completed = Column(Boolean, default=False)
    plant_id = Column(Integer, ForeignKey('plants.id'))
    plot_id = Column(Integer, ForeignKey('plots.id'))
    priority = Column(String(20))  # 'low', 'medium', 'high'
    recurrence_pattern = Column(String(100))
    created_at = Column(DateTime)
    
    # Relationships
    garden = relationship('Garden')
    plant = relationship('Plant')
    plot = relationship('Plot')
    
    def __repr__(self):
        return f"<CalendarEntry(id={self.id}, garden_id={self.garden_id}, title='{self.title}', entry_type='{self.entry_type}')>"


class Recommendation(Base):
    """Plant recommendations for gardens based on conditions."""
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True)
    garden_id = Column(Integer, ForeignKey('gardens.id'), nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id'), nullable=False)
    recommendation_type = Column(String(50), nullable=False)  # 'hardiness', 'season', 'companion', 'rotation'
    score = Column(Float)
    reason = Column(String(500))
    season = Column(String(50))
    created_at = Column(DateTime)
    
    # Relationships
    garden = relationship('Garden')
    plant = relationship('Plant', back_populates='recommendations')
    
    def __repr__(self):
        return f"<Recommendation(id={self.id}, garden_id={self.garden_id}, plant_id={self.plant_id}, type='{self.recommendation_type}')>"


class GardenNote(Base):
    """Notes and observations about a garden."""
    __tablename__ = 'garden_notes'
    
    id = Column(Integer, primary_key=True)
    garden_id = Column(Integer, ForeignKey('gardens.id'), nullable=False)
    title = Column(String(200))
    content = Column(String(2000), nullable=False)
    note_type = Column(String(50))  # 'observation', 'plan', 'problem', 'success'
    created_at = Column(DateTime)
    
    # Relationships
    garden = relationship('Garden', back_populates='notes_rel')
    
    def __repr__(self):
        return f"<GardenNote(id={self.id}, garden_id={self.garden_id}, title='{self.title}')>"