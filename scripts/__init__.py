# PURPOSE: Package root init file for scripts module
# CONSUMED BY: pipeline.py, all submodules
# DEPENDS ON: none

"""
Scripts package for the data pipeline.
Contains fetchers, loaders, transformers, and config modules.
"""

__version__ = "1.0.0"
__all__ = ["fetchers", "loaders", "transformers", "config"]