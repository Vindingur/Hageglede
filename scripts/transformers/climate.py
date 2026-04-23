#!/usr/bin/env python3
"""
Climate data transformer for weather sources.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def transform_met_observations(data: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    """Transform MET API observations into standardized format."""
    transformed = []
    
    try:
        observations = data.get('data', {}).get('tseries', [])
        
        for obs in observations:
            time = obs.get('time')
            value = obs.get('observations', [{}])[0].get('value')
            
            if time and value is not None:
                transformed.append({
                    'source': 'MET',
                    'location': location,
                    'timestamp': time,
                    'temperature_c': float(value),
                    'collected_at': datetime.utcnow().isoformat()
                })
                
    except Exception as e:
        logger.error(f"Failed to transform MET observations: {e}")
        
    return transformed


def transform_nasa_power(data: Dict[str, Any], location: str) -> List[Dict[str, Any]]:
    """Transform NASA POWER API data into standardized format."""
    transformed = []
    
    try:
        properties = data.get('properties', {}).get('parameter', {})
        dates = properties.get('T2M', {}).keys()
        
        for date in dates:
            temp = properties.get('T2M', {}).get(date)
            
            if temp is not None:
                transformed.append({
                    'source': 'NASA_POWER',
                    'location': location,
                    'timestamp': f"{date}T00:00:00Z",
                    'temperature_c': float(temp),
                    'collected_at': datetime.utcnow().isoformat()
                })
                
    except Exception as e:
        logger.error(f"Failed to transform NASA POWER data: {e}")
        
    return transformed


def transform_weather(data: Dict[str, Any], source: str, location: str) -> List[Dict[str, Any]]:
    """
    Transform weather data from various sources into standardized format.
    
    Args:
        data: Raw API response data
        source: Source identifier ('MET', 'NASA_POWER', etc.)
        location: Location identifier
        
    Returns:
        List of standardized weather observation records
    """
    if source.upper() == 'MET':
        return transform_met_observations(data, location)
    elif source.upper() == 'NASA_POWER':
        return transform_nasa_power(data, location)
    else:
        logger.warning(f"Unknown weather source: {source}")
        return []
