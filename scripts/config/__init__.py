# PURPOSE: Package initialization file that defines public API for the config module, allowing other scripts to import configuration objects
# CONSUMED BY: scripts/pipeline.py imports config, DATA_DIR, DATABASE_PATH, FROST_CONFIG
# DEPENDS ON: scripts/config/config.py for the actual configuration objects; scripts/config.py for DATABASE_PATH and FROST_CONFIG
# TEST: tests/test_bug_config_import.py

"""
Configuration module for ETL pipeline settings.
"""

__all__ = ['config', 'DATA_DIR', 'DATABASE_PATH', 'FROST_CONFIG']

# Import config and DATA_DIR from the submodule scripts/config/config.py.
# This is a normal relative import — config.py lives inside this package.
from .config import config, DATA_DIR

# Import DATABASE_PATH and FROST_CONFIG from the sibling file module
# scripts/config.py.  We cannot use a normal `import config` or
# `from ..config import ...` here because both `scripts/config.py` (file
# module) and `scripts/config/` (this package) share the name `config`,
# and Python always resolves a plain `config` to this package itself,
# creating a circular import.  Using importlib lets us load the file
# module under a distinct internal name, sidestepping the collision.
import importlib.util
import os

_SIBLING_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'config.py'
)
_spec = importlib.util.spec_from_file_location(
    '_scripts_config_file_module', _SIBLING_PATH
)
_sibling = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sibling)

DATABASE_PATH = _sibling.DATABASE_PATH
FROST_CONFIG = _sibling.FROST_CONFIG
