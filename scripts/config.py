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
    path: str = "data/hageglede.db"
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
        if 'log_level' in data:
            self.config.log_level = data['log_level']
        if 'cache_dir' in data:
            self.config.cache_dir = data['cache_dir']
        if 'max_workers' in data:
            self.config.max_workers = data['max_workers']
        if 'batch_size' in data:
            self.config.batch_size = data['batch_size']
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Database settings
        db_path = os.getenv('DATABASE_PATH')
        if db_path:
            self.config.database.path = db_path
        
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
        log_level = os.getenv('LOG_LEVEL')
        if log_level:
            self.config.log_level = log_level
        
        cache_dir = os.getenv('CACHE_DIR')
        if cache_dir:
            self.config.cache_dir = cache_dir
        
        max_workers = os.getenv('MAX_WORKERS')
        if max_workers:
            self.config.max_workers = int(max_workers)
        
        batch_size = os.getenv('BATCH_SIZE')
        if batch_size:
            self.config.batch_size = int(batch_size)
    
    def save(self, path: str):
        """Save current configuration to file."""
        data = {
            'database': {
                'path': self.config.database.path,
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
            'batch_size': self.config.batch_size
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


# Backward-compatible module-level exports for pipeline.py and other imports

# Database configuration
DATABASE_PATH = config.database.path

# Logging configuration (dictionary format for compatibility)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": config.log_level,
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": config.log_level,
            "propagate": True
        }
    }
}

# GBIF retry configuration (default values)
GBIF_RETRY_CONFIG = {
    "max_retries": 3,
    "backoff_factor": 1.0,
    "status_forcelist": [408, 429, 500, 502, 503, 504]
}

# Frost (MET) configuration
def get_frost_config():
    """Get FROST configuration from MET source if available."""
    met_source = _config_manager.get_source("MET")
    if met_source and met_source.url:
        return {
            "base_url": met_source.url,
            "client_id": met_source.params.get("client_id") if met_source.params else "",
            "client_secret": met_source.params.get("client_secret") if met_source.params else "",
            "auth": met_source.api_key,
            "timeout": met_source.timeout,
            "retries": met_source.retries
        }
    return {
        "base_url": "https://frost.met.no",
        "client_id": "",
        "client_secret": "",
        "auth": "",
        "timeout": 30,
        "retries": 3
    }

FROST_CONFIG = get_frost_config()

# MET client ID (legacy compatibility)
MET_CLIENT_ID = FROST_CONFIG.get("client_id", "")

# Directory configurations
CACHE_DIR = config.cache_dir
DATA_DIR = os.path.dirname(config.database.path) if config.database.path else "data"

# Additional constants for backward compatibility
MAX_WORKERS = config.max_workers
BATCH_SIZE = config.batch_size