# PURPOSE: Fetch plant data for ETL pipeline
# CONSUMED BY: pipeline.py
# DEPENDS ON: config.base

import json
import csv
import requests
from typing import List, Dict, Any, Optional
import logging
from scripts.config.base import get_config

logger = logging.getLogger(__name__)

def fetch_plant_data() -> List[Dict[str, Any]]:
    """
    Fetch plant data from the configured data source.
    
    Returns:
        List of plant records as dictionaries
    """
    config = get_config()
    data_source = config.get('data_source', {}).get('url')
    
    if not data_source:
        logger.warning("No data source URL configured, returning empty list")
        return []
    
    try:
        logger.info(f"Fetching plant data from {data_source}")
        response = requests.get(data_source, timeout=30)
        response.raise_for_status()
        
        # Try to parse as JSON first, then CSV
        content_type = response.headers.get('content-type', '')
        
        if 'application/json' in content_type:
            data = response.json()
            logger.info(f"Fetched {len(data) if isinstance(data, list) else 1} plant records")
            return data if isinstance(data, list) else [data]
        
        elif 'text/csv' in content_type or data_source.endswith('.csv'):
            # Parse CSV
            decoded_content = response.content.decode('utf-8')
            csv_reader = csv.DictReader(decoded_content.splitlines())
            data = list(csv_reader)
            logger.info(f"Fetched {len(data)} plant records from CSV")
            return data
        
        else:
            # Try to parse as JSON anyway
            try:
                data = response.json()
                logger.info(f"Fetched {len(data) if isinstance(data, list) else 1} plant records")
                return data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                logger.error(f"Unsupported content type: {content_type}")
                return []
                
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching plant data: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in fetch_plant_data: {e}")
        return []