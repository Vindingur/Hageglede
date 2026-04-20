from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from src.database import get_db
from src.models.plot import Plot
from src.models.user import User
from src.schemas.plot import PlotCreate, PlotUpdate, PlotResponse
from src.core.security import get_current_user

router = APIRouter(prefix="/plots", tags=["plots"])


@router.post("/", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
def create_plot(
    plot: PlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new plot for the authenticated user."""
    db_plot = Plot(
        user_id=current_user.id,
        name=plot.name,
        description=plot.description,
        geometry=plot.geometry,
        area_sqm=plot.area_sqm,
        soil_type=plot.soil_type,
        sunlight_hours=plot.sunlight_hours,
    )
    db.add(db_plot)
    db.commit()
    db.refresh(db_plot)
    return db_plot


@router.get("/", response_model=List[PlotResponse])
def list_plots(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all plots for the authenticated user."""
    plots = db.query(Plot).filter(Plot.user_id == current_user.id).offset(skip).limit(limit).all()
    return plots


@router.get("/{plot_id}", response_model=PlotResponse)
def get_plot(
    plot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific plot by ID."""
    plot = db.query(Plot).filter(Plot.id == plot_id, Plot.user_id == current_user.id).first()
    if not plot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")
    return plot


@router.put("/{plot_id}", response_model=PlotResponse)
def update_plot(
    plot_id: UUID,
    plot_update: PlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific plot."""
    plot = db.query(Plot).filter(Plot.id == plot_id, Plot.user_id == current_user.id).first()
    if not plot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")
    
    update_data = plot_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plot, field, value)
    
    db.commit()
    db.refresh(plot)
    return plot


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot(
    plot_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a specific plot."""
    plot = db.query(Plot).filter(Plot.id == plot_id, Plot.user_id == current_user.id).first()
    if not plot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")
    
    db.delete(plot)
    db.commit()
    return None