"""GBIF data fetcher for plant occurrences and species information."""

import asyncio
import requests
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)


class GBIFClient:
    """Client for interacting with GBIF API."""
    
    BASE_URL = "https://api.gbif.org/v1"
    
    def __init__(self, timeout: int = 30):
        """Initialize GBIF client.
        
        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()
        
    def search_species(self, query: str, limit: int = 100) -> List[Dict]:
        """Search for species by name.
        
        Args:
            query: Scientific or vernacular name to search for.
            limit: Maximum number of results.
            
        Returns:
            List of species records.
        """
        url = f"{self.BASE_URL}/species/search"
        params = {
            "q": query,
            "limit": limit,
            "datasetKey": "d7dddbf4-2cf0-4f39-9b2a-bb099caae36c"  # Backbone taxonomy
        }
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for result in data.get("results", []):
                species_data = {
                    "gbif_key": result.get("key"),
                    "scientific_name": result.get("scientificName"),
                    "canonical_name": result.get("canonicalName"),
                    "kingdom": result.get("kingdom"),
                    "phylum": result.get("phylum"),
                    "class": result.get("class"),
                    "order": result.get("order"),
                    "family": result.get("family"),
                    "genus": result.get("genus"),
                    "species": result.get("species"),
                    "taxon_rank": result.get("rank"),
                    "vernacular_names": result.get("vernacularNames", []),
                    "taxonomic_status": result.get("taxonomicStatus"),
                    "accepted_key": result.get("acceptedKey"),
                }
                results.append(species_data)
                
            logger.info(f"Found {len(results)} species for query: {query}")
            return results
            
        except requests.RequestException as e:
            logger.error(f"Error searching GBIF species: {e}")
            return []
            
    def get_occurrences(self, taxon_key: int, country: str = "NO", limit: int = 500) -> List[Dict]:
        """Get occurrence records for a taxon.
        
        Args:
            taxon_key: GBIF taxon key.
            country: ISO country code (default: NO for Norway).
            limit: Maximum number of occurrences.
            
        Returns:
            List of occurrence records.
        """
        url = f"{self.BASE_URL}/occurrence/search"
        params = {
            "taxonKey": taxon_key,
            "country": country,
            "limit": limit,
            "hasCoordinate": "true",
            "hasGeospatialIssue": "false",
            "basisOfRecord": "PRESERVED_SPECIMEN,HUMAN_OBSERVATION"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            occurrences = []
            for occurrence in data.get("results", []):
                occ_data = {
                    "gbif_id": occurrence.get("key"),
                    "species_key": occurrence.get("speciesKey"),
                    "scientific_name": occurrence.get("scientificName"),
                    "decimal_latitude": occurrence.get("decimalLatitude"),
                    "decimal_longitude": occurrence.get("decimalLongitude"),
                    "country": occurrence.get("country"),
                    "county": occurrence.get("county"),
                    "locality": occurrence.get("locality"),
                    "event_date": occurrence.get("eventDate"),
                    "year": occurrence.get("year"),
                    "month": occurrence.get("month"),
                    "day": occurrence.get("day"),
                    "basis_of_record": occurrence.get("basisOfRecord"),
                    "dataset_name": occurrence.get("datasetName"),
                    "recorded_by": occurrence.get("recordedBy"),
                    "coordinate_uncertainty_m": occurrence.get("coordinateUncertaintyInMeters"),
                    "elevation_m": occurrence.get("elevation"),
                }
                occurrences.append(occ_data)
                
            logger.info(f"Found {len(occurrences)} occurrences for taxon key {taxon_key}")
            return occurrences
            
        except requests.RequestException as e:
            logger.error(f"Error fetching GBIF occurrences: {e}")
            return []
            
    def get_species_details(self, taxon_key: int) -> Optional[Dict]:
        """Get detailed information for a specific species.
        
        Args:
            taxon_key: GBIF taxon key.
            
        Returns:
            Species details dictionary or None if not found.
        """
        url = f"{self.BASE_URL}/species/{taxon_key}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            details = {
                "gbif_key": data.get("key"),
                "scientific_name": data.get("scientificName"),
                "canonical_name": data.get("canonicalName"),
                "kingdom": data.get("kingdom"),
                "phylum": data.get("phylum"),
                "class": data.get("class"),
                "order": data.get("order"),
                "family": data.get("family"),
                "genus": data.get("genus"),
                "species": data.get("species"),
                "taxon_rank": data.get("rank"),
                "taxonomic_status": data.get("taxonomicStatus"),
                "nomenclatural_status": data.get("nomenclaturalStatus"),
                "accepted_key": data.get("acceptedKey"),
                "parent_key": data.get("parentKey"),
                "descriptions": data.get("descriptions", []),
                "vernacular_names": data.get("vernacularNames", []),
                "distribution": data.get("distributions", []),
                "habitats": data.get("habitats", []),
            }
            
            logger.info(f"Retrieved details for species {data.get('canonicalName')}")
            return details
            
        except requests.RequestException as e:
            logger.error(f"Error fetching species details for key {taxon_key}: {e}")
            return None


class GbifFetcher:
    """Async wrapper for GBIF API operations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the GBIF fetcher.
        
        Args:
            config: Configuration dictionary (currently unused but kept for compatibility).
        """
        self.config = config or {}
        self.client = GBIFClient()
    
    async def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for species by name.
        
        Args:
            query: Scientific or vernacular name to search for.
            limit: Maximum number of results.
            
        Returns:
            List of dicts with keys 'scientific_name', 'canonical_name', 'rank'.
        """
        # Run the synchronous client method in a thread pool
        raw_results = await asyncio.to_thread(self.client.search_species, query, limit)
        
        # Transform to required format
        results = []
        for result in raw_results:
            transformed = {
                'scientific_name': result.get('scientific_name'),
                'canonical_name': result.get('canonical_name'),
                'rank': result.get('taxon_rank')
            }
            results.append(transformed)
        
        return results
    
    async def fetch_occurrences(self, taxon_key: int) -> pd.DataFrame:
        """Fetch occurrence records for a taxon.
        
        Args:
            taxon_key: GBIF taxon key.
            
        Returns:
            DataFrame with occurrence data.
        """
        # Run the synchronous client method in a thread pool
        raw_occurrences = await asyncio.to_thread(
            self.client.get_occurrences, 
            taxon_key, 
            "NO",  # Norway
            500     # Default limit
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_occurrences) if raw_occurrences else pd.DataFrame()
        return df


