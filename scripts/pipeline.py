#!/usr/bin/env python3
"""
Async ETL pipeline for Hageglede project using fetcher classes and correct transformer functions.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Third-party imports
import pandas as pd
from dotenv import load_dotenv

# Local imports
from scripts.fetchers.gbif import GbifFetcher
from scripts.fetchers.met import METFetcher
from scripts.fetchers.artsdatabanken import ArtsdatabankenFetcher
from scripts.transformers.plants import transform_gbif_occurrences, transform_artsdatabanken_data
from scripts.transformers.climate import transform_met_weather_data
from scripts.loaders.plant_loader import load_plant_data
from scripts.loaders.weather_loader import load_weather_data
from scripts.config import (
    DATABASE_PATH,
    LOGGING_CONFIG,
    GBIF_API_CONFIG,
    MET_API_CONFIG,
    ARTSDATABANKEN_API_CONFIG
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(**LOGGING_CONFIG)
logger = logging.getLogger(__name__)


async def run_pipeline(config_path="config/pipeline_config.json"):
    """
    Main async ETL pipeline runner.
    
    Args:
        config_path (str): Path to pipeline configuration file.
    
    Returns:
        bool: True if pipeline completed successfully, False otherwise.
    """
    logger.info("Starting Hageglede async ETL pipeline")
    
    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        return False
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize fetchers
    gbif_fetcher = GbifFetcher(**GBIF_API_CONFIG)
    met_fetcher = METFetcher(**MET_API_CONFIG)
    artsdatabanken_fetcher = ArtsdatabankenFetcher(**ARTSDATABANKEN_API_CONFIG)
    
    # EXTRACT phase
    logger.info("Starting EXTRACT phase")
    
    # Extract data from all sources concurrently
    gbif_data = None
    met_data = None
    artsdatabanken_data = None
    
    try:
        # Run fetchers concurrently
        extract_tasks = []
        
        if config.get("extract", {}).get("gbif", False):
            logger.info("Starting GBIF data extraction")
            extract_tasks.append(gbif_fetcher.fetch_occurrences_async(
                taxon_key=config.get("gbif", {}).get("taxon_key", None),
                country=config.get("gbif", {}).get("country", "NO"),
                limit=config.get("gbif", {}).get("limit", 1000)
            ))
        
        if config.get("extract", {}).get("met", False):
            logger.info("Starting MET weather data extraction")
            extract_tasks.append(met_fetcher.fetch_weather_async(
                lat=config.get("met", {}).get("latitude", 59.9139),
                lon=config.get("met", {}).get("longitude", 10.7522),
                days=config.get("met", {}).get("days", 7)
            ))
        
        if config.get("extract", {}).get("artsdatabanken", False):
            logger.info("Starting Artsdatabanken data extraction")
            extract_tasks.append(artsdatabanken_fetcher.fetch_species_async(
                taxon_id=config.get("artsdatabanken", {}).get("taxon_id", None),
                limit=config.get("artsdatabanken", {}).get("limit", 100)
            ))
        
        # Wait for all extraction tasks to complete
        if extract_tasks:
            results = await asyncio.gather(*extract_tasks, return_exceptions=True)
            
            # Process results
            result_index = 0
            if config.get("extract", {}).get("gbif", False):
                gbif_result = results[result_index]
                if isinstance(gbif_result, Exception):
                    logger.error(f"Failed to extract GBIF data: {gbif_result}")
                else:
                    gbif_data = gbif_result
                    logger.info(f"Extracted GBIF data: {len(gbif_data) if gbif_data else 0} records")
                result_index += 1
            
            if config.get("extract", {}).get("met", False):
                met_result = results[result_index]
                if isinstance(met_result, Exception):
                    logger.error(f"Failed to extract MET data: {met_result}")
                else:
                    met_data = met_result
                    logger.info(f"Extracted MET data: {len(met_data) if met_data else 0} records")
                result_index += 1
            
            if config.get("extract", {}).get("artsdatabanken", False):
                artsdatabanken_result = results[result_index]
                if isinstance(artsdatabanken_result, Exception):
                    logger.error(f"Failed to extract Artsdatabanken data: {artsdatabanken_result}")
                else:
                    artsdatabanken_data = artsdatabanken_result
                    logger.info(f"Extracted Artsdatabanken data: {len(artsdatabanken_data) if artsdatabanken_data else 0} records")
        
        logger.info("EXTRACT phase completed")
        
    except Exception as e:
        logger.error(f"Error during EXTRACT phase: {e}")
        return False
    
    # TRANSFORM phase
    logger.info("Starting TRANSFORM phase")
    
    plant_df = None
    weather_df = None
    species_df = None
    
    try:
        # Transform GBIF data
        if gbif_data:
            try:
                plant_df = transform_gbif_occurrences(gbif_data)
                logger.info(f"Transformed GBIF data: {len(plant_df) if plant_df is not None else 0} rows")
            except Exception as e:
                logger.error(f"Failed to transform GBIF data: {e}")
        
        # Transform MET weather data
        if met_data:
            try:
                weather_df = transform_met_weather_data(met_data)
                logger.info(f"Transformed MET weather data: {len(weather_df) if weather_df is not None else 0} rows")
            except Exception as e:
                logger.error(f"Failed to transform MET weather data: {e}")
        
        # Transform Artsdatabanken data
        if artsdatabanken_data:
            try:
                species_df = transform_artsdatabanken_data(artsdatabanken_data)
                logger.info(f"Transformed Artsdatabanken data: {len(species_df) if species_df is not None else 0} rows")
            except Exception as e:
                logger.error(f"Failed to transform Artsdatabanken data: {e}")
        
        logger.info("TRANSFORM phase completed")
        
    except Exception as e:
        logger.error(f"Error during TRANSFORM phase: {e}")
        return False
    
    # LOAD phase
    logger.info("Starting LOAD phase")
    
    try:
        # Load plant data
        if plant_df is not None and not plant_df.empty:
            try:
                load_plant_data(plant_df, DATABASE_PATH)
                logger.info(f"Loaded {len(plant_df)} plant records to database")
            except Exception as e:
                logger.error(f"Failed to load plant data: {e}")
        
        # Load weather data
        if weather_df is not None and not weather_df.empty:
            try:
                load_weather_data(weather_df, DATABASE_PATH)
                logger.info(f"Loaded {len(weather_df)} weather records to database")
            except Exception as e:
                logger.error(f"Failed to load weather data: {e}")
        
        # Load species data (Artsdatabanken)
        if species_df is not None and not species_df.empty:
            try:
                # For now, use plant loader for species data too
                load_plant_data(species_df, DATABASE_PATH)
                logger.info(f"Loaded {len(species_df)} species records to database")
            except Exception as e:
                logger.error(f"Failed to load species data: {e}")
        
        logger.info("LOAD phase completed")
        
    except Exception as e:
        logger.error(f"Error during LOAD phase: {e}")
        return False
    
    # Generate summary statistics
    logger.info("Generating summary statistics")
    try:
        import sqlite3
        
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Count records in each table
        tables = ["plants", "weather_data", "species"]
        for table in tables:
            try:
                count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]["count"]
                logger.info(f"Table '{table}': {count} records")
            except Exception as e:
                logger.warning(f"Could not count records in table '{table}': {e}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to generate statistics: {e}")
    
    logger.info("ETL pipeline completed successfully")
    return True


def main():
    """Main entry point for the pipeline."""
    # Default config path
    config_path = "config/pipeline_config.json"
    
    # Allow command-line override of config path
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # Run the async pipeline
    success = asyncio.run(run_pipeline(config_path))
    
    if success:
        logger.info("Pipeline execution finished successfully")
        sys.exit(0)
    else:
        logger.error("Pipeline execution failed")
        sys.exit(1)


if __name__ == "__main__":
    main()