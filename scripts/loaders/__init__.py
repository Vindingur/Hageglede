# PURPOSE: Public interface for data loaders module
# CONSUMED BY: scripts/pipeline.py, any script importing from scripts.loaders
# DEPENDS ON: scripts/loaders/weather_loader.py, scripts/loaders/plant_loader.py
# TEST: none

"""
Data loaders for Aletheia agricultural pipeline.

This module provides standardized interfaces for loading weather and plant data
from various sources.
"""

from .weather_loader import load_weather_data
from .plant_loader import load_plant_data

__all__ = ["load_weather_data", "load_plant_data"]