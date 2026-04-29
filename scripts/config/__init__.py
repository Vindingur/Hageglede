# PURPOSE: Package initialization file that defines public API for the config module, allowing other scripts to import configuration objects.
# CONSUMED BY: scripts/pipeline.py imports config and DATA_DIR
# DEPENDS ON: scripts/config.py for the actual configuration objects
# TEST: none

"""
Configuration module for ETL pipeline settings.
"""

from .config import config, DATA_DIR

__all__ = ['config', 'DATA_DIR']