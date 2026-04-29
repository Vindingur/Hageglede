# PURPOSE: Configuration management for the Hageglede data pipeline with sensible defaults
# CONSUMED BY: scripts/pipeline.py, fetchers/plant_fetcher.py, loaders/weather_loader.py, loaders/plant_loader.py
# DEPENDS ON: none
# TEST: none

"""
Configuration management for the Hageglede data pipeline.
Handles API keys, database paths, source URLs, and rate limits.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

import yaml
import dotenv


class SourceType(Enum):
    """Supported data source types."""
    SIV = "siv"
    WIKIDATA = "wikidata"
    OPENSTREETMAP = "openstreetmap"
    GEOJSON = "geojson"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    path: str = "hageglede.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class SourceConfig:
    """Configuration for a single data source."""
    name: str
    source_type: SourceType
    url: Optional[str] = None
    api_key: Optional[str] = None
    rate_limit: float = 1.0  # requests per second
    timeout: int = 30
    retries: int = 3
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Main pipeline configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    sources: List[SourceConfig] = field(default_factory=list)
    log_level: str = "INFO"
    cache_dir: str = "data/cache"
    max_workers: int = 4
    batch_size: int = 1000
    data_dir: str = "data"


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, loads from default locations.
        """
        self.config_path = config_path
        self.config = PipelineConfig()
        
        # Default sources
        self.config.sources = [
            SourceConfig(
                name="SIV",
                source_type=SourceType.SIV,
                url="https://transport.infra.digitaltjeneste.no/siv/api/v1/",
                rate_limit=0.5
            ),
            SourceConfig(
                name="Wikidata",
                source_type=SourceType.WIKIDATA,
                url="https://www.wikidata.org/w/api.php",
                rate_limit=2.0
            ),
            SourceConfig(
                name="OpenStreetMap",
                source_type=SourceType.OPENSTREETMAP,
                url="https://overpass-api.de/api/interpreter",
                rate_limit=1.0
            ),
            SourceConfig(
                name="MET",
                source_type=SourceType.SIV,
                url="https://frost.met.no",
                rate_limit=1.0
            )
        ]
        
    def load(self) -> PipelineConfig:
        """Load configuration from file or environment."""
        # Load environment variables
        dotenv.load_dotenv()
        
        # Try to load from config file if specified
        if self.config_path and Path(self.config_path).exists():
            self._load_from_file(self.config_path)
        
        # Override from environment variables
        self._load_from_env()
        
        # Ensure sensible defaults
        if not self.config.data_dir:
            self.config.data_dir = "data"
        
        # Ensure database path is relative to project root if not absolute
        if not Path(self.config.database.path).is_absolute():
            # Make it relative to project root (where config is in scripts/)
            scripts_dir = Path(__file__).parent
            project_root = scripts_dir.parent
            self.config.database.path = str(project_root / self.config.database.path)
        
        return self.config
    
    def _load_from_file(self, path: str):
        """Load configuration from YAML or JSON file."""
        path_obj = Path(path)
        
        if path_obj.suffix in ['.yaml', '.yml']:
            with open(path_obj, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        elif path_obj.suffix == '.json':
            with open(path_obj, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path_obj.suffix}")
        
        # Update database config
        if 'database' in data:
            db_data = data['database']
            self.config.database = DatabaseConfig(
                path=db_data.get('path', self.config.database.path),
                echo=db_data.get('echo', self.config.database.echo),
                pool_size=db_data.get('pool_size', self.config.database.pool_size),
                max_overflow=db_data.get('max_overflow', self.config.database.max_overflow)
            )
        
        # Update sources
        if 'sources' in data:
            sources_data = data['sources']
            self.config.sources = []
            for src_data in sources_data:
                source = SourceConfig(
                    name=src_data['name'],
                    source_type=SourceType(src_data['source_type']),
                    url=src_data.get('url'),
                    api_key=src_data.get('api_key'),
                    rate_limit=src_data.get('rate_limit', 1.0),
                    timeout=src_data.get('timeout', 30),
                    retries=src_data.get('retries', 3),
                    enabled=src_data.get('enabled', True),
                    params=src_data.get('params', {})
                )
                self.config.sources.append(source)
        
        # Update pipeline settings
        for key in ['log_level', 'cache_dir', 'max_workers', 'batch_size', 'data_dir']:
            if key in data:
                setattr(self.config, key, data[key])
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Database settings
        db_path = os.getenv('DATABASE_PATH')
        if db_path:
            self.config.database.path = db_path
        
        # Data directory
        data_dir = os.getenv('DATA_DIR')
        if data_dir:
            self.config.data_dir = data_dir
        
        # API keys
        for source in self.config.sources:
            env_key = f"{source.name.upper()}_API_KEY"
            api_key = os.getenv(env_key)
            if api_key:
                source.api_key = api_key
        
        # MET client ID and secret
        met_client_id = os.getenv('MET_CLIENT_ID')
        met_client_secret = os.getenv('MET_CLIENT_SECRET')
        
        if met_client_id and met_client_secret:
            # Set MET credentials as a composite API key or parameters
            met_source = self.get_source("MET")
            if met_source:
                met_source.params = {
                    "client_id": met_client_id,
                    "client_secret": met_client_secret
                }
                # For OAuth2 flow, we might need both ID and secret
                # Use a special format for authentication
                met_source.api_key = f"{met_client_id}:{met_client_secret}"
        
        # Pipeline settings
        for env_var, attr in [('LOG_LEVEL', 'log_level'), ('CACHE_DIR', 'cache_dir'), 
                             ('DATA_DIR', 'data_dir')]:
            value = os.getenv(env_var)
            if value:
                setattr(self.config, attr, value)
        
        max_workers = os.getenv('MAX_WORKERS')
        if max_workers:
            self.config.max_workers = int(max_workers)
        
        batch_size = os.getenv('BATCH_SIZE')
        if batch_size:
            self.config.batch_size = int(batch_size)
    
    def save(self, path: str):
        """Save current configuration to file."""
        # Convert paths to relative for storage
        db_path_relative = self.config.database.path
        if Path(db_path_relative).is_absolute():
            scripts_dir = Path(__file__).parent
            project_root = scripts_dir.parent
            try:
                db_path_relative = str(Path(db_path_relative).relative_to(project_root))
            except ValueError:
                # Path is not relative to project, keep as is
                pass
                
        data = {
            'database': {
                'path': db_path_relative,
                'echo': self.config.database.echo,
                'pool_size': self.config.database.pool_size,
                'max_overflow': self.config.database.max_overflow
            },
            'sources': [
                {
                    'name': source.name,
                    'source_type': source.source_type.value,
                    'url': source.url,
                    'api_key': source.api_key,
                    'rate_limit': source.rate_limit,
                    'timeout': source.timeout,
                    'retries': source.retries,
                    'enabled': source.enabled,
                    'params': source.params
                }
                for source in self.config.sources
            ],
            'log_level': self.config.log_level,
            'cache_dir': self.config.cache_dir,
            'max_workers': self.config.max_workers,
            'batch_size': self.config.batch_size,
            'data_dir': self.config.data_dir
        }
        
        path_obj = Path(path)
        
        if path_obj.suffix in ['.yaml', '.yml']:
            with open(path_obj, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False)
        elif path_obj.suffix == '.json':
            with open(path_obj, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported config file format: {path_obj.suffix}")
    
    def get_source(self, name: str) -> Optional[SourceConfig]:
        """Get configuration for a specific source."""
        for source in self.config.sources:
            if source.name.lower() == name.lower():
                return source
        return None


def get_source(name: str) -> Optional[SourceConfig]:
    """Module-level wrapper for ConfigManager.get_source method.
    
    This function is imported by met.py to get source configuration.
    It delegates to the global ConfigManager instance.
    
    Args:
        name: Name of the source to retrieve.
        
    Returns:
        SourceConfig object or None if not found.
    """
    return _config_manager.get_source(name)


# Global configuration instance
_config_manager = ConfigManager()
config = _config_manager.load()


def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file.
        
    Returns:
        PipelineConfig object.
    """
    manager = ConfigManager(config_path)
    return manager.load()


# Backward-compatible module-level exports for pipeline.py
DATABASE_PATH = config.database.path
DATA_DIR = config.data_dir

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard"
        }
    },
    "root": {
        "handlers": ["console"],
        "level": config.log_level
    }
}

# GBIF retry configuration
GBIF_RETRY_CONFIG = {
    "retries": 3,
    "backoff_factor": 2,
    "status_forcelist": [429, 500, 502, 503, 504],
    "allowed_methods": ["GET"]
}

# FROST API configuration
FROST_CONFIG = {
    "base_url": "https://frost.met.no",
    "timeout": 30
}

# MET client ID from environment
MET_CLIENT_ID = os.getenv('MET_CLIENT_ID', '')

# Directory paths
CACHE_DIR = config.cache_dir