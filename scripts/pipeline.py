#!/usr/bin/env python3
"""
Pipeline for the hageglede project.

This script coordinates fetching species data from GBIF,
processing it, and storing the results.
"""

import asyncio
import logging
from pathlib import Path

import pandas as pd

from scripts.fetchers.gbif import GbifFetcher
from scripts.transformers.plants import CropTransformer
from scripts.transformers.climate import ZoneTransformer
from scripts.transformers.weather import WeatherTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.fetcher = GbifFetcher()
        self.crop_transformer = CropTransformer()
        self.zone_transformer = ZoneTransformer()
        self.weather_transformer = WeatherTransformer()

    async def run(self, query: str, limit: int = 50):
        """Run the complete pipeline for a given search query."""
        logger.info(f"Starting pipeline with query: '{query}' (limit: {limit})")
        
        try:
            # 1. Fetch species from GBIF
            logger.info("Fetching species data from GBIF...")
            species_list = await self.fetcher.search(query, limit=limit)
            
            if not species_list:
                logger.warning(f"No species found for query: '{query}'")
                return
            
            logger.info(f"Found {len(species_list)} species")
            
            # 2. Process species data using CropTransformer
            logger.info("Processing species data with CropTransformer...")
            processed_species = []
            for species in species_list:
                try:
                    processed = self.crop_transformer.transform(species)
                    processed_species.append(processed)
                except Exception as e:
                    logger.warning(f"Failed to process species {species.get('canonical_name', 'unknown')}: {e}")
            
            # 3. Process climate data using ZoneTransformer
            logger.info("Processing climate data with ZoneTransformer...")
            climate_results = []
            for species in processed_species:
                try:
                    zone_data = self.zone_transformer.transform(species)
                    climate_results.append({
                        'species': species.get('canonical_name', 'unknown'),
                        'zone_data': zone_data
                    })
                except Exception as e:
                    logger.warning(f"Failed to process climate data for {species.get('canonical_name', 'unknown')}: {e}")
            
            # 4. For each species, fetch occurrences
            logger.info("Fetching occurrences for each species...")
            occurrence_results = []
            
            for species in processed_species:
                if 'taxon_key' in species:
                    try:
                        occurrences = await self.fetcher.fetch_occurrences(species['taxon_key'])
                        if occurrences is not None and not occurrences.empty:
                            logger.info(f"Found {len(occurrences)} occurrences for {species.get('canonical_name', 'unknown')}")
                            occurrence_results.append({
                                'species': species['canonical_name'],
                                'taxon_key': species['taxon_key'],
                                'occurrences': occurrences
                            })
                            # Process occurrences with WeatherTransformer
                            try:
                                weather_enhanced = self.weather_transformer.transform(occurrences)
                                logger.info(f"WeatherTransformer enhanced {len(weather_enhanced)} occurrences")
                            except Exception as e:
                                logger.warning(f"Failed to enhance occurrences with WeatherTransformer: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to fetch occurrences for {species.get('canonical_name', 'unknown')}: {e}")
            
            logger.info(f"Pipeline completed successfully for query: '{query}'")
            logger.info(f"- Processed {len(processed_species)} species using CropTransformer")
            logger.info(f"- Found occurrence data for {len(occurrence_results)} species")
            logger.info(f"- Generated zone data for {len(climate_results)} species using ZoneTransformer")
            
            return {
                'species': processed_species,
                'occurrences': occurrence_results,
                'zone_data': climate_results
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise

    async def run_multiple_queries(self, queries: list[str], limit_per_query: int = 20):
        """Run pipeline for multiple queries sequentially."""
        results = {}
        
        for query in queries:
            logger.info(f"Processing query: '{query}'")
            try:
                result = await self.run(query, limit=limit_per_query)
                results[query] = result
            except Exception as e:
                logger.error(f"Failed to process query '{query}': {e}")
                results[query] = {'error': str(e)}
                
        return results


async def main():
    """Main entry point for the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the hageglede pipeline')
    parser.add_argument('query', nargs='+', help='Search query(ies) for species')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of species per query')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    
    args = parser.parse_args()
    
    pipeline = Pipeline(args.config)
    
    if len(args.query) == 1:
        await pipeline.run(args.query[0], args.limit)
    else:
        await pipeline.run_multiple_queries(args.query, args.limit)


if __name__ == '__main__':
    asyncio.run(main())