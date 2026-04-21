#!/usr/bin/env python3
"""
ETL pipeline for Hageglede project.
"""

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
from scripts.extractors import extract_github_data, extract_weather_data
from scripts.transformers import (
    transform_plant_data, 
    transform_climate_data,
    transform_garden_data, 
    transform_weather_data,
    load_to_db
)
from scripts.loaders import (
    init_sqlite_db,
    setup_logging
)
from scripts.database import get_db_connection

# Load environment variables
load_dotenv()

# Configuration
GITHUB_API_URL = "https://api.github.com"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


def run_pipeline(config_path="config/pipeline_config.json"):
    """
    Main ETL pipeline runner.
    
    Args:
        config_path (str): Path to pipeline configuration file.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Hageglede ETL pipeline")
    
    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)
    
    # Initialize database
    try:
        db_path = config.get("database", {}).get("path", "data/hageglede.db")
        init_sqlite_db(db_path)
        logger.info(f"Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # EXTRACT phase
    logger.info("Starting EXTRACT phase")
    
    # Extract GitHub data
    github_data = None
    if config.get("extract", {}).get("github", False):
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                logger.warning("GITHUB_TOKEN not found in environment, using unauthenticated GitHub API")
            
            github_data = extract_github_data(
                api_url=GITHUB_API_URL,
                token=github_token,
                repos=config.get("github_repos", []),
                since_days=config.get("extract", {}).get("since_days", 7)
            )
            logger.info(f"Extracted GitHub data: {len(github_data) if github_data else 0} records")
        except Exception as e:
            logger.error(f"Failed to extract GitHub data: {e}")
    
    # Extract weather data
    weather_data = None
    if config.get("extract", {}).get("weather", False):
        try:
            weather_data = extract_weather_data(
                api_url=WEATHER_API_URL,
                latitude=config.get("weather", {}).get("latitude", 59.9139),  # Oslo
                longitude=config.get("weather", {}).get("longitude", 10.7522),
                days=config.get("extract", {}).get("weather_days", 7)
            )
            logger.info(f"Extracted weather data: {len(weather_data) if weather_data else 0} records")
        except Exception as e:
            logger.error(f"Failed to extract weather data: {e}")
    
    # TRANSFORM phase
    logger.info("Starting TRANSFORM phase")
    
    # Transform plant data
    plant_df = None
    if github_data:
        try:
            plant_df = transform_plant_data(github_data)
            logger.info(f"Transformed plant data: {len(plant_df) if plant_df is not None else 0} rows")
        except Exception as e:
            logger.error(f"Failed to transform plant data: {e}")
    
    # Transform climate data
    climate_df = None
    if weather_data:
        try:
            climate_df = transform_climate_data(weather_data)
            logger.info(f"Transformed climate data: {len(climate_df) if climate_df is not None else 0} rows")
        except Exception as e:
            logger.error(f"Failed to transform climate data: {e}")
    
    # Transform garden data
    garden_df = None
    if github_data:
        try:
            garden_df = transform_garden_data(github_data)
            logger.info(f"Transformed garden data: {len(garden_df) if garden_df is not None else 0} rows")
        except Exception as e:
            logger.error(f"Failed to transform garden data: {e}")
    
    # Transform weather data
    weather_df = None
    if weather_data:
        try:
            weather_df = transform_weather_data(weather_data)
            logger.info(f"Transformed weather data: {len(weather_df) if weather_df is not None else 0} rows")
        except Exception as e:
            logger.error(f"Failed to transform weather data: {e}")
    
    # LOAD phase
    logger.info("Starting LOAD phase")
    
    # Load all transformed data to database
    try:
        load_to_db(
            plant_df=plant_df,
            climate_df=climate_df,
            garden_df=garden_df,
            weather_df=weather_df,
            db_path=db_path
        )
        logger.info("Successfully loaded all data to database")
    except Exception as e:
        logger.error(f"Failed to load data to database: {e}")
        sys.exit(1)
    
    # Generate summary statistics
    logger.info("Generating summary statistics")
    try:
        with get_db_connection(db_path) as conn:
            # Count records in each table
            tables = ["plants", "climate_data", "gardens", "weather_observations"]
            for table in tables:
                count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]["count"]
                logger.info(f"Table '{table}': {count} records")
    except Exception as e:
        logger.error(f"Failed to generate statistics: {e}")
    
    logger.info("ETL pipeline completed successfully")
    return True


if __name__ == "__main__":
    # Default config path
    config_path = "config/pipeline_config.json"
    
    # Allow command-line override of config path
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    success = run_pipeline(config_path)
    sys.exit(0 if success else 1)