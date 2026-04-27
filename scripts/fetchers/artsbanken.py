#!/usr/bin/env python3
"""
Artsdatabanken fetcher - interfaces with Norwegian species database.

This module provides functions to fetch plant species data from Artsdatabanken (Norwegian Biodiversity Information Centre).

Functions:
- fetch_artsdatabanken_data: Main function to fetch plant species data
- get_plant_species_families: Get families tree for plants
- fetch_all_plants: Comprehensive plant fetch with all fields
"""

import requests
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

BASE_URL = "https://api.artsdatabanken.no"

def fetch_artsdatabanken_data(output_path: str = "data/artsdatabanken_plants.csv") -> bool:
    """
    Fetch plant species data from Artsdatabanken API.
    
    Args:
        output_path: Path to save the CSV file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Fetching plant species data from Artsdatabanken...")
        
        # Get complete plant data
        plants_df = get_complete_plant_data()
        
        if plants_df.empty:
            logger.error("No plant data retrieved from Artsdatabanken")
            return False
            
        # Save to CSV
        plants_df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully saved {len(plants_df)} plant records to {output_path}")
        print(f"\nArtsdatabanken Data Summary:")
        print(f"  Total plants: {len(plants_df)}")
        print(f"  Columns: {list(plants_df.columns)}")
        print(f"  Saved to: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fetching Artsdatabanken data: {e}")
        return False

def get_complete_plant_data() -> pd.DataFrame:
    """
    Get comprehensive plant data from Artsdatabanken.
    
    Returns:
        DataFrame with plant species data
    """
    try:
        # Search for plants (Viridiplantae kingdom)
        search_url = f"{BASE_URL}/search/species"
        search_params = {
            "kingdom": "Viridiplantae",
            "take": 1000,
            "skip": 0
        }
        
        logger.info(f"Searching for plants with params: {search_params}")
        response = requests.get(search_url, params=search_params, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Search request failed with status {response.status_code}")
            return pd.DataFrame()
            
        search_data = response.json()
        
        if not search_data or "items" not in search_data:
            logger.error("Invalid response format from search")
            return pd.DataFrame()
            
        plant_items = search_data["items"]
        logger.info(f"Found {len(plant_items)} plant species in search")
        
        # Get detailed data for each plant
        plants_data = []
        for i, item in enumerate(plant_items):
            try:
                species_id = item.get("scientificNameId")
                if not species_id:
                    continue
                    
                # Fetch detailed species information
                species_url = f"{BASE_URL}/species/{species_id}"
                species_response = requests.get(species_url, timeout=30)
                
                if species_response.status_code == 200:
                    species_details = species_response.json()
                    
                    plant_record = {
                        "species_id": species_id,
                        "scientific_name": species_details.get("scientificName", ""),
                        "vernacular_name": item.get("vernacularName", ""),
                        "author": species_details.get("author", ""),
                        "accepted_name": species_details.get("acceptedNameScientificName", ""),
                        "kingdom": species_details.get("kingdom", ""),
                        "phylum": species_details.get("phylum", ""),
                        "class": species_details.get("class", ""),
                        "order": species_details.get("order", ""),
                        "family": species_details.get("family", ""),
                        "genus": species_details.get("genus", ""),
                        "species": species_details.get("species", ""),
                        "risk_category": species_details.get("riskCategory", ""),
                        "last_assessed": species_details.get("lastAssessed", ""),
                        "assessment_authority": species_details.get("assessmentAuthority", ""),
                        "taxon_rank": species_details.get("taxonRank", ""),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    plants_data.append(plant_record)
                    
                if i % 50 == 0:
                    logger.debug(f"Processed {i+1}/{len(plant_items)} plant species")
                    
            except Exception as e:
                logger.warning(f"Error fetching details for species {item.get('scientificNameId')}: {e}")
                continue
        
        if not plants_data:
            logger.warning("No detailed plant data could be retrieved")
            return pd.DataFrame()
            
        plants_df = pd.DataFrame(plants_data)
        logger.info(f"Retrieved detailed data for {len(plants_df)} plant species")
        
        return plants_df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching Artsdatabanken data: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in get_complete_plant_data: {e}")
        return pd.DataFrame()

def get_plant_species_families() -> Dict[str, List[str]]:
    """
    Get the plant families and their species from Artsdatabanken.
    
    Returns:
        Dictionary mapping family names to lists of species scientific names
    """
    families = {}
    
    try:
        plants_df = get_complete_plant_data()
        
        if plants_df.empty:
            return {}
            
        # Group by family
        for family in plants_df["family"].unique():
            if pd.isna(family):
                continue
                
            family_species = plants_df[plants_df["family"] == family]["scientific_name"].tolist()
            families[family] = family_species
        
        logger.info(f"Found {len(families)} plant families with species")
        return families
        
    except Exception as e:
        logger.error(f"Error getting plant families: {e}")
        return {}

def fetch_all_plants(include_risk_assessment: bool = True) -> pd.DataFrame:
    """
    Alternative function to fetch all plant data with comprehensive fields.
    
    Args:
        include_risk_assessment: Whether to include risk assessment data
        
    Returns:
        DataFrame with comprehensive plant data
    """
    return get_complete_plant_data()

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = "data/artsdatabanken_plants.csv"
        
    success = fetch_artsdatabanken_data(output_path)
    
    if success:
        print("\n✅ Artsdatabanken data fetch completed successfully")
    else:
        print("\n❌ Artsdatabanken data fetch failed")
        sys.exit(1)