# PURPOSE: Configuration management for the Hageglede data pipeline with sensible defaults
# CONSUMED BY: scripts/pipeline.py, fetchers/plant_fetcher.py, loaders/weather_loader.py, loaders/plant_loader.py
# DEPENDS ON: os, pathlib, dataclasses, yaml, dotenv
# TEST: none

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    path: str = str(DATA_DIR / "hageglede.db")
    echo: bool = False
    pool_pre_ping: bool = True
    pool_recycle: int = 3600


@dataclass
class FetcherConfig:
    """Data fetcher configuration."""
    # API endpoints
    weather_api_url: str = "https://api.met.no"
    plant_api_url: str = "https://trefle.io/api/v1"
    
    # API keys (loaded from environment)
    weather_api_key: Optional[str] = field(default_factory=lambda: os.getenv("WEATHER_API_KEY"))
    plant_api_key: Optional[str] = field(default_factory=lambda: os.getenv("PLANT_API_KEY"))
    
    # Rate limiting
    rate_limit_delay: float = 1.0  # seconds between requests
    max_retries: int = 3
    timeout: int = 30  # seconds


@dataclass
class LoaderConfig:
    """Data loader configuration."""
    batch_size: int = 1000
    chunk_size: int = 10000
    max_workers: int = 4
    validation_enabled: bool = True
    skip_duplicates: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = field(default_factory=lambda: str(DATA_DIR / "hageglede.log") if DATA_DIR.exists() else None)
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class DataPaths:
    """Paths to data files."""
    weather_csv: str = field(default_factory=lambda: str(DATA_DIR / "weather.csv"))
    plants_csv: str = field(default_factory=lambda: str(DATA_DIR / "plants.csv"))
    raw_data_dir: str = field(default_factory=lambda: str(DATA_DIR / "raw"))
    processed_data_dir: str = field(default_factory=lambda: str(DATA_DIR / "processed"))
    
    def ensure_directories(self) -> None:
        """Create all necessary data directories."""
        for path_str in [self.raw_data_dir, self.processed_data_dir]:
            Path(path_str).mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    """Main application configuration."""
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # Components
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)
    loader: LoaderConfig = field(default_factory=LoaderConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    paths: DataPaths = field(default_factory=DataPaths)
    
    # Feature flags
    enable_weather_fetching: bool = True
    enable_plant_fetching: bool = True
    enable_data_validation: bool = True
    
    def load_yaml(self, yaml_path: str) -> None:
        """Load configuration from a YAML file and update this config object."""
        yaml_path_obj = Path(yaml_path)
        if not yaml_path_obj.exists():
            raise FileNotFoundError(f"Config YAML not found: {yaml_path}")
        
        with open(yaml_path_obj, 'r') as f:
            yaml_config = yaml.safe_load(f)
        
        # TODO: Implement recursive update of dataclass fields from YAML
        # This is a placeholder for future enhancement
        print(f"Warning: YAML config loading not fully implemented. File: {yaml_path}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "database": {
                "path": self.database.path,
                "echo": self.database.echo,
                "pool_pre_ping": self.database.pool_pre_ping,
                "pool_recycle": self.database.pool_recycle,
            },
            "fetcher": {
                "weather_api_url": self.fetcher.weather_api_url,
                "plant_api_url": self.fetcher.plant_api_url,
                "weather_api_key": self.fetcher.weather_api_key,
                "plant_api_key": self.fetcher.plant_api_key,
                "rate_limit_delay": self.fetcher.rate_limit_delay,
                "max_retries": self.fetcher.max_retries,
                "timeout": self.fetcher.timeout,
            },
            "loader": {
                "batch_size": self.loader.batch_size,
                "chunk_size": self.loader.chunk_size,
                "max_workers": self.loader.max_workers,
                "validation_enabled": self.loader.validation_enabled,
                "skip_duplicates": self.loader.skip_duplicates,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file_path": self.logging.file_path,
                "max_bytes": self.logging.max_bytes,
                "backup_count": self.logging.backup_count,
            },
            "paths": {
                "weather_csv": self.paths.weather_csv,
                "plants_csv": self.paths.plants_csv,
                "raw_data_dir": self.paths.raw_data_dir,
                "processed_data_dir": self.paths.processed_data_dir,
            },
            "feature_flags": {
                "enable_weather_fetching": self.enable_weather_fetching,
                "enable_plant_fetching": self.enable_plant_fetching,
                "enable_data_validation": self.enable_data_validation,
            }
        }


# Global configuration instance
config = AppConfig()

# Ensure data directories exist on import
config.paths.ensure_directories()