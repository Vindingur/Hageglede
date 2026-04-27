"""
Fetcher for plant data from Artsdatabanken API.

Artsdatabanken (Norwegian Biodiversity Information Centre) provides data on
Norwegian species, including plants. This module fetches plant taxonomy,
distribution, and conservation status data.

API Documentation: https://api.artsdatabanken.no/
"""
import json
import logging
import time
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ArtsdatabankenFetcher:
    """Fetch plant data from Artsdatabanken API."""

    BASE_URL = "https://api.artsdatabanken.no"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Artsdatabanken fetcher.
        
        Args:
            api_key: Optional API key for authenticated requests.
                     Public endpoints may work without key.
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        
        # Common headers
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "Hageglede/1.0 Data Pipeline"
        })
    
    def get_plant_species(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch plant species data.
        
        Args:
            limit: Number of records to fetch per request
            offset: Starting offset for pagination
            
        Returns:
            List of plant species records
        """
        endpoint = f"{self.BASE_URL}/species"
        params = {
            "limit": limit,
            "offset": offset,
            "taxonRank": "Species",
            "kingdom": "Plantae"
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Fetched {len(data.get('items', []))} plant species from Artsdatabanken")
            return data.get("items", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching plant species: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:500]}")
            return []
    
    def get_species_details(self, taxon_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific species.
        
        Args:
            taxon_id: Artsdatabanken taxon ID
            
        Returns:
            Detailed species information or None if error
        """
        endpoint = f"{self.BASE_URL}/species/{taxon_id}"
        
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching species details for {taxon_id}: {e}")
            return None
    
    def search_plants(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for plants by name or other criteria.
        
        Args:
            query: Search query (scientific name, Norwegian name, etc.)
            limit: Maximum number of results
            
        Returns:
            List of matching plant records
        """
        endpoint = f"{self.BASE_URL}/search"
        params = {
            "q": query,
            "limit": limit,
            "kingdom": "Plantae"
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Found {len(data.get('items', []))} plants matching '{query}'")
            return data.get("items", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching plants: {e}")
            return []
    
    def get_conservation_status(self, taxon_id: str) -> Optional[Dict]:
        """
        Fetch conservation status for a species.
        
        Args:
            taxon_id: Artsdatabanken taxon ID
            
        Returns:
            Conservation status information or None
        """
        endpoint = f"{self.BASE_URL}/species/{taxon_id}/conservation"
        
        try:
            response = self.session.get(endpoint)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching conservation status for {taxon_id}: {e}")
            return None
    
    def fetch_all_plants(self, max_pages: int = 10) -> List[Dict]:
        """
        Fetch all available plant data with pagination.
        
        Args:
            max_pages: Maximum number of pages to fetch
            
        Returns:
            Combined list of all plant records
        """
        all_plants = []
        limit = 100
        offset = 0
        
        for page in range(max_pages):
            logger.info(f"Fetching page {page + 1} of plant data (offset: {offset})")
            
            plants = self.get_plant_species(limit=limit, offset=offset)
            if not plants:
                break
            
            all_plants.extend(plants)
            
            if len(plants) < limit:
                break
            
            offset += limit
            time.sleep(0.5)  # Be nice to the API
        
        logger.info(f"Total plants fetched: {len(all_plants)}")
        return all_plants


# PURPOSE: Fix pipeline import by providing ArtsdatabankenClient alias for ArtsdatabankenFetcher class
# CONSUMED BY: scripts/pipeline.py likely imports ArtsdatabankenClient from here
# DEPENDS ON: requests library for HTTP requests
ArtsdatabankenClient = ArtsdatabankenFetcher