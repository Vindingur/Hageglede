"""
Planting calendar service for Hageglede.

Calculates sowing windows, planting dates, and harvest predictions
based on hardiness zones, crop types, and Norwegian climate data.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class PlantingCalendarService:
    """Service for calculating planting schedules and harvest predictions."""
    
    # Hardiness zone data for Norway (USDA zones 2-9)
    # Zone 2-3: Northern Norway, interior
    # Zone 4-5: Coastal Northern Norway, inland Central
    # Zone 6-7: Coastal Central, Southern inland
    # Zone 8-9: Coastal South & West, including Oslo, Bergen, Stavanger
    
    # Crop definitions with growing requirements
    CROPS = {
        "tomato": {
            "name": "Tomato",
            "type": "warm_season",
            "sowing_window_start": {"zone2": "late_june", "zone8": "mid_february"},
            "transplant_window_start": {"zone2": "early_july", "zone8": "late_april"},
            "days_to_maturity": 70,
            "frost_tolerant": False,
            "requires_indoor_start": True,
        },
        "potato": {
            "name": "Potato",
            "type": "cool_season",
            "sowing_window_start": {"zone2": "late_may", "zone8": "mid_march"},
            "transplant_window_start": None,  # Direct sowing
            "days_to_maturity": 90,
            "frost_tolerant": True,
            "requires_indoor_start": False,
        },
        "carrot": {
            "name": "Carrot",
            "type": "cool_season",
            "sowing_window_start": {"zone2": "early_june", "zone8": "mid_march"},
            "transplant_window_start": None,
            "days_to_maturity": 75,
            "frost_tolerant": True,
            "requires_indoor_start": False,
        },
        "lettuce": {
            "name": "Lettuce",
            "type": "cool_season",
            "sowing_window_start": {"zone2": "early_june", "zone8": "mid_march"},
            "transplant_window_start": {"zone2": "mid_june", "zone8": "mid_april"},
            "days_to_maturity": 45,
            "frost_tolerant": True,
            "requires_indoor_start": True,
        },
        "peas": {
            "name": "Peas",
            "type": "cool_season",
            "sowing_window_start": {"zone2": "late_may", "zone8": "early_march"},
            "transplant_window_start": None,
            "days_to_maturity": 60,
            "frost_tolerant": True,
            "requires_indoor_start": False,
        },
        "cabbage": {
            "name": "Cabbage",
            "type": "cool_season",
            "sowing_window_start": {"zone2": "mid_may", "zone8": "mid_february"},
            "transplant_window_start": {"zone2": "mid_june", "zone8": "mid_april"},
            "days_to_maturity": 80,
            "frost_tolerant": True,
            "requires_indoor_start": True,
        },
        "zucchini": {
            "name": "Zucchini",
            "type": "warm_season",
            "sowing_window_start": {"zone2": "early_june", "zone8": "mid_april"},
            "transplant_window_start": {"zone2": "late_june", "zone8": "mid_may"},
            "days_to_maturity": 55,
            "frost_tolerant": False,
            "requires_indoor_start": True,
        },
        "strawberry": {
            "name": "Strawberry",
            "type": "perennial",
            "planting_window": {"zone2": "early_june", "zone8": "mid_april"},
            "transplant_window_start": None,
            "days_to_maturity": 0,  # Perennial, harvest next year
            "frost_tolerant": True,
            "requires_indoor_start": False,
        },
    }
    
    # Norwegian month to approximate date mapping
    MONTH_MAPPING = {
        "mid_february": (2, 15),
        "late_february": (2, 25),
        "early_march": (3, 5),
        "mid_march": (3, 15),
        "late_march": (3, 25),
        "early_april": (4, 5),
        "mid_april": (4, 15),
        "late_april": (4, 25),
        "early_may": (5, 5),
        "mid_may": (5, 15),
        "late_may": (5, 25),
        "early_june": (6, 5),
        "mid_june": (6, 15),
        "late_june": (6, 25),
        "early_july": (7, 5),
        "mid_july": (7, 15),
        "late_july": (7, 25),
    }
    
    def __init__(self):
        """Initialize planting calendar service."""
        self.current_year = date.today().year
    
    def get_crop_list(self) -> List[Dict]:
        """Get list of available crops with basic information."""
        crops = []
        for crop_id, crop_data in self.CROPS.items():
            crops.append({
                "id": crop_id,
                "name": crop_data["name"],
                "type": crop_data["type"],
                "frost_tolerant": crop_data["frost_tolerant"],
                "requires_indoor_start": crop_data["requires_indoor_start"],
            })
        return crops
    
    def get_crop_schedule(
        self,
        crop_id: str,
        hardiness_zone: int,
        current_date: Optional[date] = None
    ) -> Dict:
        """
        Calculate planting schedule for a specific crop in a given hardiness zone.
        
        Args:
            crop_id: Identifier for the crop (e.g., "tomato")
            hardiness_zone: USDA hardiness zone (2-9 for Norway)
            current_date: Optional current date for calculating relative dates
            
        Returns:
            Dictionary with sowing, planting, and harvest dates
        """
        if crop_id not in self.CROPS:
            raise ValueError(f"Unknown crop: {crop_id}")
        
        if not (2 <= hardiness_zone <= 9):
            raise ValueError(f"Hardiness zone must be between 2 and 9 for Norway, got {hardiness_zone}")
        
        crop = self.CROPS[crop_id]
        zone_key = f"zone{hardiness_zone}"
        
        # Use closest zone if exact zone not defined
        if zone_key not in crop.get("sowing_window_start", {}):
            # Find closest zone
            available_zones = [int(k.replace("zone", "")) for k in crop.get("sowing_window_start", {}).keys()]
            closest_zone = min(available_zones, key=lambda z: abs(z - hardiness_zone))
            zone_key = f"zone{closest_zone}"
            logger.info(f"Using zone {closest_zone} data for zone {hardiness_zone} for crop {crop_id}")
        
        # Calculate sowing date
        sowing_period = crop.get("sowing_window_start", {}).get(zone_key)
        if not sowing_period:
            sowing_date = None
        else:
            sowing_date = self._period_to_date(sowing_period)
        
        # Calculate transplant date (if applicable)
        transplant_period = crop.get("transplant_window_start", {}).get(zone_key) if crop.get("transplant_window_start") else None
        if transplant_period:
            transplant_date = self._period_to_date(transplant_period)
        else:
            transplant_date = None
        
        # Calculate harvest date
        harvest_date = None
        if sowing_date and crop["days_to_maturity"] > 0:
            # For annual crops, add days to maturity to sowing date
            harvest_date = sowing_date + timedelta(days=crop["days_to_maturity"])
        elif crop.get("planting_window") and zone_key in crop.get("planting_window", {}):
            # For perennials like strawberries
            planting_period = crop["planting_window"][zone_key]
            harvest_date = self._period_to_date(planting_period)
            # Perennials are typically planted for harvest next season
            harvest_date = harvest_date.replace(year=harvest_date.year + 1)
        
        # Calculate relative timing indicators
        current_date = current_date or date.today()
        status = self._calculate_crop_status(current_date, sowing_date, transplant_date, harvest_date)
        
        return {
            "crop_id": crop_id,
            "crop_name": crop["name"],
            "hardiness_zone": hardiness_zone,
            "crop_type": crop["type"],
            "frost_tolerant": crop["frost_tolerant"],
            "requires_indoor_start": crop["requires_indoor_start"],
            "sowing_date": sowing_date.isoformat() if sowing_date else None,
            "transplant_date": transplant_date.isoformat() if transplant_date else None,
            "harvest_date": harvest_date.isoformat() if harvest_date else None,
            "days_to_maturity": crop["days_to_maturity"],
            "status": status,
            "current_date": current_date.isoformat(),
        }
    
    def get_seasonal_schedule(
        self,
        hardiness_zone: int,
        season: Optional[str] = None
    ) -> Dict:
        """
        Get planting schedule for all crops in a zone, optionally filtered by season.
        
        Args:
            hardiness_zone: USDA hardiness zone (2-9)
            season: Optional season filter ("spring", "summer", "autumn", "winter")
            
        Returns:
            Dictionary with seasonal planting schedule
        """
        all_schedules = []
        current_date = date.today()
        
        for crop_id in self.CROPS:
            try:
                schedule = self.get_crop_schedule(crop_id, hardiness_zone, current_date)
                
                # Filter by season if specified
                if season:
                    sowing_date = schedule.get("sowing_date")
                    if sowing_date:
                        sowing_month = datetime.fromisoformat(sowing_date).month
                        crop_season = self._month_to_season(sowing_month)
                        if crop_season != season:
                            continue
                
                all_schedules.append(schedule)
            except ValueError:
                # Skip crops that don't have data for this zone
                continue
        
        # Sort by sowing date
        all_schedules.sort(key=lambda x: x.get("sowing_date") or "9999-12-31")
        
        return {
            "hardiness_zone": hardiness_zone,
            "season": season,
            "current_date": current_date.isoformat(),
            "crop_schedules": all_schedules,
        }
    
    def get_harvest_prediction(
        self,
        crop_id: str,
        planting_date: date,
        hardiness_zone: int
    ) -> Dict:
        """
        Predict harvest date based on actual planting date.
        
        Args:
            crop_id: Crop identifier
            planting_date: Actual planting date
            hardiness_zone: USDA hardiness zone
            
        Returns:
            Dictionary with harvest prediction and recommendations
        """
        if crop_id not in self.CROPS:
            raise ValueError(f"Unknown crop: {crop_id}")
        
        crop = self.CROPS[crop_id]
        
        # Calculate expected harvest date
        if crop["days_to_maturity"] > 0:
            harvest_date = planting_date + timedelta(days=crop["days_to_maturity"])
        else:
            # For perennials, next season
            harvest_date = planting_date.replace(year=planting_date.year + 1)
        
        # Check if planting is too early/late for zone
        zone_key = f"zone{hardiness_zone}"
        recommended_sowing = crop.get("sowing_window_start", {}).get(zone_key)
        recommended_date = self._period_to_date(recommended_sowing) if recommended_sowing else None
        
        timing_status = "optimal"
        if recommended_date:
            days_diff = (planting_date - recommended_date).days
            if days_diff < -14:
                timing_status = "early"
            elif days_diff > 14:
                timing_status = "late"
        
        # Weather risk assessment
        risk_factors = []
        if not crop["frost_tolerant"]:
            # Check if planting is before last frost date (approximate)
            last_frost_by_zone = {
                2: (6, 15),  # Mid-June
                3: (6, 10),  # Early June
                4: (5, 30),  # Late May
                5: (5, 20),  # Mid-May
                6: (5, 10),  # Early May
                7: (4, 30),  # Late April
                8: (4, 20),  # Mid-April
                9: (4, 10),  # Early April
            }
            
            if hardiness_zone in last_frost_by_zone:
                last_frost_month, last_frost_day = last_frost_by_zone[hardiness_zone]
                last_frost_date = date(planting_date.year, last_frost_month, last_frost_day)
                if planting_date < last_frost_date:
                    risk_factors.append("frost_risk")
        
        return {
            "crop_id": crop_id,
            "crop_name": crop["name"],
            "planting_date": planting_date.isoformat(),
            "predicted_harvest_date": harvest_date.isoformat(),
            "days_to_maturity": crop["days_to_maturity"],
            "timing_status": timing_status,
            "recommended_sowing_period": recommended_sowing,
            "risk_factors": risk_factors,
            "recommendations": self._generate_recommendations(crop, timing_status, risk_factors),
        }
    
    def _period_to_date(self, period: str) -> date:
        """Convert period string like 'mid_march' to actual date for current year."""
        if period not in self.MONTH_MAPPING:
            # Default to mid-March if period not found
            month, day = (3, 15)
        else:
            month, day = self.MONTH_MAPPING[period]
        
        return date(self.current_year, month, day)
    
    def _calculate_crop_status(
        self,
        current_date: date,
        sowing_date: Optional[date],
        transplant_date: Optional[date],
        harvest_date: Optional[date]
    ) -> str:
        """Calculate current status of crop based on dates."""
        if not sowing_date:
            return "unknown"
        
        if current_date < sowing_date:
            return "planning"
        elif transplant_date and current_date < transplant_date:
            return "sowing"
        elif transplant_date and current_date >= transplant_date:
            if harvest_date and current_date >= harvest_date:
                return "harvested"
            else:
                return "growing"
        elif harvest_date and current_date >= harvest_date:
            return "harvested"
        else:
            return "growing"
    
    def _month_to_season(self, month: int) -> str:
        """Convert month number to season."""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:  # 9, 10, 11
            return "autumn"
    
    def _generate_recommendations(
        self,
        crop: Dict,
        timing_status: str,
        risk_factors: List[str]
    ) -> List[str]:
        """Generate planting recommendations based on crop and conditions."""
        recommendations = []
        
        if timing_status == "early":
            recommendations.append("Consider starting indoors or using cloches for protection.")
        elif timing_status == "late":
            recommendations.append("Choose fast-maturing varieties to ensure harvest before frost.")
        
        if "frost_risk" in risk_factors:
            recommendations.append("Protect with row covers or cloches until risk of frost has passed.")
        
        if crop["requires_indoor_start"]:
            recommendations.append("Start seeds indoors 6-8 weeks before transplanting.")
        
        if crop["type"] == "warm_season":
            recommendations.append("Plant in a warm, sunny location with good drainage.")
        elif crop["type"] == "cool_season":
            recommendations.append("Can tolerate light frost; may bolt in hot weather.")
        
        return recommendations