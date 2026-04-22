from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum
from typing import List
from pydantic import BaseModel


class SourceType(str, Enum):
    API = "api"
    DATABASE = "database"
    FILE = "file"


class SourceConfig(BaseModel):
    name: str
    type: SourceType
    env_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./hageglede.db"
    
    # API
    debug: bool = False
    title: str = "Hageglede API"
    version: str = "1.0.0"
    
    # Security
    cors_origins: list[str] = ["*"]
    
    # Data sources configuration
    default_sources: List[SourceConfig] = [
        SourceConfig(
            name="GBIF",
            type=SourceType.API,
            env_key="GBIF_USERNAME",
            api_secret="GBIF_PASSWORD",
            base_url="https://api.gbif.org/v1",
            description="Global Biodiversity Information Facility API"
        ),
        SourceConfig(
            name="Artsdatabanken",
            type=SourceType.API,
            env_key="ARTSDATABANKEN_API_KEY",
            base_url="https://api.artsdatabanken.no",
            description="Artsdatabanken species data API"
        ),
        SourceConfig(
            name="MET",
            type=SourceType.API,
            env_key="MET_CLIENT_ID",
            api_secret="MET_CLIENT_SECRET",
            base_url="https://frost.met.no",
            description="Norwegian Meteorological Institute API"
        )
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


def get_source(name: str) -> Optional[SourceConfig]:
    """Get source configuration by name."""
    for source in settings.default_sources:
        if source.name == name:
            return source
    return None