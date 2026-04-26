# PURPOSE: Config module for ETL pipeline
# CONSUMED BY: gbif.py, artsbanken.py, utils/config_reader.py
# DEPENDS ON: none

"""Configuration module for the hageglede ETL pipeline."""
from .config_reader import read_config, get_db_credentials

__all__ = ["read_config", "get_db_credentials"]