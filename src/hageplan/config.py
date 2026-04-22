"""Configuration management for Hageglede."""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class ConfigManager:
    """Manages configuration loading, validation, and access."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ConfigManager.

        Args:
            config_path: Path to config file. If None, uses ~/.hageglede/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".hageglede" / "config.json"

        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Default configuration
        self.default_config = {
            "sources": {
                "open_meteo": {
                    "location": {"latitude": 59.9139, "longitude": 10.7522},
                    "units": {
                        "temperature": "celsius",
                        "windspeed": "kmh",
                        "precipitation": "mm",
                        "timeformat": "iso8601",
                        "timezone": "auto"
                    }
                },
                "pirate_weather": {
                    "location": {"latitude": 59.9139, "longitude": 10.7522},
                    "units": {
                        "temperature": "celsius",
                        "windspeed": "kmh",
                        "precipitation": "mm"
                    }
                }
            },
            "data_dir": str(Path.home() / ".hageglede" / "data"),
            "cache_dir": str(Path.home() / ".hageglede" / "cache"),
            "log_level": "INFO"
        }

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    file_config = json.load(f)
                config = self._merge_configs(self.default_config, file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}. Using defaults.")
                config = self.default_config.copy()
        else:
            config = self.default_config.copy()
            self._save_config(config)

        # Load sensitive values from environment variables
        config = self._load_from_env(config)
        return config

    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge default and override configs."""
        result = default.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _load_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load sensitive configuration from environment variables."""
        # API keys for data sources
        source_keys = {
            "pirate_weather": "PIRATE_WEATHER_API_KEY",
            "open_meteo": "OPEN_METEO_API_KEY",
        }

        for source_name, env_var in source_keys.items():
            if source_name in config.get("sources", {}):
                api_key = os.getenv(env_var)
                if api_key:
                    config["sources"][source_name]["api_key"] = api_key
                else:
                    print(f"Warning: Environment variable {env_var} not set for {source_name}")

        return config

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            # Don't save API keys to file
            safe_config = config.copy()
            if "sources" in safe_config:
                for source_config in safe_config["sources"].values():
                    if "api_key" in source_config:
                        del source_config["api_key"]

            with open(self.config_path, "w") as f:
                json.dump(safe_config, f, indent=2)
        except IOError as e:
            print(f"Error saving config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a configuration value."""
        keys = key.split(".")
        config = self.config

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

        if save:
            self._save_config(self.config)

    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()


class PipelineConfig:
    """Configuration for the data pipeline."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize PipelineConfig.

        Args:
            config_manager: Optional ConfigManager instance. If None, creates one.
        """
        if config_manager is None:
            config_manager = ConfigManager()
        self.config_manager = config_manager

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return Path(self.config_manager.get("data_dir", Path.home() / ".hageglede" / "data"))

    @property
    def cache_dir(self) -> Path:
        """Get cache directory path."""
        return Path(self.config_manager.get("cache_dir", Path.home() / ".hageglede" / "cache"))

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.config_manager.get("log_level", "INFO")

    @property
    def sources(self) -> List[str]:
        """Get list of enabled data sources."""
        sources_config = self.config_manager.get("sources", {})
        return list(sources_config.keys())

    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        """Get configuration for a specific data source."""
        return self.config_manager.get(f"sources.{source_name}", {})

    def get_api_key(self, source_name: str) -> Optional[str]:
        """Get API key for a data source."""
        source_config = self.get_source_config(source_name)
        return source_config.get("api_key")


# Module-level constants for easy import
MET_CLIENT_ID = os.getenv("MET_CLIENT_ID")
DATA_DIR = Path.home() / ".hageglede" / "data"
CACHE_DIR = Path.home() / ".hageglede" / "cache"

# Global config instance
_config_manager = ConfigManager()
pipeline_config = PipelineConfig(_config_manager)