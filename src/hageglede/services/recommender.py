"""
CropRecommender service for Hageglede.
Provides crop recommendations based on postcode (hardiness zone) and user effort level.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Plant:
    """Plant data model for recommendations."""
    name: str
    effort: int  # 1-5 (1=easiest, 5=most demanding)
    yield_kg: float  # estimated yield in kilograms
    meal_ideas: List[str]
    suitable_zones: List[int]  # which hardiness zones this plant can grow in


class CropRecommender:
    """Recommends crops based on user's location and effort preference."""
    
    def __init__(self):
        # Initialize with a hardcoded list of 20 Norwegian garden plants
        self.plants = self._initialize_plants()
    
    def _initialize_plants(self) -> List[Plant]:
        """Create the hardcoded list of 20 Norwegian garden plants."""
        return [
            Plant(
                name="Poteter (Potato) 'Mandel'",
                effort=2,
                yield_kg=3.5,
                meal_ideas=["Potetmos", "Bakt potet", "Potetsalat"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Tomater (Tomato) 'Sungold'",
                effort=4,
                yield_kg=2.0,
                meal_ideas=["Salat", "Bruschetta", "Tomatsuppe"],
                suitable_zones=[3, 4, 5]
            ),
            Plant(
                name="Gulrøtter (Carrots) 'Nantes'",
                effort=2,
                yield_kg=2.5,
                meal_ideas=["Gulrotstuing", "Råkost", "Suppe"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Salat (Lettuce) 'Butterhead'",
                effort=1,
                yield_kg=1.0,
                meal_ideas=["Salat", "Wraps", "Sandwich"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Løk (Onion) 'Stuttgarter'",
                effort=2,
                yield_kg=2.0,
                meal_ideas=["Sauser", "Sote", "Suppe"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Paprika (Bell pepper) 'California Wonder'",
                effort=4,
                yield_kg=1.5,
                meal_ideas=["Fylt paprika", "Wok", "Salat"],
                suitable_zones=[3, 4, 5]
            ),
            Plant(
                name="Agurk (Cucumber) 'Marketmore'",
                effort=3,
                yield_kg=2.0,
                meal_ideas=["Salat", "Agurksalat", "Smoothie"],
                suitable_zones=[2, 3, 4, 5]
            ),
            Plant(
                name="Erter (Peas) 'Kelvedon Wonder'",
                effort=2,
                yield_kg=1.5,
                meal_ideas=["Ertepuré", "Salat", "Wok"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Bønner (Beans) 'Purple Queen'",
                effort=2,
                yield_kg=2.0,
                meal_ideas=["Bønnesalat", "Wok", "Gryterett"],
                suitable_zones=[2, 3, 4, 5]
            ),
            Plant(
                name="Blomkål (Cauliflower) 'Snowball'",
                effort=3,
                yield_kg=1.5,
                meal_ideas=["Blomkålgrateng", "Suppe", "Vegetabilsk risotto"],
                suitable_zones=[2, 3, 4, 5]
            ),
            Plant(
                name="Brokkoli (Broccoli) 'Calabrese'",
                effort=3,
                yield_kg=1.5,
                meal_ideas=["Wok", "Suppe", "Ovnstekt brokkoli"],
                suitable_zones=[2, 3, 4, 5]
            ),
            Plant(
                name="Reddik (Radish) 'Cherry Belle'",
                effort=1,
                yield_kg=0.5,
                meal_ideas=["Salat", "Dipp", "Pynt"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Spinatt (Spinach) 'Matador'",
                effort=2,
                yield_kg=1.0,
                meal_ideas=["Smoothie", "Saus", "Pai"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Squash (Squash) 'Butternut'",
                effort=3,
                yield_kg=3.0,
                meal_ideas=["Suppe", "Grateng", "Ovnstekt"],
                suitable_zones=[3, 4, 5]
            ),
            Plant(
                name="Mais (Corn) 'Sweetcorn'",
                effort=4,
                yield_kg=1.5,
                meal_ideas=["Grillet mais", "Salat", "Suppe"],
                suitable_zones=[3, 4, 5]
            ),
            Plant(
                name="Selleri (Celery) 'Green Utah'",
                effort=3,
                yield_kg=1.5,
                meal_ideas=["Suppe", "Salat", "Smoothie"],
                suitable_zones=[2, 3, 4, 5]
            ),
            Plant(
                name="Persille (Parsley) 'Mosskrøllet'",
                effort=1,
                yield_kg=0.3,
                meal_ideas=["Pynt", "Saus", "Smør"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Basilikum (Basil) 'Genovese'",
                effort=2,
                yield_kg=0.3,
                meal_ideas=["Pesto", "Salat", "Pasta"],
                suitable_zones=[3, 4, 5]
            ),
            Plant(
                name="Jordbær (Strawberries) 'Korona'",
                effort=3,
                yield_kg=1.0,
                meal_ideas=["Dessert", "Syltetøy", "Smoothie"],
                suitable_zones=[1, 2, 3, 4, 5]
            ),
            Plant(
                name="Bringebær (Raspberries) 'Glen Ample'",
                effort=3,
                yield_kg=1.5,
                meal_ideas=["Dessert", "Syltetøy", "Smoothie"],
                suitable_zones=[1, 2, 3, 4, 5]
            )
        ]
    
    def _postcode_to_zone(self, postcode_str: str) -> int:
        """
        Convert Norwegian postcode to hardiness zone.
        
        Mapping:
        0-1999 = zone 1
        2000-2999 = zone 2
        3000-4999 = zone 3
        5000-7999 = zone 4
        8000-9999 = zone 5
        
        Args:
            postcode_str: Norwegian postcode as string
            
        Returns:
            Hardiness zone (1-5)
            
        Raises:
            ValueError: If postcode is invalid
        """
        try:
            postcode = int(postcode_str)
        except ValueError:
            raise ValueError(f"Invalid postcode: {postcode_str}")
        
        if not (0 <= postcode <= 9999):
            raise ValueError(f"Postcode must be between 0000-9999: {postcode}")
        
        if postcode <= 1999:
            return 1
        elif postcode <= 2999:
            return 2
        elif postcode <= 4999:
            return 3
        elif postcode <= 7999:
            return 4
        else:  # 8000-9999
            return 5
    
    def recommend(self, postcode: str, effort: int) -> List[Plant]:
        """
        Recommend plants based on postcode and effort level.
        
        Args:
            postcode: Norwegian postcode (e.g., "0123", "5000", "9010")
            effort: Maximum effort level (1-5), where 1=easiest, 5=most demanding
            
        Returns:
            List of Plant objects sorted by yield (descending)
            
        Raises:
            ValueError: If effort is not between 1-5
        """
        if not (1 <= effort <= 5):
            raise ValueError(f"Effort must be between 1-5: {effort}")
        
        # Convert postcode to zone
        zone = self._postcode_to_zone(postcode)
        
        # Filter plants: effort ≤ requested effort AND suitable for the zone
        filtered_plants = [
            plant for plant in self.plants
            if plant.effort <= effort and zone in plant.suitable_zones
        ]
        
        # Sort by yield descending
        filtered_plants.sort(key=lambda p: p.yield_kg, reverse=True)
        
        return filtered_plants
    
    def get_all_plants(self) -> List[Plant]:
        """Get all available plants (for debugging or UI display)."""
        return self.plants


# Singleton instance for easy import
recommender = CropRecommender()