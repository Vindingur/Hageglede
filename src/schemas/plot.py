from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class SoilType(str, Enum):
    SANDY = "sandy"
    CLAY = "clay"
    LOAM = "loam"
    SILT = "silt"
    PEAT = "peat"
    CHALK = "chalk"


class PlotCreate(BaseModel):
    """Schema for creating a new plot"""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the plot")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    width_meters: float = Field(..., gt=0, le=100, description="Width in meters")
    height_meters: float = Field(..., gt=0, le=100, description="Height in meters")
    soil_type: SoilType = Field(..., description="Type of soil in the plot")
    sunlight_hours: float = Field(..., ge=0, le=24, description="Average daily sunlight hours")
    is_indoor: bool = Field(False, description="Whether the plot is indoors/controlled environment")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class PlotUpdate(BaseModel):
    """Schema for updating an existing plot"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the plot")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")
    width_meters: Optional[float] = Field(None, gt=0, le=100, description="Width in meters")
    height_meters: Optional[float] = Field(None, gt=0, le=100, description="Height in meters")
    soil_type: Optional[SoilType] = Field(None, description="Type of soil in the plot")
    sunlight_hours: Optional[float] = Field(None, ge=0, le=24, description="Average daily sunlight hours")
    is_indoor: Optional[bool] = Field(None, description="Whether the plot is indoors/controlled environment")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class PlotBase(BaseModel):
    """Base plot schema with common fields"""
    id: int
    name: str
    description: Optional[str]
    width_meters: float
    height_meters: float
    soil_type: SoilType
    sunlight_hours: float
    is_indoor: bool
    notes: Optional[str]
    user_id: str


class PlotResponse(PlotBase):
    """Full plot response schema"""
    area_sqm: float = Field(..., description="Calculated area in square meters")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PlotListResponse(BaseModel):
    """Schema for listing plots"""
    plots: List[PlotResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PlotGeometry(BaseModel):
    """Schema for plot geometry (simplified for MVP)"""
    x: float = Field(..., description="X coordinate (longitude or relative position)")
    y: float = Field(..., description="Y coordinate (latitude or relative position)")
    rotation: Optional[float] = Field(0, ge=0, lt=360, description="Rotation in degrees")


class PlotWithGeometry(PlotResponse):
    """Plot response including geometry information"""
    geometry: Optional[PlotGeometry] = None