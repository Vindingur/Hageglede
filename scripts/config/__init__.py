# PURPOSE: Package initialization file that defines public API for the config module, allowing other scripts to import configuration objects
# CONSUMED BY: scripts/pipeline.py imports config and DATA_DIR
# DEPENDS ON: scripts/config/config.py for the actual configuration objects
# TEST: none

"""
Configuration module for ETL pipeline settings.
"""

__all__ = ['config', 'DATA_DIR']

# Try direct import first, then fallback to module-level import
try:
    from .config import config, DATA_DIR
except ImportError:
    # Fallback for backward compatibility
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    from config import config, DATA_DIR