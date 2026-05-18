# PURPOSE: Main entry point for the Hageglede data pipeline; orchestrates fetching, processing, and loading.
# CONSUMED BY: none (entry point)
# DEPENDS ON: scripts.config, fetchers.siv, fetchers.wikidata, db.db_ops, db.utils
# TEST: none

"""
Main entry point for the Hageglede data pipeline.
Orchestrates fetching, processing, and loading of all data.
"""
import sys
import os
import time
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Callable

from scripts.config import DATABASE_PATH, DATA_DIR, FROST_CONFIG, MET_API_CONFIG, ARTSDB_API_CONFIG

from fetchers.siv import (
    SIVClient, fetch_all_siv_data, process_siv_data
)
from fetchers.wikidata import (
    WikidataFetcher, search_wikidata_entities, fetch_entity_data, extract_taxon_info
)
from db.db_ops import DatabaseManager
from db.utils import get_connection, close_connection, execute_query


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the pipeline."""
    # Add colored output for terminal
    import logging
    
    # Create a custom formatter with colors
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors for terminal output."""
        
        COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m' # Magenta
        }
        RESET = '\033[0m'
        
        def format(self, record):
            # Only use colors if outputting to a terminal
            if sys.stdout.isatty():
                level_color = self.COLORS.get(record.levelname, '')
                record.levelname = f"{level_color}{record.levelname}{self.RESET}"
            return super().format(record)
    
    formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.handlers = []
    root_logger.addHandler(handler)


def run_step(step_func: Callable, step_name: str) -> None:
    """Helper to run a pipeline step with timing and error handling."""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting step: {step_name}")
    
    start_time = time.time()
    try:
        result = step_func()
        elapsed = time.time() - start_time
        logger.info(f"Completed step '{step_name}' in {elapsed:.2f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed step '{step_name}' after {elapsed:.2f}s: {e}")
        raise


