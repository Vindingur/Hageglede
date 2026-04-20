"""
Unit tests for the CropRecommender service.
"""

import pytest
from src.hageglede.services.recommender import CropRecommender, Plant


class TestPlant:
    """Test the Plant dataclass."""
    
    def test_plant_creation(self):
        """Test that a Plant can be created with all required fields."""
        plant = Plant(
            name="Kål",
            effort=3,
            yield_kg=2.5,
            meal_ideas=["Kålsuppe", "Kålstuing", "Fyldte kålblade"],
            suitable_zones={1, 2, 3}
        )
        
        assert plant.name == "Kål"
        assert plant.effort == 3
        assert plant.yield_kg == 2.5
        assert plant.meal_ideas == ["Kålsuppe", "Kålstuing", "Fyldte kålblade"]
        assert plant.suitable_zones == {1, 2, 3}


class TestCropRecommender:
    """Test the CropRecommender service."""
    
    def setup_method(self):
        """Create a fresh recommender instance for each test."""
        self.recommender = CropRecommender()
    
    def test_zone_mapping(self):
        """Test the postcode to zone mapping."""
        # Zone 1: 0-1999
        assert self.recommender._get_zone_from_postcode("0001") == 1
        assert self.recommender._get_zone_from_postcode("1999") == 1
        
        # Zone 2: 2000-2999
        assert self.recommender._get_zone_from_postcode("2000") == 2
        assert self.recommender._get_zone_from_postcode("2999") == 2
        
        # Zone 3: 3000-4999
        assert self.recommender._get_zone_from_postcode("3000") == 3
        assert self.recommender._get_zone_from_postcode("4999") == 3
        
        # Zone 4: 5000-7999
        assert self.recommender._get_zone_from_postcode("5000") == 4
        assert self.recommender._get_zone_from_postcode("7999") == 4
        
        # Zone 5: 8000-9999
        assert self.recommender._get_zone_from_postcode("8000") == 5
        assert self.recommender._get_zone_from_postcode("9999") == 5
    
    def test_recommendation_basic_filters(self):
        """Test that recommendations filter by effort and zone."""
        # Test with zone 2 and effort 3
        results = self.recommender.recommend("2500", 3)
        
        # All results should have effort <= 3 and be suitable for zone 2
        for plant in results:
            assert plant.effort <= 3
            assert 2 in plant.suitable_zones
    
    def test_recommendation_sorting(self):
        """Test that recommendations are sorted by yield descending."""
        results = self.recommender.recommend("1000", 5)  # Zone 1, max effort
        
        # Should be sorted by yield_kg descending
        yields = [plant.yield_kg for plant in results]
        assert yields == sorted(yields, reverse=True)
    
    def test_recommendation_effort_filter(self):
        """Test that effort filtering works correctly."""
        # Get recommendations with different effort levels
        low_effort = self.recommender.recommend("1000", 1)  # Only effort 1 plants
        medium_effort = self.recommender.recommender.recommend("1000", 3)  # Effort 1-3 plants
        high_effort = self.recommender.recommender.recommend("1000", 5)  # All plants
        
        # Higher effort should include all plants from lower effort
        low_effort_names = {plant.name for plant in low_effort}
        medium_effort_names = {plant.name for plant in medium_effort}
        high_effort_names = {plant.name for plant in high_effort}
        
        # Low effort plants should be subset of medium effort
        assert low_effort_names.issubset(medium_effort_names)
        # Medium effort plants should be subset of high effort
        assert medium_effort_names.issubset(high_effort_names)
    
    def test_zone_filtering(self):
        """Test that zone filtering works correctly."""
        # Get recommendations for different zones
        zone1_results = self.recommender.recommender.recommend("1000", 5)  # Zone 1
        zone5_results = self.recommender.recommender.recommend("9000", 5)  # Zone 5
        
        # Some plants may be suitable for multiple zones, but there should be differences
        # At minimum, verify the logic is applied
        for plant in zone1_results:
            assert 1 in plant.suitable_zones
        for plant in zone5_results:
            assert 5 in plant.suitable_zones
    
    def test_plant_list_completeness(self):
        """Test that all 20 plants are defined."""
        assert len(self.recommender.plants) == 20
        
        # Check that we have a variety of plants
        plant_names = {plant.name for plant in self.recommender.plants}
        expected_plants = {
            "Potet", "Gulrot", "Løk", "Hvitkål", "Rødkål", "Salat", "Spinat",
            "Bønner", "Erter", "Agurk", "Squash", "Tomater", "Jordbær",
            "Bringebær", "Rips", "Epler", "Pærer", "Solsikkefrø", "Salvie",
            "Tymian"
        }
        
        # All expected plants should be present
        for plant in expected_plants:
            assert plant in plant_names
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Invalid postcode (non-numeric)
        with pytest.raises(ValueError):
            self.recommender.recommend("ABCD", 3)
        
        # Postcode out of range (too high)
        with pytest.raises(ValueError):
            self.recommender.recommend("10000", 3)
        
        # Postcode negative
        with pytest.raises(ValueError):
            self.recommender.recommend("-100", 3)
        
        # Invalid effort (negative)
        with pytest.raises(ValueError):
            self.recommender.recommend("1000", -1)
        
        # Invalid effort (too high)
        with pytest.raises(ValueError):
            self.recommender.recommend("1000", 6)