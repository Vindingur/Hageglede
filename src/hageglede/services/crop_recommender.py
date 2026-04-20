"""
Crop recommender service for Hageglede.

Rule-based crop recommendation engine that matches crops to garden zones
based on zone characteristics and gardener effort level.
"""

from typing import Dict, List, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CropRecommendation:
    """Data class for crop recommendations with match scores."""
    plant_id: int
    plant_name: str
    match_score: float  # 0-100 score indicating how well the crop matches requirements
    suitability_reason: str  # Explanation of why this crop is recommended
    effort_required: str  # low, medium, high
    maintenance_tips: List[str]  # Tips for growing this crop


class CropRecommenderService:
    """Rule-based crop recommendation service."""
    
    # Hardcoded crop database with characteristics
    # Based on common Norwegian garden crops
    CROP_DATABASE = [
        {
            "id": 1,
            "name": "Tomato",
            "scientific_name": "Solanum lycopersicum",
            "zone_preference": [4, 5, 6, 7, 8, 9],  # Prefers warmer zones
            "effort_level": 3,  # Medium effort (requires staking, regular watering)
            "sunlight_needs": "full",  # full, partial, shade
            "water_needs": "medium",  # low, medium, high
            "soil_preference": "well-drained",
            "frost_tolerance": False,
            "days_to_maturity": 70,
            "is_perennial": False,
            "maintenance_tips": [
                "Requires staking or cages for support",
                "Water consistently to prevent blossom end rot",
                "Prune side shoots for better fruit production"
            ]
        },
        {
            "id": 2,
            "name": "Potato",
            "scientific_name": "Solanum tuberosum",
            "zone_preference": [2, 3, 4, 5, 6, 7, 8],  # Very hardy
            "effort_level": 2,  # Low-medium effort
            "sunlight_needs": "full",
            "water_needs": "medium",
            "soil_preference": "loose, well-drained",
            "frost_tolerance": True,
            "days_to_maturity": 90,
            "is_perennial": False,
            "maintenance_tips": [
                "Hill soil around plants as they grow",
                "Keep well-watered during tuber formation",
                "Harvest after foliage dies back"
            ]
        },
        {
            "id": 3,
            "name": "Carrot",
            "scientific_name": "Daucus carota",
            "zone_preference": [2, 3, 4, 5, 6, 7, 8, 9],
            "effort_level": 1,  # Low effort
            "sunlight_needs": "full",
            "water_needs": "medium",
            "soil_preference": "sandy, stone-free",
            "frost_tolerance": True,
            "days_to_maturity": 75,
            "is_perennial": False,
            "maintenance_tips": [
                "Thin seedlings to prevent crowding",
                "Keep soil consistently moist",
                "Harvest when tops are about 1-2cm in diameter"
            ]
        },
        {
            "id": 4,
            "name": "Lettuce",
            "scientific_name": "Lactuca sativa",
            "zone_preference": [3, 4, 5, 6, 7, 8, 9],
            "effort_level": 1,  # Low effort
            "sunlight_needs": "partial",  # Can bolt in full sun
            "water_needs": "high",
            "soil_preference": "moist, rich",
            "frost_tolerance": True,
            "days_to_maturity": 45,
            "is_perennial": False,
            "maintenance_tips": [
                "Harvest outer leaves for continuous production",
                "Provide shade in hot weather to prevent bolting",
                "Keep consistently watered"
            ]
        },
        {
            "id": 5,
            "name": "Peas",
            "scientific_name": "Pisum sativum",
            "zone_preference": [2, 3, 4, 5, 6, 7, 8],
            "effort_level": 2,  # Low-medium effort
            "sunlight_needs": "full",
            "water_needs": "medium",
            "soil_preference": "well-drained",
            "frost_tolerance": True,
            "days_to_maturity": 60,
            "is_perennial": False,
            "maintenance_tips": [
                "Provide trellis or support for climbing varieties",
                "Pick regularly to encourage more production",
                "Water at base to prevent mildew"
            ]
        },
        {
            "id": 6,
            "name": "Cabbage",
            "scientific_name": "Brassica oleracea",
            "zone_preference": [3, 4, 5, 6, 7, 8],
            "effort_level": 3,  # Medium effort (pest prone)
            "sunlight_needs": "full",
            "water_needs": "high",
            "soil_preference": "rich, moist",
            "frost_tolerance": True,
            "days_to_maturity": 80,
            "is_perennial": False,
            "maintenance_tips": [
                "Watch for cabbage worms and use row covers",
                "Keep soil consistently moist",
                "Harvest when heads feel firm"
            ]
        },
        {
            "id": 7,
            "name": "Zucchini",
            "scientific_name": "Cucurbita pepo",
            "zone_preference": [5, 6, 7, 8, 9],
            "effort_level": 1,  # Low effort (very productive)
            "sunlight_needs": "full",
            "water_needs": "medium",
            "soil_preference": "well-drained, rich",
            "frost_tolerance": False,
            "days_to_maturity": 55,
            "is_perennial": False,
            "maintenance_tips": [
                "Harvest when small for best flavor",
                "One plant produces many fruits",
                "Water at base to prevent mildew"
            ]
        },
        {
            "id": 8,
            "name": "Strawberry",
            "scientific_name": "Fragaria × ananassa",
            "zone_preference": [3, 4, 5, 6, 7, 8, 9],
            "effort_level": 2,  # Low-medium effort
            "sunlight_needs": "full",
            "water_needs": "medium",
            "soil_preference": "well-drained, slightly acidic",
            "frost_tolerance": True,
            "days_to_maturity": 0,  # Perennial
            "is_perennial": True,
            "maintenance_tips": [
                "Mulch to keep fruit clean and conserve moisture",
                "Remove runners to focus energy on fruit production",
                "Renew beds every 3-4 years"
            ]
        },
        {
            "id": 9,
            "name": "Radish",
            "scientific_name": "Raphanus sativus",
            "zone_preference": [2, 3, 4, 5, 6, 7, 8, 9],
            "effort_level": 1,  # Very low effort
            "sunlight_needs": "full",
            "water_needs": "medium",
            "soil_preference": "loose, well-drained",
            "frost_tolerance": True,
            "days_to_maturity": 30,
            "is_perennial": False,
            "maintenance_tips": [
                "Fast growing - good for beginners",
                "Thin seedlings early",
                "Harvest promptly when mature"
            ]
        },
        {
            "id": 10,
            "name": "Kale",
            "scientific_name": "Brassica oleracea var. sabellica",
            "zone_preference": [3, 4, 5, 6, 7, 8],
            "effort_level": 1,  # Low effort
            "sunlight_needs": "full",
            "water_needs": "medium",
            "soil_preference": "rich, well-drained",
            "frost_tolerance": True,
            "days_to_maturity": 60,
            "is_perennial": False,
            "maintenance_tips": [
                "Tastes sweeter after frost",
                "Harvest outer leaves for continuous production",
                "Drought tolerant once established"
            ]
        },
    ]
    
    # Zone characteristics for matching
    ZONE_CHARACTERISTICS = {
        2: {"name": "Arctic/Northern Interior", "growing_season": "very short", "last_frost": "mid-June", "first_frost": "early September"},
        3: {"name": "Northern Interior", "growing_season": "short", "last_frost": "early June", "first_frost": "mid-September"},
        4: {"name": "Northern Coastal/Inland Central", "growing_season": "moderate-short", "last_frost": "late May", "first_frost": "late September"},
        5: {"name": "Central Inland", "growing_season": "moderate", "last_frost": "mid-May", "first_frost": "early October"},
        6: {"name": "Central Coastal/Southern Inland", "growing_season": "moderate-long", "last_frost": "early May", "first_frost": "mid-October"},
        7: {"name": "Southern Coastal", "growing_season": "long", "last_frost": "late April", "first_frost": "late October"},
        8: {"name": "West Coast/South Coast", "growing_season": "very long", "last_frost": "mid-April", "first_frost": "early November"},
        9: {"name": "Extreme South/West Coast", "growing_season": "extended", "last_frost": "early April", "first_frost": "mid-November"},
    }
    
    def __init__(self):
        """Initialize crop recommender service."""
        logger.info("CropRecommenderService initialized")
    
    def recommend_crops(
        self, 
        zone: int, 
        effort_level: int,
        max_recommendations: int = 5
    ) -> List[CropRecommendation]:
        """
        Recommend crops based on zone and gardener effort level.
        
        Args:
            zone: USDA hardiness zone (2-9 for Norway)
            effort_level: Gardener effort level (1-5, where 1=lowest effort, 5=highest)
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of CropRecommendation objects sorted by match score
        """
        # Validate inputs
        if not (2 <= zone <= 9):
            raise ValueError(f"Zone must be between 2 and 9 for Norway, got {zone}")
        
        if not (1 <= effort_level <= 5):
            raise ValueError(f"Effort level must be between 1 and 5, got {effort_level}")
        
        # Calculate recommendations for all crops
        recommendations = []
        for crop in self.CROP_DATABASE:
            match_score = self._calculate_match_score(crop, zone, effort_level)
            
            if match_score > 0:  # Only include crops with some match
                effort_category = self._get_effort_category(crop["effort_level"])
                suitability_reason = self._generate_suitability_reason(crop, zone, effort_level, match_score)
                
                recommendation = CropRecommendation(
                    plant_id=crop["id"],
                    plant_name=crop["name"],
                    match_score=match_score,
                    suitability_reason=suitability_reason,
                    effort_required=effort_category,
                    maintenance_tips=crop["maintenance_tips"]
                )
                recommendations.append(recommendation)
        
        # Sort by match score (highest first) and limit results
        recommendations.sort(key=lambda x: x.match_score, reverse=True)
        return recommendations[:max_recommendations]
    
    def get_crop_by_id(self, crop_id: int) -> Optional[Dict]:
        """Get crop details by ID."""
        for crop in self.CROP_DATABASE:
            if crop["id"] == crop_id:
                return crop
        return None
    
    def get_zone_info(self, zone: int) -> Optional[Dict]:
        """Get information about a specific zone."""
        return self.ZONE_CHARACTERISTICS.get(zone)
    
    def _calculate_match_score(self, crop: Dict, zone: int, effort_level: int) -> float:
        """
        Calculate match score for a crop based on zone and effort level.
        
        Scoring breakdown:
        - Zone compatibility: 50 points max
        - Effort level match: 30 points max  
        - Crop characteristics: 20 points max
        Total: 100 points max
        """
        score = 0.0
        
        # 1. Zone compatibility (50 points)
        if zone in crop["zone_preference"]:
            # Base score for zone match
            score += 30
            
            # Bonus for crops that thrive in specific zones
            zone_range = max(crop["zone_preference"]) - min(crop["zone_preference"])
            if zone_range <= 3:  # Crops with narrow zone preferences get bonus if in preferred zone
                score += 10
            
            # Adjust for frost tolerance in colder zones
            if zone <= 4 and crop["frost_tolerance"]:
                score += 10
            elif zone >= 7 and not crop["frost_tolerance"]:
                score += 10
        else:
            # Partial credit if zone is close to preferred range
            closest_zone = min(crop["zone_preference"], key=lambda z: abs(z - zone))
            zone_diff = abs(closest_zone - zone)
            if zone_diff == 1:
                score += 15
            elif zone_diff == 2:
                score += 5
        
        # 2. Effort level match (30 points)
        crop_effort = crop["effort_level"]
        effort_diff = abs(crop_effort - effort_level)
        
        if effort_diff == 0:
            score += 25
        elif effort_diff == 1:
            score += 20
        elif effort_diff == 2:
            score += 10
        elif effort_diff == 3:
            score += 5
        
        # Bonus for low-effort crops when effort_level is low
        if effort_level <= 2 and crop_effort <= 2:
            score += 5
        
        # 3. Crop characteristics (20 points)
        # Perennial bonus for low-effort gardeners
        if effort_level <= 2 and crop["is_perennial"]:
            score += 10
        
        # Quick-maturing bonus for short growing seasons
        if zone <= 4 and crop["days_to_maturity"] <= 60:
            score += 10
        elif zone >= 7 and crop["days_to_maturity"] > 60:
            score += 5  # Longer season crops do well in warmer zones
        
        # Cap score at 100
        return min(score, 100.0)
    
    def _get_effort_category(self, effort_level: int) -> str:
        """Convert numerical effort level to category."""
        if effort_level == 1:
            return "very low"
        elif effort_level == 2:
            return "low"
        elif effort_level == 3:
            return "medium"
        elif effort_level == 4:
            return "high"
        else:
            return "very high"
    
    def _generate_suitability_reason(
        self, 
        crop: Dict, 
        zone: int, 
        effort_level: int, 
        match_score: float
    ) -> str:
        """Generate a human-readable explanation of why the crop is suitable."""
        reasons = []
        
        # Zone-related reasons
        if zone in crop["zone_preference"]:
            if crop["frost_tolerance"] and zone <= 4:
                reasons.append(f"frost-tolerant for zone {zone}")
            elif not crop["frost_tolerance"] and zone >= 7:
                reasons.append(f"thrives in warmer zone {zone}")
            else:
                reasons.append(f"well-suited for zone {zone}")
        else:
            closest = min(crop["zone_preference"], key=lambda z: abs(z - zone))
            zone_diff = abs(closest - zone)
            if zone_diff == 1:
                reasons.append(f"marginally suitable for zone {zone} (prefers zone {closest})")
            else:
                reasons.append(f"may require protection in zone {zone}")
        
        # Effort-related reasons
        crop_effort = crop["effort_level"]
        if crop_effort == effort_level:
            reasons.append("matches your preferred effort level")
        elif crop_effort < effort_level:
            reasons.append("easier than your preferred effort level")
        else:
            reasons.append("requires more effort than preferred")
        
        # Characteristic reasons
        if crop["is_perennial"]:
            reasons.append("perennial - plant once, harvest for years")
        if crop["days_to_maturity"] <= 45:
            reasons.append("fast-maturing for quick harvest")
        
        # Combine reasons
        if match_score >= 80:
            prefix = "Excellent match: "
        elif match_score >= 60:
            prefix = "Good match: "
        elif match_score >= 40:
            prefix = "Moderate match: "
        else:
            prefix = "Possible match: "
        
        return prefix + ", ".join(reasons)


# Example usage and helper function
def get_recommender_service() -> CropRecommenderService:
    """Factory function to get crop recommender service instance."""
    return CropRecommenderService()