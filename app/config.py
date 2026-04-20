from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Hageglede API"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # Database configuration
    database_url: str = "sqlite+aiosqlite:///./hageglede.db"
    
    # CORS configuration
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # API configuration
    api_prefix: str = "/api"
    api_version: str = "v1"
    
    # Security (minimal for MVP)
    session_secret_key: str = "dev-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()