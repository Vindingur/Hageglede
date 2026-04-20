"""Planting calendar endpoints."""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from src.database import get_db
from src.services.calendar import PlantingCalendarService, PlantingWindow, CropSchedule, get_calendar_service

router = APIRouter(prefix="/calendar", tags=["calendar"])


class PlantingWindowResponse(BaseModel):
    """Response model for a planting window."""
    crop_name: str
    variety: Optional[str] = None
    sowing_start: date
    sowing_end: date
    transplant_start: Optional[date] = None
    transplant_end: Optional[date] = None
    harvest_start: date
    harvest_end: date
    direct_sow: bool
    days_to_maturity: int
    notes: Optional[str] = None
    
    @classmethod
    def from_service(cls, window: PlantingWindow) -> "PlantingWindowResponse":
        """Convert service model to response."""
        return cls(
            crop_name=window.crop_name,
            variety=window.variety,
            sowing_start=window.sowing_start,
            sowing_end=window.sowing_end,
            transplant_start=window.transplant_start,
            transplant_end=window.transplant_end,
            harvest_start=window.harvest_start,
            harvest_end=window.harvest_end,
            direct_sow=window.direct_sow,
            days_to_maturity=window.days_to_maturity,
            notes=window.notes
        )


class CropScheduleResponse(BaseModel):
    """Response model for a crop schedule."""
    crop_name: str
    variety: Optional[str] = None
    hardiness_zones: List[str]
    planting_windows: List[PlantingWindowResponse]
    successions: List[date] = Field(default_factory=list)
    season_type: str  # "spring", "summer", "fall", "winter"
    
    @classmethod
    def from_service(cls, schedule: CropSchedule) -> "CropScheduleResponse":
        """Convert service model to response."""
        return cls(
            crop_name=schedule.crop_name,
            variety=schedule.variety,
            hardiness_zones=schedule.hardiness_zones,
            planting_windows=[
                PlantingWindowResponse.from_service(window) 
                for window in schedule.planting_windows
            ],
            successions=schedule.successions,
            season_type=schedule.season_type
        )


class CalendarYearRequest(BaseModel):
    """Request model for generating a calendar year."""
    hardiness_zone: str = Field(..., description="USDA hardiness zone, e.g., '7a'")
    year: int = Field(default_factory=lambda: date.today().year)
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Optional latitude for more precise calculations")
    elevation_m: Optional[float] = Field(None, ge=0, description="Optional elevation in meters")


@router.get("/windows/{crop_name}", response_model=List[PlantingWindowResponse])
async def get_planting_windows(
    crop_name: str,
    hardiness_zone: str = Query(..., description="USDA hardiness zone"),
    year: int = Query(None, description="Year (defaults to current year)"),
    variety: Optional[str] = Query(None, description="Specific crop variety"),
    service: PlantingCalendarService = Depends(get_calendar_service)
) -> List[PlantingWindowResponse]:
    """Get planting windows for a specific crop in a given zone."""
    if year is None:
        year = date.today().year
    
    try:
        windows = await service.get_crop_windows(
            crop_name=crop_name,
            hardiness_zone=hardiness_zone,
            year=year,
            variety=variety
        )
        return [PlantingWindowResponse.from_service(w) for w in windows]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating planting windows: {str(e)}")


@router.get("/schedule/{crop_name}", response_model=CropScheduleResponse)
async def get_crop_schedule(
    crop_name: str,
    hardiness_zone: str = Query(..., description="USDA hardiness zone"),
    year: int = Query(None, description="Year (defaults to current year)"),
    variety: Optional[str] = Query(None, description="Specific crop variety"),
    service: PlantingCalendarService = Depends(get_calendar_service)
) -> CropScheduleResponse:
    """Get complete crop schedule including all planting windows for a year."""
    if year is None:
        year = date.today().year
    
    try:
        schedule = await service.get_crop_schedule(
            crop_name=crop_name,
            hardiness_zone=hardiness_zone,
            year=year,
            variety=variety
        )
        return CropScheduleResponse.from_service(schedule)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating crop schedule: {str(e)}")


@router.post("/year", response_model=List[CropScheduleResponse])
async def generate_year_calendar(
    request: CalendarYearRequest,
    service: PlantingCalendarService = Depends(get_calendar_service)
) -> List[CropScheduleResponse]:
    """Generate planting calendar for a full year with recommended crops."""
    try:
        schedules = await service.generate_year_calendar(
            hardiness_zone=request.hardiness_zone,
            year=request.year,
            latitude=request.latitude,
            elevation_m=request.elevation_m
        )
        return [CropScheduleResponse.from_service(s) for s in schedules]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating year calendar: {str(e)}")


@router.get("/crops", response_model=List[str])
async def list_available_crops(
    hardiness_zone: Optional[str] = Query(None, description="Filter crops suitable for a specific zone"),
    season: Optional[str] = Query(None, description="Filter by season: spring, summer, fall, winter"),
    service: PlantingCalendarService = Depends(get_calendar_service)
) -> List[str]:
    """List all available crops, optionally filtered by zone and season."""
    try:
        crops = await service.list_crops(
            hardiness_zone=hardiness_zone,
            season=season
        )
        return crops
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing crops: {str(e)}")


@router.get("/successions/{crop_name}", response_model=List[date])
async def calculate_succession_planting(
    crop_name: str,
    hardiness_zone: str = Query(..., description="USDA hardiness zone"),
    year: int = Query(None, description="Year (defaults to current year)"),
    interval_days: int = Query(14, ge=7, le=60, description="Days between plantings"),
    max_plantings: int = Query(5, ge=1, le=12, description="Maximum number of successions"),
    service: PlantingCalendarService = Depends(get_calendar_service)
) -> List[date]:
    """Calculate succession planting dates for continuous harvest."""
    if year is None:
        year = date.today().year
    
    try:
        successions = await service.calculate_successions(
            crop_name=crop_name,
            hardiness_zone=hardiness_zone,
            year=year,
            interval_days=interval_days,
            max_plantings=max_plantings
        )
        return successions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating successions: {str(e)}")