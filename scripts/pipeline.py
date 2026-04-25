#!/usr/bin/env python3
"""
Plant data ETL pipeline: fetch, transform, and load operations.
Coordinates the whole workflow from fetching raw data to loading into SQLite.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the Python path for module imports
sys.path.append(str(Path(__file__).parent))

from fetch.plant_fetcher import fetch_plant_data
from processors.plant_processor import process_plant_data
from loaders.plant_loader import load_plant_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_PATH = DATA_DIR / "plant_data.db"

def run_pipeline() -> bool:
    """
    Execute the full ETL pipeline:
    1. Fetch plant data
    2. Process/transform the data
    3. Load into SQLite database
    
    Returns:
        bool: True if pipeline completed successfully, False otherwise
    """
    try:
        logger.info("Starting plant data ETL pipeline")
        
        # Ensure directories exist
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Step 1: Fetch plant data
        logger.info("Step 1: Fetching plant data...")
        raw_file_path = RAW_DATA_DIR / f"plants_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            fetch_plant_data(raw_file_path)
            logger.info(f"✓ Successfully fetched plant data to {raw_file_path}")
        except Exception as e:
            logger.error(f"✗ Failed to fetch plant data: {e}")
            return False
        
        # Step 2: Process/transform the data
        logger.info("Step 2: Processing plant data...")
        processed_file_path = PROCESSED_DATA_DIR / f"plants_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            plant_df = process_plant_data(raw_file_path, processed_file_path)
            logger.info(f"✓ Successfully processed plant data to {processed_file_path}")
            logger.info(f"  Processed {len(plant_df)} plant records")
        except Exception as e:
            logger.error(f"✗ Failed to process plant data: {e}")
            return False
        
        # Step 3: Load into SQLite database
        logger.info("Step 3: Loading plant data into database...")
        
        try:
            load_plant_data(plant_df, DATABASE_PATH)
            logger.info(f"✓ Successfully loaded plant data into {DATABASE_PATH}")
        except Exception as e:
            logger.error(f"✗ Failed to load plant data: {e}")
            return False
        
        logger.info("✓ Plant data ETL pipeline completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Pipeline failed with unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)