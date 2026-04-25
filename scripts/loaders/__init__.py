# PURPOSE: Module wrapper for loaders package
# CONSUMED BY: pipeline.py, loaders modules
# DEPENDS ON: none

from .plant_loader import load_plant_data

__all__ = ['load_plant_data']