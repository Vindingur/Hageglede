# PURPOSE: Package initialization file that defines public API for the config module, allowing other scripts to import configuration objects
# CONSUMED BY: scripts/pipeline.py imports config, DATA_DIR, DATABASE_PATH, FROST_CONFIG
# DEPENDS ON: scripts/config/config.py for the actual configuration objects; scripts/config.py for DATABASE_PATH and FROST_CONFIG
# TEST: tests/test_bug_config_import.py

"""
Configuration module for ETL pipeline settings.
"""

__all__ = ['config', 'DATA_DIR', 'DATABASE_PATH', 'FROST_CONFIG']

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

# Import DATABASE_PATH and FROST_CONFIG from the standalone scripts/config.py
# (these names are not in the package submodule scripts/config/config.py)
import sys
import os
_cfg_parent = os.path.dirname(os.path.dirname(__file__))
if _cfg_parent not in sys.path:
    sys.path.insert(0, _cfg_parent)
from config import DATABASE_PATH, FROST_CONFIG
