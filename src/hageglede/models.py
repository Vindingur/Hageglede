"""
SQLAlchemy async-compatible models for the Hageglede gardening application.
All models inherit from declarative_base() and are designed for async SQLAlchemy usage.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, Table, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for many-to-many relationship between plants and zones
plant_zone_association = Table(
    'plant_zone_association',
    Base.metadata,
    Column('plant_id', Integer, ForeignKey('plants.id', ondelete='CASCADE'), primary_key=True),
    Column('zone_id', Integer, ForeignKey('zones.id', ondelete='CASCADE'), primary_key=True)
)


class Plant(Base):
    """Model representing a plant in the system."""
    __tablename__ = 'plants'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    scientific_name = Column(String(200))
    description = Column(Text)
    water_needs = Column(String(50))  # e.g., 'low', 'medium', 'high'
    sun_needs = Column(String(50))    # e.g., 'full_sun', 'partial_shade', 'shade'
    growth_habit = Column(String(50))  # e.g., 'annual', 'perennial', 'biennial'
    mature_height_cm = Column(Float)
    mature_width_cm = Column(Float)
    sowing_time = Column(String(100))  # e.g., 'spring', 'autumn'
    harvest_time = Column(String(100)) # e.g., 'summer', 'autumn'
    difficulty = Column(String(50))    # e.g., 'easy', 'medium', 'hard'
    image_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    zones = relationship(
        'Zone', 
        secondary=plant_zone_association,
        back_populates='plants'
    )
    user_plants = relationship('UserPlant', back_populates='plant', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Plant(name='{self.name}', id={self.id})>"


class Zone(Base):
    """Model representing a hardiness zone (based on postcode)."""
    __tablename__ = 'zones'

    id = Column(Integer, primary_key=True)
    zone_number = Column(String(10), nullable=False, unique=True, index=True)  # e.g., '7a', '8b'
    description = Column(Text)
    min_temperature_c = Column(Float)
    max_temperature_c = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    plants = relationship(
        'Plant', 
        secondary=plant_zone_association,
        back_populates='zones'
    )
    user_plants = relationship('UserPlant', back_populates='zone', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Zone(zone_number='{self.zone_number}', id={self.id})>"


class UserPlant(Base):
    """Model representing a user's specific plant instance in their garden."""
    __tablename__ = 'user_plants'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)  # User identifier from auth system
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
    zone_id = Column(Integer, ForeignKey('zones.id', ondelete='CASCADE'), nullable=False)
    nickname = Column(String(100))  # Optional user-given name for the plant
    planting_date = Column(DateTime(timezone=True))
    location = Column(String(200))  # e.g., 'backyard', 'balcony', 'kitchen window'
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plant = relationship('Plant', back_populates='user_plants')
    zone = relationship('Zone', back_populates='user_plants')
    care_logs = relationship('CareLog', back_populates='user_plant', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('user_id', 'plant_id', 'nickname', name='uix_user_plant_nickname'),
    )

    def __repr__(self):
        return f"<UserPlant(user_id='{self.user_id}', plant_id={self.plant_id}, id={self.id})>"


class CareLog(Base):
    """Model for logging care activities for user plants."""
    __tablename__ = 'care_logs'

    id = Column(Integer, primary_key=True)
    user_plant_id = Column(Integer, ForeignKey('user_plants.id', ondelete='CASCADE'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # e.g., 'watering', 'fertilizing', 'pruning'
    notes = Column(Text)
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_plant = relationship('UserPlant', back_populates='care_logs')

    def __repr__(self):
        return f"<CareLog(user_plant_id={self.user_plant_id}, activity_type='{self.activity_type}')>"


# Optional: Additional tables that might be useful for future features

class PostcodeZoneMapping(Base):
    """Mapping table for postcodes to hardiness zones."""
    __tablename__ = 'postcode_zone_mappings'

    id = Column(Integer, primary_key=True)
    postcode = Column(String(10), nullable=False, index=True)  # e.g., '02110'
    zone_id = Column(Integer, ForeignKey('zones.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    zone = relationship('Zone')

    __table_args__ = (
        UniqueConstraint('postcode', 'zone_id', name='uix_postcode_zone'),
    )

    def __repr__(self):
        return f"<PostcodeZoneMapping(postcode='{self.postcode}', zone_id={self.zone_id})>"


class PlantCategory(Base):
    """Model for categorizing plants (e.g., vegetables, herbs, flowers)."""
    __tablename__ = 'plant_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Many-to-many relationship with plants through association table
    plants = relationship(
        'Plant', 
        secondary='plant_category_association',
        back_populates='categories'
    )

    def __repr__(self):
        return f"<PlantCategory(name='{self.name}', id={self.id})>"


# Association table for plant categories
plant_category_association = Table(
    'plant_category_association',
    Base.metadata,
    Column('plant_id', Integer, ForeignKey('plants.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('plant_categories.id', ondelete='CASCADE'), primary_key=True)
)

# Add categories relationship to Plant model
Plant.categories = relationship(
    'PlantCategory',
    secondary=plant_category_association,
    back_populates='plants'
)