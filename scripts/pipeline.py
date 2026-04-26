#!/usr/bin/env python3
"""
ETL pipeline for synchronizing plant observation data.
Coordinates fetching from GBIF and Artsdatabanken,
cleaning, and merging to a master dataset.
"""

# PURPOSE: Fix imports to directly use gbif and artsbanken fetchers instead of broken plant_fetcher wrapper
# CONSUMED BY: main entry point
# DEPENDS ON: scripts.fetchers.gbif, scripts.fetchers.artsbanken, scripts.common.logger, scripts.common.errors

import os
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from scripts.common.logger import setup_logger
from scripts.common.errors import DataFetchError
from scripts.fetchers.gbif import GBIFDataFetcher
from scripts.fetchers.artsbanken import ArtsdatabankenDataFetcher


# Constants
INTERMEDIATE_PATH = Path("./data/intermediate")
FINAL_PATH = Path("./data/final")
LOG_PATH = Path("./logs")


def ensure_directories():
    """Ensure all required directories exist."""
    INTERMEDIATE_PATH.mkdir(parents=True, exist_ok=True)
    FINAL_PATH.mkdir(parents=True, exist_ok=True)
    LOG_PATH.mkdir(parents=True, exist_ok=True)


def fetch_gbif_data(logger):
    """Fetch data from GBIF API."""
    logger.info("Starting GBIF fetch...")
    try:
        # GBIF specific configuration
        gbif_config = {
            "taxon_key": 6,  # Plantae
            "year": "2020,2021,2022,2023",
            "country": "NO",
            "limit": 1000  # Adjust based on needs
        }
        
        fetcher = GBIFDataFetcher(gbif_config)
        data = fetcher.fetch()
        
        # Save intermediate data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gbif_file = INTERMEDIATE_PATH / f"gbif_raw_{timestamp}.json"
        fetcher.save_to_file(data, gbif_file)
        
        logger.info(f"GBIF fetch completed. Data saved to {gbif_file}")
        return gbif_file
        
    except Exception as e:
        logger.error(f"GBIF fetch failed: {e}")
        raise DataFetchError(f"GBIF fetch failed: {e}")


def fetch_artsdatabanken_data(logger):
    """Fetch data from Artsdatabanken API."""
    logger.info("Starting Artsdatabanken fetch...")
    try:
        # Artsdatabanken specific configuration
        arts_config = {
            "taxon_id": 6,  # Plantae kingdom
            "area": "HELE_LANDET",
            "limit": 1000
        }
        
        fetcher = ArtsdatabankenDataFetcher(arts_config)
        data = fetcher.fetch()
        
        # Save intermediate data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arts_file = INTERMEDIATE_PATH / f"artsdatabanken_raw_{timestamp}.json"
        fetcher.save_to_file(data, arts_file)
        
        logger.info(f"Artsdatabanken fetch completed. Data saved to {arts_file}")
        return arts_file
        
    except Exception as e:
        logger.error(f"Artsdatabanken fetch failed: {e}")
        raise DataFetchError(f"Artsdatabanken fetch failed: {e}")


def clean_and_transform(data_files, logger):
    """Clean and transform raw data from both sources.
    
    Args:
        data_files: Dictionary with 'gbif' and 'artsdatabanken' keys pointing to file paths
        logger: Logger instance
        
    Returns:
        Dictionary with cleaned data from both sources
    """
    logger.info("Starting data cleaning and transformation...")
    
    # Placeholder for actual cleaning logic
    cleaned_data = {
        'gbif': f"Cleaned GBIF data from {data_files.get('gbif')}",
        'artsdatabanken': f"Cleaned Artsdatabanken data from {data_files.get('artsdatabanken')}"
    }
    
    logger.info("Data cleaning completed.")
    return cleaned_data


def merge_datasets(cleaned_data, logger):
    """Merge cleaned data from both sources into a unified dataset."""
    logger.info("Starting dataset merge...")
    
    # Placeholder for actual merging logic
    merged_data = {
        'merged': True,
        'sources': ['gbif', 'artsdatabanken'],
        'record_count': 0,  # This would be actual count
        'timestamp': datetime.now().isoformat()
    }
    
    # Save merged dataset
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    merged_file = FINAL_PATH / f"merged_plant_observations_{timestamp}.json"
    
    # In a real implementation, you would write the actual merged data
    with open(merged_file, 'w') as f:
        import json
        json.dump(merged_data, f, indent=2)
    
    logger.info(f"Merged dataset saved to {merged_file}")
    return merged_file


def run_pipeline():
    """Main pipeline execution function."""
    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_PATH / f"pipeline_{timestamp}.log"
    
    logger = setup_logger(
        name="etl_pipeline",
        log_file=log_file,
        level=logging.INFO
    )
    
    logger.info("=" * 60)
    logger.info("Starting ETL Pipeline for Plant Observation Data")
    logger.info("=" * 60)
    
    try:
        # Ensure directories exist
        ensure_directories()
        
        # Step 1: Fetch data from both sources
        logger.info("Phase 1: Data Fetching")
        logger.info("-" * 40)
        
        gbif_file = fetch_gbif_data(logger)
        arts_file = fetch_artsdatabanken_data(logger)
        
        data_files = {
            'gbif': gbif_file,
            'artsdatabanken': arts_file
        }
        
        # Step 2: Clean and transform
        logger.info("\nPhase 2: Data Cleaning")
        logger.info("-" * 40)
        
        cleaned_data = clean_and_transform(data_files, logger)
        
        # Step 3: Merge datasets
        logger.info("\nPhase 3: Data Merging")
        logger.info("-" * 40)
        
        merged_file = merge_datasets(cleaned_data, logger)
        
        logger.info("=" * 60)
        logger.info("ETL Pipeline completed successfully!")
        logger.info(f"Final dataset: {merged_file}")
        logger.info("=" * 60)
        
        return True, merged_file
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False, None


if __name__ == "__main__":
    success, result = run_pipeline()
    if success:
        print(f"Pipeline completed successfully. Result: {result}")
        sys.exit(0)
    else:
        print("Pipeline failed.")
        sys.exit(1)