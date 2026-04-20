"""
Abstract base class for data fetchers.

This module defines the BaseFetcher abstract base class that all data fetchers
must implement. It provides a common interface for fetching data from various
sources.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Abstract base class for data fetchers.
    
    All data fetchers must inherit from this class and implement the fetch() method.
    This ensures a consistent interface for data acquisition across different
    data sources.
    
    Attributes:
        name: Human-readable name of the fetcher
        source: String identifier for the data source
    """
    
    def __init__(self, name: str, source: str):
        """Initialize the fetcher.
        
        Args:
            name: Human-readable name of the fetcher
            source: String identifier for the data source
        """
        self.name = name
        self.source = source
        logger.debug(f"Initialized {self.__class__.__name__}: {name} for source {source}")
    
    @abstractmethod
    def fetch(self, **kwargs) -> Dict[str, Any]:
        """Fetch data from the source.
        
        This is the main method that all fetchers must implement. It should
        handle data retrieval, error handling, and return the data in a
        standardized format.
        
        Args:
            **kwargs: Fetcher-specific parameters (e.g., location, date range, filters)
            
        Returns:
            A dictionary containing the fetched data. The structure should be
            consistent for similar data types:
            - 'data': The actual data (list, dict, or other structure)
            - 'metadata': Information about the fetch operation
            - 'status': Status of the fetch ('success', 'partial', 'error')
            - 'error': Error message if status is 'error'
            
        Raises:
            Fetcher-specific exceptions for unrecoverable errors
        """
        pass
    
    def __repr__(self) -> str:
        """Return a string representation of the fetcher."""
        return f"{self.__class__.__name__}(name='{self.name}', source='{self.source}')"
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.name} fetcher for {self.source}"