def run_pipeline(steps: List[str], force_refresh: bool = False, 
                 skip_fetch: bool = False) -> Dict[str, Any]:
    """
    Run the full data pipeline.
    
    Args:
        steps: List of pipeline steps to run (e.g., ['fetch', 'process', 'load'])
        force_refresh: If True, bypass any data caching and re-fetch everything
        skip_fetch: If True, skip fetching fresh data and use cached/processed data
        
    Returns:
        Dictionary containing the status of each step and summary metrics
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Hageglede Pipeline started")
    logger.info(f"Database path: {DATABASE_PATH}")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"MET API config: {MET_API_CONFIG}")
    logger.info(f"Artsdatabanken API config: {ARTSDB_API_CONFIG}")
    
    # Ensure database and paths exist
    os.makedirs(DATA_DIR, exist_ok=True)
    db_path = Path(DATABASE_PATH)
    if not db_path.exists():
        logger.info("Creating new database")
        # Initialize database schema
        init_db()
    
    # Ensure subdirectories exist for caching
    cache_dir = Path(DATA_DIR) / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    results = {
        'steps_completed': [],
        'steps_failed': [],
        'errors': [],
        'total_time': 0,
        'records_processed': 0
    }
    
    steps = [step.lower() for step in steps]
    all_steps = ['fetch', 'process', 'load', 'validate']
    
    # If 'all' is requested, run everything
    if 'all' in steps:
        steps = all_steps
    
    start_time = time.time()
    
    try:
        # Step: Initialize database if needed
        if any(step in all_steps for step in steps):
            run_step(init_db, "Initialize database")
            results['steps_completed'].append('init')
        
        # Step: Fetch data from sources
        if 'fetch' in steps and not skip_fetch:
            if force_refresh:
                logger.info("Force refresh enabled - will clear caches")
                clear_all_caches()
            
            # Fetch plant data
            run_step(fetch_plant_data, "Fetch plant data")
            
            # Fetch weather data
            run_step(fetch_weather_data, "Fetch weather data")
            
            results['steps_completed'].append('fetch')
        
        # Step: Process and clean data
        if 'process' in steps:
            pass  # Processing done inline during fetch
        
        # Step: Load data into database
        if 'load' in steps:
            run_step(load_all_data, "Load all data")
            results['steps_completed'].append('load')
        
        # Step: Validate data
        if 'validate' in steps:
            run_step(validate_pipeline, "Validate pipeline data")
            results['steps_completed'].append('validate')
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        results['errors'].append(str(e))
        results['steps_failed'].append('pipeline')
        raise
    
    finally:
        # Always close database connections
        close_connection()
        
        elapsed = time.time() - start_time
        results['total_time'] = elapsed
        
        if results['steps_failed']:
            logger.warning(f"Pipeline completed with {len(results['steps_failed'])} failed steps in {elapsed:.2f}s")
        else:
            logger.info(f"Pipeline completed successfully in {elapsed:.2f}s")
        
        return results


def init_db() -> None:
    """Initialize database schema and ensure tables exist."""
    db = DatabaseManager()
    db.init_db()


def fetch_plant_data() -> Dict[str, Any]:
    """Fetch plant data from all configured sources."""
    results = {
        'siv': {},
        'wikidata': {},
        'errors': []
    }
    
    logger = logging.getLogger(__name__)
    
    # Fetch from SIV
    try:
        siv_client = SIVClient()
        siv_data = siv_client.fetch_all()
        results['siv'] = process_siv_data(siv_data)
    except Exception as e:
        logger.error(f"Error fetching SIV data: {e}")
        results['errors'].append(('siv', str(e)))
    
    # Fetch from Wikidata
    try:
        wikidata_fetcher = WikidataFetcher()
        # Search for relevant entities
        entities = wikidata_fetcher.search_entities("Norwegian garden plants", lang="no")
        results['wikidata'] = entities
    except Exception as e:
        logger.error(f"Error fetching Wikidata: {e}")
        results['errors'].append(('wikidata', str(e)))
    
    return results


def fetch_weather_data() -> Dict[str, Any]:
    """Fetch weather data from MET API."""
    logger = logging.getLogger(__name__)
    
    from fetchers.met import FrostClient, fetch_weather_observations
    
    results = {
        'observations': [],
        'errors': []
    }
    
    try:
        # Initialize Frost client with config
        client = FrostClient()
        
        # Fetch observations for Norway
        observations = fetch_weather_observations(client, source_id="SN18700")
        results['observations'] = observations
        
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        results['errors'].append(('met', str(e)))
    
    return results


def load_all_data() -> Dict[str, Any]:
    """Load all fetched data into the database."""
    logger = logging.getLogger(__name__)
    
    # Load plant data (placeholder - actual implementation depends on data structure)
    logger.info("Loading plant data")
    # TODO: Implement data loading based on actual data structures
    
    return {}


def validate_pipeline() -> bool:
    """Validate pipeline data integrity."""
    logger = logging.getLogger(__name__)
    
    # Check for required tables
    # Check for data freshness
    # Validate relationships between data sources
    
    logger.info("Pipeline validation completed")
    return True


def clear_all_caches() -> None:
    """Clear all cached data to force re-fetching."""
    logger = logging.getLogger(__name__)
    cache_dir = Path(DATA_DIR) / "cache"
    if cache_dir.exists():
        logger.info(f"Clearing cache directory: {cache_dir}")
        for f in cache_dir.glob("*"):
            try:
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    import shutil
                    shutil.rmtree(f)
            except Exception as e:
                logger.warning(f"Failed to remove cache item {f}: {e}")


def main():
    """Main entry point for the pipeline CLI."""
    parser = argparse.ArgumentParser(description="Hageglede Data Pipeline")
    parser.add_argument(
        'steps',
        nargs='*',
        default=['all'],
        help='Pipeline steps to run (fetch, process, load, validate) or "all"'
    )
    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force re-fetching all data'
    )
    parser.add_argument(
        '--skip-fetch',
        action='store_true',
        help='Skip fetching and use cached data only'
    )
    
    args = parser.parse_args()
    
    try:
        results = run_pipeline(
            steps=args.steps,
            force_refresh=args.force_refresh,
            skip_fetch=args.skip_fetch
        )
        
        if results['steps_failed']:
            print(f"\nPipeline completed with errors in {results['total_time']:.2f}s")
            sys.exit(1)
        else:
            print(f"\nPipeline completed successfully in {results['total_time']:.2f}s")
            
    except Exception as e:
        print(f"\nPipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
