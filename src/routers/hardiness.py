from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.database import get_db
from src.services.hardiness import HardinessZoneService

router = APIRouter(prefix="/hardiness", tags=["hardiness"])


@router.get("/zone/{postcode}")
def get_hardiness_zone(
    postcode: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Look up hardiness zone for a Norwegian postcode.
    
    Postcode format: 4 digits (e.g., 0373 for Oslo, 5006 for Bergen).
    Returns USDA hardiness zone and local climate details.
    """
    service = HardinessZoneService(db)
    
    try:
        result = service.lookup_by_postcode(postcode)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No hardiness data found for postcode {postcode}"
            )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error looking up hardiness zone: {str(e)}"
        )


@router.get("/zones")
def list_hardiness_zones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all hardiness zones with pagination.
    """
    service = HardinessZoneService(db)
    
    try:
        zones = service.list_zones(skip=skip, limit=limit)
        total = service.count_zones()
        
        return {
            "zones": zones,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing hardiness zones: {str(e)}"
        )


@router.get("/climate/{postcode}")
def get_climate_details(
    postcode: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed climate information for a postcode.
    Includes growing season length, first/last frost dates, and precipitation.
    """
    service = HardinessZoneService(db)
    
    try:
        details = service.get_climate_details(postcode)
        if not details:
            raise HTTPException(
                status_code=404,
                detail=f"No climate data found for postcode {postcode}"
            )
        return details
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching climate details: {str(e)}"
        )