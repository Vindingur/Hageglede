"""
CRUD operations for Hageglede models.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from typing import Optional, Sequence, List

from . import models, schemas


class PlantCRUD:
    """CRUD operations for Plant model."""
    
    @staticmethod
    async def get(db: AsyncSession, plant_id: int) -> Optional[models.Plant]:
        """Get a plant by ID."""
        result = await db.execute(
            select(models.Plant)
            .where(models.Plant.id == plant_id)
            .options(
                selectinload(models.Plant.planting_schedules),
                selectinload(models.Plant.pests)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[models.Plant]:
        """Get multiple plants with pagination."""
        result = await db.execute(
            select(models.Plant)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(models.Plant.planting_schedules),
                selectinload(models.Plant.pests)
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[models.Plant]:
        """Get a plant by name (case-insensitive)."""
        result = await db.execute(
            select(models.Plant)
            .where(models.Plant.name.ilike(f"%{name}%"))
            .options(
                selectinload(models.Plant.planting_schedules),
                selectinload(models.Plant.pests)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, plant_in: schemas.PlantCreate) -> models.Plant:
        """Create a new plant."""
        plant = models.Plant(
            name=plant_in.name,
            botanical_name=plant_in.botanical_name,
            description=plant_in.description,
            plant_type=plant_in.plant_type,
            sun_requirements=plant_in.sun_requirements,
            water_requirements=plant_in.water_requirements,
            soil_preferences=plant_in.soil_preferences,
            hardiness_zone_min=plant_in.hardiness_zone_min,
            hardiness_zone_max=plant_in.hardiness_zone_max,
            days_to_maturity=plant_in.days_to_maturity,
            spacing_cm=plant_in.spacing_cm,
            planting_depth_cm=plant_in.planting_depth_cm,
            is_perennial=plant_in.is_perennial,
            is_vine=plant_in.is_vine,
            is_tree=plant_in.is_tree,
            is_shrub=plant_in.is_shrub,
            is_edible=plant_in.is_edible,
            notes=plant_in.notes
        )
        db.add(plant)
        await db.commit()
        await db.refresh(plant)
        return plant
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        plant_id: int, 
        plant_update: schemas.PlantUpdate
    ) -> Optional[models.Plant]:
        """Update a plant."""
        # Get plant first
        plant = await PlantCRUD.get(db, plant_id)
        if not plant:
            return None
        
        # Extract update data
        update_data = plant_update.model_dump(exclude_unset=True)
        
        # Perform update
        await db.execute(
            update(models.Plant)
            .where(models.Plant.id == plant_id)
            .values(**update_data)
        )
        await db.commit()
        
        # Return updated plant
        return await PlantCRUD.get(db, plant_id)
    
    @staticmethod
    async def delete(db: AsyncSession, plant_id: int) -> bool:
        """Delete a plant."""
        result = await db.execute(
            delete(models.Plant).where(models.Plant.id == plant_id)
        )
        await db.commit()
        return result.rowcount > 0


class ZoneCRUD:
    """CRUD operations for Zone model."""
    
    @staticmethod
    async def get(db: AsyncSession, zone_id: int) -> Optional[models.Zone]:
        """Get a zone by ID."""
        result = await db.execute(
            select(models.Zone)
            .where(models.Zone.id == zone_id)
            .options(
                selectinload(models.Zone.planting_schedules),
                selectinload(models.Zone.plants)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[models.Zone]:
        """Get multiple zones with pagination."""
        result = await db.execute(
            select(models.Zone)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(models.Zone.planting_schedules),
                selectinload(models.Zone.plants)
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def create(db: AsyncSession, zone_in: schemas.ZoneCreate) -> models.Zone:
        """Create a new zone."""
        zone = models.Zone(
            name=zone_in.name,
            description=zone_in.description,
            zone_type=zone_in.zone_type,
            size_square_meters=zone_in.size_square_meters,
            sun_exposure=zone_in.sun_exposure,
            soil_type=zone_in.soil_type,
            soil_ph=zone_in.soil_ph,
            irrigation_system=zone_in.irrigation_system,
            notes=zone_in.notes
        )
        db.add(zone)
        await db.commit()
        await db.refresh(zone)
        return zone
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        zone_id: int, 
        zone_update: schemas.ZoneUpdate
    ) -> Optional[models.Zone]:
        """Update a zone."""
        zone = await ZoneCRUD.get(db, zone_id)
        if not zone:
            return None
        
        update_data = zone_update.model_dump(exclude_unset=True)
        
        await db.execute(
            update(models.Zone)
            .where(models.Zone.id == zone_id)
            .values(**update_data)
        )
        await db.commit()
        
        return await ZoneCRUD.get(db, zone_id)
    
    @staticmethod
    async def delete(db: AsyncSession, zone_id: int) -> bool:
        """Delete a zone."""
        result = await db.execute(
            delete(models.Zone).where(models.Zone.id == zone_id)
        )
        await db.commit()
        return result.rowcount > 0


class PlantingScheduleCRUD:
    """CRUD operations for PlantingSchedule model."""
    
    @staticmethod
    async def get(db: AsyncSession, schedule_id: int) -> Optional[models.PlantingSchedule]:
        """Get a planting schedule by ID."""
        result = await db.execute(
            select(models.PlantingSchedule)
            .where(models.PlantingSchedule.id == schedule_id)
            .options(
                selectinload(models.PlantingSchedule.plant),
                selectinload(models.PlantingSchedule.zone)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[models.PlantingSchedule]:
        """Get multiple planting schedules."""
        result = await db.execute(
            select(models.PlantingSchedule)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(models.PlantingSchedule.plant),
                selectinload(models.PlantingSchedule.zone)
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def create(
        db: AsyncSession, 
        schedule_in: schemas.PlantingScheduleCreate
    ) -> models.PlantingSchedule:
        """Create a new planting schedule."""
        schedule = models.PlantingSchedule(
            plant_id=schedule_in.plant_id,
            zone_id=schedule_in.zone_id,
            planting_date=schedule_in.planting_date,
            planned_harvest_date=schedule_in.planned_harvest_date,
            actual_harvest_date=schedule_in.actual_harvest_date,
            quantity_planted=schedule_in.quantity_planted,
            spacing_cm=schedule_in.spacing_cm,
            notes=schedule_in.notes,
            status=schedule_in.status
        )
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule, ["plant", "zone"])
        return schedule
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        schedule_id: int, 
        schedule_update: schemas.PlantingScheduleUpdate
    ) -> Optional[models.PlantingSchedule]:
        """Update a planting schedule."""
        schedule = await PlantingScheduleCRUD.get(db, schedule_id)
        if not schedule:
            return None
        
        update_data = schedule_update.model_dump(exclude_unset=True)
        
        await db.execute(
            update(models.PlantingSchedule)
            .where(models.PlantingSchedule.id == schedule_id)
            .values(**update_data)
        )
        await db.commit()
        
        return await PlantingScheduleCRUD.get(db, schedule_id)
    
    @staticmethod
    async def delete(db: AsyncSession, schedule_id: int) -> bool:
        """Delete a planting schedule."""
        result = await db.execute(
            delete(models.PlantingSchedule).where(models.PlantingSchedule.id == schedule_id)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def get_by_zone(
        db: AsyncSession, 
        zone_id: int
    ) -> Sequence[models.PlantingSchedule]:
        """Get all planting schedules for a specific zone."""
        result = await db.execute(
            select(models.PlantingSchedule)
            .where(models.PlantingSchedule.zone_id == zone_id)
            .options(
                selectinload(models.PlantingSchedule.plant),
                selectinload(models.PlantingSchedule.zone)
            )
        )
        return result.scalars().all()


class PestCRUD:
    """CRUD operations for Pest model."""
    
    @staticmethod
    async def get(db: AsyncSession, pest_id: int) -> Optional[models.Pest]:
        """Get a pest by ID."""
        result = await db.execute(
            select(models.Pest)
            .where(models.Pest.id == pest_id)
            .options(selectinload(models.Pest.plants))
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_multi(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> Sequence[models.Plant]:
        """Get multiple pests with pagination."""
        result = await db.execute(
            select(models.Pest)
            .offset(skip)
            .limit(limit)
            .options(selectinload(models.Pest.plants))
        )
        return result.scalars().all()
    
    @staticmethod
    async def create(db: AsyncSession, pest_in: schemas.PestCreate) -> models.Pest:
        """Create a new pest."""
        pest = models.Pest(
            name=pest_in.name,
            scientific_name=pest_in.scientific_name,
            description=pest_in.description,
            type=pest_in.type,
            common_plants_affected=pest_in.common_plants_affected,
            organic_treatments=pest_in.organic_treatments,
            chemical_treatments=pest_in.chemical_treatments,
            prevention_methods=pest_in.prevention_methods,
            damage_symptoms=pest_in.damage_symptoms
        )
        db.add(pest)
        await db.commit()
        await db.refresh(pest)
        return pest
    
    @staticmethod
    async def update(
        db: AsyncSession, 
        pest_id: int, 
        pest_update: schemas.PestUpdate
    ) -> Optional[models.Pest]:
        """Update a pest."""
        pest = await PestCRUD.get(db, pest_id)
        if not pest:
            return None
        
        update_data = pest_update.model_dump(exclude_unset=True)
        
        await db.execute(
            update(models.Pest)
            .where(models.Pest.id == pest_id)
            .values(**update_data)
        )
        await db.commit()
        
        return await PestCRUD.get(db, pest_id)
    
    @staticmethod
    async def delete(db: AsyncSession, pest_id: int) -> bool:
        """Delete a pest."""
        result = await db.execute(
            delete(models.Pest).where(models.Pest.id == pest_id)
        )
        await db.commit()
        return result.rowcount > 0