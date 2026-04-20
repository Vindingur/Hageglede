"""
Unit tests for the CropRecommender service.
"""

import pytest
from src.hageglede.services.crop_recommender import CropRecommender


class TestCropRecommender:
    """Test suite for CropRecommender."""

    @pytest.fixture
    def recommender(self):
        """Create a CropRecommender instance."""
        return CropRecommender()

    def test_recommend_crops_basic_zone_1(self, recommender):
        """Test crop recommendations for zone 1."""
        zone = 1
        effort_level = 3
        recommendations = recommender.recommend_crops(zone, effort_level)

        assert len(recommendations) > 0
        for rec in recommendations:
            assert "crop" in rec
            assert "match_score" in rec
            assert isinstance(rec["match_score"], float)
            assert 0 <= rec["match_score"] <= 1

        # Zone 1 is cooler climate, should include hardy vegetables
        crop_names = [rec["crop"] for rec in recommendations]
        assert any("kale" in name.lower() or "cabbage" in name.lower() 
                  for name in crop_names)

    def test_recommend_crops_basic_zone_8(self, recommender):
        """Test crop recommendations for zone 8 (warmer climate)."""
        zone = 8
        effort_level = 3
        recommendations = recommender.recommend_crops(zone, effort_level)

        assert len(recommendations) > 0
        for rec in recommendations:
            assert "crop" in rec
            assert "match_score" in rec

        # Zone 8 is warmer, should include heat-loving crops
        crop_names = [rec["crop"] for rec in recommendations]
        assert any("tomato" in name.lower() or "pepper" in name.lower() 
                  for name in crop_names)

    def test_recommend_crops_low_effort(self, recommender):
        """Test low effort level recommendations."""
        zone = 5
        effort_level = 1
        recommendations = recommender.recommend_crops(zone, effort_level)

        assert len(recommendations) > 0
        # Low effort crops should have high scores for low effort
        low_effort_crops = ["carrot", "lettuce", "radish"]
        for rec in recommendations:
            if any(crop in rec["crop"].lower() for crop in low_effort_crops):
                assert rec["match_score"] >= 0.7

    def test_recommend_crops_high_effort(self, recommender):
        """Test high effort level recommendations."""
        zone = 5
        effort_level = 5
        recommendations = recommender.recommend_crops(zone, effort_level)

        assert len(recommendations) > 0
        # High effort crops should have high scores for high effort
        high_effort_crops = ["tomato", "cucumber", "zucchini"]
        for rec in recommendations:
            if any(crop in rec["crop"].lower() for crop in high_effort_crops):
                assert rec["match_score"] >= 0.7

    def test_recommend_crops_effort_range(self, recommender):
        """Test all valid effort levels."""
        zone = 4
        for effort in range(1, 6):
            recommendations = recommender.recommend_crops(zone, effort)
            assert len(recommendations) > 0
            # Each effort level should produce recommendations
            assert all(0.5 <= rec["match_score"] <= 1.0 
                      for rec in recommendations[:3])  # Check top 3

    def test_recommend_crops_zone_range(self, recommender):
        """Test all valid zone ranges."""
        effort_level = 3
        for zone in range(1, 14):
            recommendations = recommender.recommend_crops(zone, effort_level)
            assert len(recommendations) > 0
            # Each zone should produce recommendations
            assert all("crop" in rec and "match_score" in rec 
                      for rec in recommendations)

    def test_recommend_crops_invalid_effort_low(self, recommender):
        """Test effort level below valid range."""
        zone = 5
        with pytest.raises(ValueError):
            recommender.recommend_crops(zone, 0)

    def test_recommend_crops_invalid_effort_high(self, recommender):
        """Test effort level above valid range."""
        zone = 5
        with pytest.raises(ValueError):
            recommender.recommend_crops(zone, 6)

    def test_recommend_crops_invalid_zone_low(self, recommender):
        """Test zone below valid range."""
        effort_level = 3
        with pytest.raises(ValueError):
            recommender.recommend_crops(0, effort_level)

    def test_recommend_crops_invalid_zone_high(self, recommender):
        """Test zone above valid range."""
        effort_level = 3
        with pytest.raises(ValueError):
            recommender.recommender.recommend_crops(14, effort_level)

    def test_recommend_crops_with_limit(self, recommender):
        """Test limiting number of recommendations."""
        zone = 5
        effort_level = 3
        limit = 2
        recommendations = recommender.recommend_crops(zone, effort_level, limit=limit)

        assert len(recommendations) == limit
        # Recommendations should be sorted by match score (descending)
        scores = [rec["match_score"] for rec in recommendations]
        assert scores == sorted(scores, reverse=True)

    def test_get_crop_database_match_scores(self, recommender):
        """Test database crop matching scores."""
        zone = 5
        effort_level = 3
        matches = recommender._get_crop_database_matches(zone, effort_level)

        assert len(matches) > 0
        for match in matches:
            assert "crop" in match
            assert "zone_match" in match
            assert "effort_match" in match
            assert "total_score" in match
            assert 0 <= match["zone_match"] <= 1
            assert 0 <= match["effort_match"] <= 1
            assert 0 <= match["total_score"] <= 1

    def test_zone_classification_cold(self, recommender):
        """Test zone classification for cold climates."""
        assert recommender._classify_zone(1) == "cold"
        assert recommender._classify_zone(3) == "cold"

    def test_zone_classification_moderate(self, recommender):
        """Test zone classification for moderate climates."""
        assert recommender._classify_zone(5) == "moderate"
        assert recommender._classify_zone(7) == "moderate"

    def test_zone_classification_warm(self, recommender):
        """Test zone classification for warm climates."""
        assert recommender._classify_zone(9) == "warm"
        assert recommender._classify_zone(12) == "warm"

    def test_effort_classification_low(self, recommender):
        """Test effort classification for low effort."""
        assert recommender._classify_effort(1) == "low"
        assert recommender._classify_effort(2) == "low"

    def test_effort_classification_medium(self, recommender):
        """Test effort classification for medium effort."""
        assert recommender._classify_effort(3) == "medium"

    def test_effort_classification_high(self, recommender):
        """Test effort classification for high effort."""
        assert recommender._classify_effort(4) == "high"
        assert recommender._classify_effort(5) == "high"

    def test_calculate_match_score(self, recommender):
        """Test match score calculation."""
        # Perfect match
        assert recommender._calculate_match_score(1.0, 1.0) == 1.0
        
        # Good match
        assert 0.7 <= recommender._calculate_match_score(0.8, 0.9) <= 0.85
        
        # Poor match
        assert recommender._calculate_match_score(0.3, 0.4) < 0.5
        
        # Zero match
        assert recommender._calculate_match_score(0.0, 0.0) == 0.0