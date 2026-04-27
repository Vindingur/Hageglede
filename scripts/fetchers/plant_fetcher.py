# PURPOSE: Clean wrapper/interface for GBIF and Artsbanken plant fetchers
# CONSUMED BY: pipeline.py, possibly other scripts
# DEPENDS ON: scripts/fetchers/gbif.py, scripts/fetchers/artsbanken.py

"""
Plant Fetcher Interface

Provides a clean abstraction over the GBIF and Artsbanken APIs.
Returns standardized plant data structures.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from . import gbif
from . import artsbanken

# Module-level logger
logger = logging.getLogger(__name__)


def fetch_gbif_plants(scientific_names: List[str], limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch plant data from GBIF for given scientific names.
    
    Args:
        scientific_names: List of scientific names to search for
        limit: Maximum number of results per name
        
    Returns:
        List of plant records from GBIF
    """
    logger.info(f"Fetching GBIF data for {len(scientific_names)} plant names")
    
    all_results = []
    for name in scientific_names:
        try:
            results = gbif.fetch_occurrences(name, limit=limit)
            if results:
                all_results.extend(results)
                logger.debug(f"Found {len(results)} GBIF occurrences for {name}")
        except Exception as e:
            logger.error(f"Error fetching GBIF data for {name}: {e}")
    
    logger.info(f"Retrieved {len(all_results)} total GBIF occurrences")
    return all_results


def fetch_artsbanken_plants(scientific_names: List[str], limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch plant data from Artsbanken for given scientific names.
    
    Args:
        scientific_names: List of scientific names to search for
        limit: Maximum number of results per name
        
    Returns:
        List of plant records from Artsbanken
    """
    logger.info(f"Fetching Artsbanken data for {len(scientific_names)} plant names")
    
    all_results = []
    for name in scientific_names:
        try:
            results = artsbanken.search_species(name, limit=limit)
            if results:
                all_results.extend(results)
                logger.debug(f"Found {len(results)} Artsbanken records for {name}")
        except Exception as e:
            logger.error(f"Error fetching Artsbanken data for {name}: {e}")
    
    logger.info(f"Retrieved {len(all_results)} total Artsbanken records")
    return all_results


def fetch_all_plants(scientific_names: List[str], limit_per_source: int = 100) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch plant data from both GBIF and Artsbanken.
    
    Args:
        scientific_names: List of scientific names to search for
        limit_per_source: Maximum number of results per name per source
        
    Returns:
        Dictionary with 'gbif' and 'artsbanken' keys containing lists of records
    """
    logger.info(f"Fetching all plant data for {len(scientific_names)} names")
    
    results = {
        'gbif': fetch_gbif_plants(scientific_names, limit=limit_per_source),
        'artsbanken': fetch_artsbanken_plants(scientific_names, limit=limit_per_source)
    }
    
    total_records = len(results['gbif']) + len(results['artsbanken'])
    logger.info(f"Total plant records fetched: {total_records}")
    
    return results


def standardize_plant_record(record: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Standardize a plant record from any source to a common format.
    
    Args:
        record: Raw record from GBIF or Artsbanken
        source: Source identifier ('gbif' or 'artsbanken')
        
    Returns:
        Standardized plant record
    """
    standardized = {
        'source': source,
        'raw_record': record,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if source == 'gbif':
        # Extract key fields from GBIF record
        standardized.update({
            'scientific_name': record.get('scientificName', ''),
            'latitude': record.get('decimalLatitude'),
            'longitude': record.get('decimalLongitude'),
            'country': record.get('country', ''),
            'year': record.get('year'),
            'month': record.get('month'),
            'day': record.get('day'),
            'dataset_name': record.get('datasetName', ''),
            'gbif_id': record.get('key')
        })
    elif source == 'artsbanken':
        # Extract key fields from Artsbanken record
        standardized.update({
            'scientific_name': record.get('scientificName', record.get('name', '')),
            'latitude': record.get('latitude'),
            'longitude': record.get('longitude'),
            'country': record.get('country', ''),
            'year': record.get('year'),
            'month': record.get('month'),
            'day': record.get('day'),
            'dataset_name': record.get('dataset', ''),
            'artsbanken_id': record.get('id')
        })
    
    return standardized


def get_plant_fetcher(source: str):
    """
    Get the appropriate fetcher module for a given source.
    
    Args:
        source: Source identifier ('gbif' or 'artsbanken')
        
    Returns:
        The fetcher module
    """
    if source == 'gbif':
        return gbif
    elif source == 'artsbanken':
        return artsbanken
    else:
        raise ValueError(f"Unknown source: {source}. Must be 'gbif' or 'artsbanken'.")


# Export the main functions
__all__ = [
    'fetch_gbif_plants',
    'fetch_artsbanken_plants',
    'fetch_all_plants',
    'standardize_plant_record',
    'get_plant_fetcher'
]