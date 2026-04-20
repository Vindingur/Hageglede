#!/usr/bin/env python3
"""
Hageglede Data Pipeline

A complete data processing pipeline for gardening planning:
- Fetches plant data from Artsdatabanken
- Fetches species observations from GBIF
- Fetches climate data from MET (Norwegian Meteorological Institute)
- Transforms and loads into local database
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.config import PipelineConfig, load_config
from scripts.fetchers.artsdatabanken import ArtsdatabankenFetcher
from scripts.fetchers.gbif import GbifFetcher
from scripts.fetchers.met import MetFetcher
from scripts.transformers.plants import PlantTransformer
from scripts.transformers.climate import ClimateTransformer
from scripts.loaders import DatabaseLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HagegledePipeline:
    """Main pipeline orchestrating data flow from sources to database."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.fetchers = {
            'artsdatabanken': ArtsdatabankenFetcher(config.sources.artsdatabanken),
            'gbif': GbifFetcher(config.sources.gbif),
            'met': MetFetcher(config.sources.met),
        }
        self.transformers = {
            'plants': PlantTransformer(),
            'climate': ClimateTransformer(),
        }
        self.loader = DatabaseLoader(config.database)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def run(self) -> dict:
        """Execute the full pipeline."""
        self.logger.info("Starting Hageglede pipeline run")
        results = {
            'started_at': datetime.utcnow().isoformat(),
            'fetch_results': {},
            'transform_results': {},
            'load_results': {},
            'errors': []
        }
        
        try:
            # Step 1: Fetch data from all sources
            self.logger.info("Fetching data from sources...")
            raw_data = await self._fetch_all()
            results['fetch_results'] = {k: len(v) if isinstance(v, list) else 'success' 
                                        for k, v in raw_data.items()}
            
            # Step 2: Transform data
            self.logger.info("Transforming data...")
            transformed = self._transform_all(raw_data)
            results['transform_results'] = {k: len(v) if isinstance(v, list) else 'success' 
                                            for k, v in transformed.items()}
            
            # Step 3: Load to database
            self.logger.info("Loading to database...")
            load_results = await self._load_all(transformed)
            results['load_results'] = load_results
            
            results['status'] = 'success'
            self.logger.info("Pipeline completed successfully")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            results['status'] = 'failed'
            results['errors'].append(str(e))
            raise
        
        finally:
            results['finished_at'] = datetime.utcnow().isoformat()
        
        return results
    
    async def _fetch_all(self) -> dict:
        """Fetch data from all configured sources."""
        results = {}
        
        # Fetch plant data
        if self.config.sources.artsdatabanken.enabled:
            self.logger.info("Fetching from Artsdatabanken...")
            results['plants'] = await self.fetchers['artsdatabanken'].fetch()
        
        # Fetch species observations
        if self.config.sources.gbif.enabled:
            self.logger.info("Fetching from GBIF...")
            results['observations'] = await self.fetchers['gbif'].fetch()
        
        # Fetch climate data
        if self.config.sources.met.enabled:
            self.logger.info("Fetching from MET...")
            results['climate'] = await self.fetchers['met'].fetch()
        
        return results
    
    def _transform_all(self, raw_data: dict) -> dict:
        """Transform all fetched data."""
        results = {}
        
        if 'plants' in raw_data:
            self.logger.info("Transforming plant data...")
            results['plants'] = self.transformers['plants'].transform(raw_data['plants'])
        
        if 'climate' in raw_data:
            self.logger.info("Transforming climate data...")
            results['climate'] = self.transformers['climate'].transform(raw_data['climate'])
        
        return results
    
    async def _load_all(self, transformed_data: dict) -> dict:
        """Load all transformed data to database."""
        results = {}
        
        async with self.loader:
            if 'plants' in transformed_data:
                self.logger.info("Loading plants to database...")
                results['plants'] = await self.loader.load_plants(transformed_data['plants'])
            
            if 'climate' in transformed_data:
                self.logger.info("Loading climate data to database...")
                results['climate'] = await self.loader.load_climate(transformed_data['climate'])
        
        return results


async def main():
    """Main entry point for pipeline execution."""
    config_path = Path(__file__).parent / 'config.yaml'
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Creating default config...")
        config = PipelineConfig.default()
    else:
        config = load_config(config_path)
    
    pipeline = HagegledePipeline(config)
    results = await pipeline.run()
    
    print(f"\nPipeline Results:")
    print(f"Status: {results['status']}")
    print(f"Fetch: {results['fetch_results']}")
    print(f"Transform: {results['transform_results']}")
    print(f"Load: {results['load_results']}")
    
    return results


if __name__ == '__main__':
    asyncio.run(main())
