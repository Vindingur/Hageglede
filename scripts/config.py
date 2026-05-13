# PURPOSE: Central configuration module exporting module-level constants and the ConfigManager class for use by the ETL pipeline.
# CONSUMED BY: scripts/pipeline.py, scripts.fetchers.met, scripts.fetchers.artsdbanken, scripts.transformers.climate, scripts.transformers.plants, scripts.loaders.weather_loader, scripts.loaders.plant_loader
# DEPENDS ON: none
# TEST: none

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

# Module-level constants for backward compatibility
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/aletheia.db")
FROST_CONFIG = {
    "client_id": os.getenv("FROST_CLIENT_ID", ""),
    "client_secret": os.getenv("FROST_CLIENT_SECRET", ""),
    "endpoint": "https://frost.met.no/observations/v0.jsonld",
    "station_id": "SN18700",
    "location": {"lat": 59.9139, "lon": 10.7522},
}
ARTSDATABANKEN_CONFIG = {
    "endpoint": "https://artsdatabanken.no/api/",
    "timeout": 30,
}


@dataclass
class DatabaseConfig:
    path: str = DATABASE_PATH


@dataclass
class SourceConfig:
    name: str
    config: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """Central configuration manager for the Aletheia ETL pipeline.

    Provides structured access to database settings and external source
    configurations (MET Frost, Artsdatabanken, etc.).
    """

    def __init__(self) -> None:
        self.database = DatabaseConfig()
        self._sources: Dict[str, SourceConfig] = {
            "MET": SourceConfig(name="MET", config=FROST_CONFIG),
            "ARTSDATABANKEN": SourceConfig(name="ARTSDATABANKEN", config=ARTSDATABANKEN_CONFIG),
        }

    def load(self) -> "ConfigManager":
        """Load/refresh configuration from environment.

        Returns self so callers can chain or immediately use the instance.
        """
        self.database.path = os.getenv("DATABASE_PATH", DATABASE_PATH)
        self._sources["MET"].config = {
            "client_id": os.getenv("FROST_CLIENT_ID", FROST_CONFIG["client_id"]),
            "client_secret": os.getenv("FROST_CLIENT_SECRET", FROST_CONFIG["client_secret"]),
            "endpoint": FROST_CONFIG["endpoint"],
            "station_id": FROST_CONFIG["station_id"],
            "location": FROST_CONFIG["location"],
        }
        return self

    def get_source(self, name: str) -> Dict[str, Any]:
        """Return the configuration dict for a named external source.

        Raises KeyError if the source is not registered.
        """
        return self._sources[name].config

    def list_sources(self) -> list[str]:
        """Return a list of registered source names."""
        return list(self._sources.keys())