def fetch_norwegian_plant_occurrences(plant_names: List[str], max_occurrences_per_species: int = 200) -> pd.DataFrame:
    """Fetch occurrence data for Norwegian plants from GBIF.
    
    Args:
        plant_names: List of plant scientific names to search for.
        max_occurrences_per_species: Maximum occurrences per species to fetch.
        
    Returns:
        DataFrame with occurrence data.
    """
    client = GBIFClient()
    all_occurrences = []
    all_species = []
    
    for plant_name in plant_names:
        logger.info(f"Processing {plant_name}...")
        
        # Search for species
        species_results = client.search_species(plant_name)
        
        for species in species_results:
            species_key = species.get("gbif_key")
            if not species_key:
                continue
                
            all_species.append(species)
            
            # Get occurrences
            occurrences = client.get_occurrences(
                taxon_key=species_key,
                country="NO",
                limit=max_occurrences_per_species
            )
            
            for occ in occurrences:
                occ["source_species_name"] = plant_name
                occ["matched_species_key"] = species_key
                
            all_occurrences.extend(occurrences)
            
        # Rate limiting
        time.sleep(0.5)
    
    # Convert to DataFrames
    species_df = pd.DataFrame(all_species) if all_species else pd.DataFrame()
    occurrences_df = pd.DataFrame(all_occurrences) if all_occurrences else pd.DataFrame()
    
    return species_df, occurrences_df


if __name__ == "__main__":
    # Example usage
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with some common Norwegian plants
    test_plants = [
        "Picea abies",  # Norway spruce
        "Betula pubescens",  # Downy birch
        "Vaccinium myrtillus",  # European blueberry
    ]
    
    species_df, occurrences_df = fetch_norwegian_plant_occurrences(test_plants, max_occurrences_per_species=50)
    
    print(f"Found {len(species_df)} species")
    print(f"Found {len(occurrences_df)} occurrences")
    
    if not species_df.empty:
        print("\nSample species:")
        print(species_df[["scientific_name", "family", "kingdom"]].head())
        
    if not occurrences_df.empty:
        print("\nSample occurrences:")
        print(occurrences_df[["scientific_name", "decimal_latitude", "decimal_longitude", "event_date"]].head())