#!/usr/bin/env python3
"""
GBIF API data fetcher for Norwegian plant occurrences.

Fetches plant occurrence records from GBIF for Norway.
"""

# PURPOSE: Fetches plant occurrence records from GBIF API for Norway with optional date filtering to limit data to relevant time periods
# CONSUMED BY: pipeline.py, any CLI or automated data fetch processes
# DEPENDS ON: requests library for HTTP calls, logging for monitoring, datetime handling

import time
import logging
import requests
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


GBIF_API_BASE = "https://api.gbif.org/v1"
DELAY_BETWEEN_REQUESTS = 0.5  # seconds


def fetch_norwegian_plant_occurrences(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    max_records: int = 10000
) -> List[Dict]:
    """
    Fetch plant occurrence records from GBIF for Norway.
    
    Parameters:
    -----------
    start_date : str, optional
        Start date for filtering occurrences (YYYY-MM-DD format)
    end_date : str, optional
        End date for filtering occurrences (YYYY-MM-DD format)
    max_records : int
        Maximum number of records to fetch (default: 10000)
    
    Returns:
    --------
    List[Dict]
        List of occurrence records, each as a dictionary
    """
    # Define search parameters
    params = {
        "country": "NO",  # Norway
        "basisOfRecord": "HUMAN_OBSERVATION",
        "limit": 300,  # Max per request
        "offset": 0,
    }
    
    # Add date filtering if provided
    if start_date or end_date:
        date_filter = ""
        if start_date:
            date_filter = start_date
        if end_date:
            if date_filter:  # If start_date was provided
                date_filter += f",{end_date}"
            else:
                date_filter = f",{end_date}"  # GBIF expects format ",end_date" for only end date
        params["occurrenceDate"] = date_filter
    
    all_occurrences = []
    total_fetched = 0
    
    try:
        while total_fetched < max_records:
            # Make request to GBIF API
            response = requests.get(
                f"{GBIF_API_BASE}/occurrence/search",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract occurrences
            occurrences = data.get("results", [])
            count = data.get("count", 0)
            end_of_records = data.get("endOfRecords", False)
            
            logger.info(
                f"Fetched {len(occurrences)} records "
                f"(offset {params['offset']}, total available: {count})"
            )
            
            # Filter for plants (kingdom Plantae)
            plant_occurrences = [
                occ for occ in occurrences
                if occ.get("kingdom") == "Plantae"
            ]
            
            all_occurrences.extend(plant_occurrences)
            total_fetched += len(plant_occurrences)
            
            # Check if we have enough records or reached the end
            if end_of_records or len(occurrences) == 0:
                logger.info("Reached end of available records")
                break
                
            if total_fetched >= max_records:
                logger.info(f"Reached maximum record limit ({max_records})")
                break
            
            # Update offset for next request
            params["offset"] += params["limit"]
            
            # Respect rate limits
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        logger.info(f"Total plant occurrences fetched: {len(all_occurrences)}")
        return all_occurrences
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from GBIF API: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def save_to_json(data: List[Dict], output_path: str = "gbif_occurrences.json"):
    """
    Save fetched data to a JSON file.
    
    Parameters:
    -----------
    data : List[Dict]
        Data to save
    output_path : str
        Path to output JSON file
    """
    import json
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Data saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    try:
        # Example with date filtering
        occurrences = fetch_norwegian_plant_occurrences(
            start_date="2020-01-01",
            end_date="2023-12-31",
            max_records=1000
        )
        save_to_json(occurrences)
    except Exception as e:
        logger.error(f"Failed to fetch GBIF data: {e}")
        raise