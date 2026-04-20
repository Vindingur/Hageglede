from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class SoilType(str, enum.Enum):
    CLAY = "clay"
    SAND = "sand"
    LOAM = "loam"
    SILT = "silt"
    PEAT = "peat"
    CHALKY = "chalky"

class Plot(Base):
    """Plot model representing a gardening plot belonging to a user."""
    
    __tablename__ = "plots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Geometry and location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_sqm = Column(Float, nullable=False)  # Area in square meters
    geometry_wkt = Column(Text, nullable=True)  # Well-Known Text representation
    
    # Soil and environmental properties
    soil_type = Column(Enum(SoilType), nullable=True)
    soil_ph = Column(Float, nullable=True)  # pH value
    sunlight_hours = Column(Float, nullable=True)  # Average daily sunlight hours
    drainage_type = Column(String(50), nullable=True)  # poor, moderate, good
    
    # Hardiness zone (could be auto-detected from location)
    hardiness_zone = Column(String(10), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<Plot(id={self.id}, name='{self.name}', user_id='{self.user_id}')>"
    
    def to_dict(self) -> dict:
        """Convert plot to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "area_sqm": self.area_sqm,
            "geometry_wkt": self.geometry_wkt,
            "soil_type": self.soil_type.value if self.soil_type else None,
            "soil_ph": self.soil_ph,
            "sunlight_hours": self.sunlight_hours,
            "drainage_type": self.drainage_type,
            "hardiness_zone": self.hardiness_zone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }