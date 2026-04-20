"""
Abstract base class for data fetchers in the Hageglede pipeline.

This module defines the BaseFetcher abstract class that all data fetchers
must implement. It provides a consistent interface for fetching data from
various sources.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime
import logging

# Type variable for the data being fetched
T = TypeVar('T')

logger = logging.getLogger(__name__)


@dataclass
class FetchResult(Generic[T]):
    """Result container for fetch operations."""
    
    data: T
    """The fetched data."""
    
    metadata: Dict[str, Any]
    """Metadata about the fetch operation."""
    
    timestamp: datetime
    """When the data was fetched."""
    
    source: str
    """The data source identifier."""
    
    success: bool = True
    """Whether the fetch was successful."""
    
    error_message: Optional[str] = None
    """Error message if fetch failed."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'success': self.success,
            'error_message': self.error_message
        }


@dataclass  
class FetchConfig:
    """Configuration for fetch operations."""
    
    url: Optional[str] = None
    """URL to fetch data from."""
    
    api_key: Optional[str] = None
    """API key for authenticated sources."""
    
    params: Optional[Dict[str, Any]] = None
    """Query parameters for the request."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    retry_attempts: int = 3
    """Number of retry attempts on failure."""
    
    retry_delay: int = 5
    """Delay between retries in seconds."""
    
    cache_duration: Optional[int] = None
    """Cache duration in seconds (None for no caching)."""


class BaseFetcher(ABC, Generic[T]):
    """
    Abstract base class for data fetchers.
    
    All data fetchers in the Hageglede pipeline must inherit from this class
    and implement the abstract methods.
    
    Attributes:
        source_name (str): Unique identifier for the data source.
        config (FetchConfig): Configuration for fetch operations.
    """
    
    def __init__(self, source_name: str, config: Optional[FetchConfig] = None):
        """
        Initialize the fetcher.
        
        Args:
            source_name: Unique identifier for the data source.
            config: Optional configuration for fetch operations.
        """
        self.source_name = source_name
        self.config = config or FetchConfig()
        self._logger = logging.getLogger(f"{__name__}.{self.source_name}")
    
    @abstractmethod
    async def fetch(self) -> FetchResult[T]:
        """
        Fetch data from the source.
        
        This is the main method that all concrete fetchers must implement.
        It should handle all aspects of fetching data including error handling,
        retries, and formatting the result.
        
        Returns:
            FetchResult containing the fetched data and metadata.
            
        Raises:
            FetchError: If the fetch operation fails after all retries.
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the fetcher configuration.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        pass
    
    def get_source_info(self) -> Dict[str, Any]:
        """
        Get information about the data source.
        
        Returns:
            Dictionary with source information.
        """
        return {
            'source_name': self.source_name,
            'config': self.config.__dict__,
            'class_name': self.__class__.__name__
        }
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the data source.
        
        Returns:
            True if the source is accessible, False otherwise.
        """
        try:
            # Try a simple fetch or ping operation
            result = await self.fetch()
            return result.success
        except Exception as e:
            self._logger.error(f"Health check failed for {self.source_name}: {e}")
            return False


class FetchError(Exception):
    """Exception raised when a fetch operation fails."""
    
    def __init__(self, source: str, message: str, status_code: Optional[int] = None):
        self.source = source
        self.message = message
        self.status_code = status_code
        super().__init__(f"Fetch failed for {source}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'source': self.source,
            'message': self.message,
            'status_code': self.status_code,
            'type': self.__class__.__name__
        }