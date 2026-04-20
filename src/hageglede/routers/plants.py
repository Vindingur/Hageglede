from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from .. import crud, models, schemas

router = APIRouter(prefix="/plants", tags=["plants"])


@router.get("/", response_model=List[schemas.PlantResponse])
async def list_plants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    zone_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List plants with optional zone filtering."""
    if zone_id:
        plants = await crud.get_plants_by_zone(db, zone_id=zone_id, skip=skip, limit=limit)
    else:
        plants = await crud.get_plants(db, skip=skip, limit=limit)
    return plants


@router.get("/{plant_id}", response_model=schemas.PlantResponse)
async def get_plant(plant_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific plant by ID."""
    plant = await crud.get_plant(db, plant_id=plant_id)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.post("/", response_model=schemas.PlantResponse, status_code=201)
async def create_plant(
    plant: schemas.PlantCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new plant."""
    return await crud.create_plant(db, plant=plant)


@router.put("/{plant_id}", response_model=schemas.PlantResponse)
async def update_plant(
    plant_id: int,
    plant_update: schemas.PlantUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing plant."""
    plant = await crud.update_plant(db, plant_id=plant_id, plant_update=plant_update)
    if plant is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.delete("/{plant_id}", status_code=204)
async def delete_plant(plant_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a plant."""
    success = await crud.delete_plant(db, plant_id=plant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")
    return None