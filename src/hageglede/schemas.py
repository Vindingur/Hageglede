from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# Base schemas with common fields
class PlantBase(BaseModel):
    name: str
    scientific_name: Optional[str] = None
    description: Optional[str] = None
    family: Optional[str] = None
    days_to_harvest: Optional[int] = None
    sunlight_needs: Optional[str] = None
    water_needs: Optional[str] = None


class ZoneBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    size_sq_m: Optional[float] = None
    soil_type: Optional[str] = None


class PlantingScheduleBase(BaseModel):
    plant_id: int
    zone_id: int
    scheduled_date: date
    quantity: Optional[int] = 1
    notes: Optional[str] = None


class PestBase(BaseModel):
    name: str
    description: Optional[str] = None
    treatment: Optional[str] = None


# Create schemas (for POST requests)
class PlantCreate(PlantBase):
    pass


class ZoneCreate(ZoneBase):
    pass


class PlantingScheduleCreate(PlantingScheduleBase):
    pass


class PestCreate(PestBase):
    pass


# Update schemas (for PATCH requests)
class PlantUpdate(BaseModel):
    name: Optional[str] = None
    scientific_name: Optional[str] = None
    description: Optional[str] = None
    family: Optional[str] = None
    days_to_harvest: Optional[int] = None
    sunlight_needs: Optional[str] = None
    water_needs: Optional[str] = None


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    size_sq_m: Optional[float] = None
    soil_type: Optional[str] = None


class PlantingScheduleUpdate(BaseModel):
    scheduled_date: Optional[date] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None


class PestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    treatment: Optional[str] = None


# Response schemas (for GET requests)
class PlantResponse(PlantBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    pests: List["PestResponse"] = []


class ZoneResponse(ZoneBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    planting_schedules: List["PlantingScheduleResponse"] = []


class PlantingScheduleResponse(PlantingScheduleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    plant: Optional[PlantResponse] = None
    zone: Optional[ZoneResponse] = None


class PestResponse(PestBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    affected_plants: List[PlantResponse] = []


# Forward references for circular dependencies
PlantResponse.model_rebuild()
ZoneResponse.model_rebuild()
PlantingScheduleResponse.model_rebuild()
PestResponse.model_rebuild()