#!/usr/bin/env python3
"""
Hageglede Phase 0.5 Data Pipeline Core
Main pipeline runner that orchestrates fetch → transform → load workflow.
"""

import logging
import sys
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

from config import PipelineConfig, SourceConfig
import loaders
from fetchers.base import BaseFetcher
from transformers.base import BaseTransformer

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from running a pipeline source."""
    source: str
    success: bool
    fetched_count: Optional[int] = None
    transformed_count: Optional[int] = None
    loaded_count: Optional[int] = None
    error: Optional[str] = None
    duration: float = 0.0


class PipelineRunner:
    """Main pipeline orchestrator."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.results: List[PipelineResult] = []
        
    def fetch(self, source_name: str, source_config: SourceConfig) -> List[Dict[str, Any]]:
        """Fetch data from a source using the appropriate fetcher."""
        try:
            # Dynamically import the fetcher based on source type
            if source_config.type == "vapi":
                from fetchers.vapi_fetcher import VapiFetcher
                fetcher: BaseFetcher = VapiFetcher(source_config)
            elif source_config.type == "elevenlabs":
                from fetchers.elevenlabs_fetcher import ElevenLabsFetcher
                fetcher: BaseFetcher = ElevenLabsFetcher(source_config)
            elif source_config.type == "paperspace":
                from fetchers.paperspace_fetcher import PaperspaceFetcher
                fetcher: BaseFetcher = PaperspaceFetcher(source_config)
            else:
                raise ValueError(f"Unknown source type: {source_config.type}")
            
            logger.info(f"Fetching from {source_name}...")
            raw_data = fetcher.fetch()
            
            if not raw_data:
                logger.warning(f"No data fetched from {source_name}")
                return []
            
            logger.info(f"Fetched {len(raw_data)} items from {source_name}")
            return raw_data
            
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {str(e)}", exc_info=True)
            raise
    
    def transform(self, source_name: str, source_config: SourceConfig, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform raw data using the appropriate transformer."""
        try:
            # Dynamically import the transformer based on source type
            if source_config.type == "vapi":
                from transformers.vapi_transformer import VapiTransformer
                transformer: BaseTransformer = VapiTransformer(source_config)
            elif source_config.type == "elevenlabs":
                from transformers.elevenlabs_transformer import ElevenLabsTransformer
                transformer: BaseTransformer = ElevenLabsTransformer(source_config)
            elif source_config.type == "paperspace":
                from transformers.paperspace_transformer import PaperspaceTransformer
                transformer: BaseTransformer = PaperspaceTransformer(source_config)
            else:
                raise ValueError(f"Unknown source type: {source_config.type}")
            
            logger.info(f"Transforming {len(raw_data)} items from {source_name}...")
            transformed_data = transformer.transform(raw_data)
            
            if not transformed_data:
                logger.warning(f"No data transformed from {source_name}")
                return []
            
            logger.info(f"Transformed {len(transformed_data)} items from {source_name}")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error transforming data from {source_name}: {str(e)}", exc_info=True)
            raise
    
    def load(self, source_name: str, transformed_data: List[Dict[str, Any]]) -> int:
        """Load transformed data into the database."""
        try:
            loader = loaders.SQLiteLoader(self.config.database_path)
            loaded_count = loader.upsert(transformed_data, source_name)
            
            if loaded_count > 0:
                logger.info(f"Loaded {loaded_count} items from {source_name} into database")
            else:
                logger.warning(f"No items loaded from {source_name} (possibly all duplicates)")
            
            return loaded_count
            
        except Exception as e:
            logger.error(f"Error loading data from {source_name}: {str(e)}", exc_info=True)
            raise
    
    def run_source(self, source_name: str, source_config: SourceConfig) -> PipelineResult:
        """Run the full pipeline for a single source."""
        logger.info(f"=== Processing source: {source_name} ===")
        start_time = time.time()
        
        try:
            # 1. Fetch
            raw_data = self.fetch(source_name, source_config)
            if not raw_data:
                return PipelineResult(
                    source=source_name,
                    success=False,
                    error="No data fetched",
                    duration=time.time() - start_time
                )
            
            # 2. Transform
            transformed_data = self.transform(source_name, source_config, raw_data)
            if not transformed_data:
                return PipelineResult(
                    source=source_name,
                    success=False,
                    error="No data transformed after fetching",
                    duration=time.time() - start_time
                )
            
            # 3. Load
            loaded_count = self.load(source_name, transformed_data)
            
            result = PipelineResult(
                source=source_name,
                success=True,
                fetched_count=len(raw_data),
                transformed_count=len(transformed_data),
                loaded_count=loaded_count,
                duration=time.time() - start_time
            )
            
            logger.info(f"✓ Completed {source_name}: {len(raw_data)} fetched → {len(transformed_data)} transformed → {loaded_count} loaded")
            return result
            
        except Exception as e:
            logger.error(f"✗ Pipeline failed for {source_name}: {str(e)}", exc_info=True)
            return PipelineResult(
                source=source_name,
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    def run(self, sources: Optional[List[str]] = None, dry_run: bool = False) -> List[PipelineResult]:
        """
        Run the pipeline for all (or specified) sources.
        
        Args:
            sources: List of source names to run, or None for all sources
            dry_run: If True, only fetch and transform, don't load to database
        
        Returns:
            List of PipelineResult objects
        """
        logger.info("Starting Phase 0.5 Data Pipeline")
        logger.info(f"Configuration: {self.config}")
        logger.info(f"Sources to process: {sources or 'all'}")
        logger.info(f"Dry run: {dry_run}")
        
        self.results = []
        
        # Determine which sources to process
        sources_to_process = sources or list(self.config.sources.keys())
        
        # Create data directory if it doesn't exist
        data_dir = Path(self.config.database_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if not dry run
        if not dry_run:
            loader = loaders.SQLiteLoader(self.config.database_path)
            loader.initialize_schema()
        
        for source_name in sources_to_process:
            if source_name not in self.config.sources:
                logger.warning(f"Source '{source_name}' not found in configuration, skipping")
                continue
            
            source_config = self.config.sources[source_name]
            
            if dry_run:
                logger.info(f"DRY RUN: Processing {source_name} (skip loading)")
                try:
                    raw_data = self.fetch(source_name, source_config)
                    transformed_data = self.transform(source_name, source_config, raw_data)
                    
                    result = PipelineResult(
                        source=source_name,
                        success=True if raw_data and transformed_data else False,
                        fetched_count=len(raw_data) if raw_data else 0,
                        transformed_count=len(transformed_data) if transformed_data else 0,
                        loaded_count=0,
                        error=None if (raw_data and transformed_data) else "Dry run: no data or transformation failed",
                        duration=time.time() - start_time
                    )
                except Exception as e:
                    result = PipelineResult(
                        source=source_name,
                        success=False,
                        error=str(e),
                        duration=time.time() - start_time
                    )
            else:
                result = self.run_source(source_name, source_config)
            
            self.results.append(result)
        
        # Print summary
        self.print_summary(dry_run)
        
        return self.results
    
    def print_summary(self, dry_run: bool = False):
        """Print a summary of pipeline execution."""
        logger.info("=" * 60)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 60)
        
        if not self.results:
            logger.info("No sources processed")
            return
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        logger.info(f"Total sources: {len(self.results)}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        
        if dry_run:
            logger.info("Mode: DRY RUN (no data was saved to database)")
        
        logger.info("-" * 60)
        
        for result in self.results:
            status = "✓" if result.success else "✗"
            if result.success:
                details = f"Fetched: {result.fetched_count}, Transformed: {result.transformed_count}, Loaded: {result.loaded_count}"
                if dry_run:
                    details = f"Fetched: {result.fetched_count}, Transformed: {result.transformed_count} (dry run)"
            else:
                details = f"Error: {result.error}"
            
            logger.info(f"{status} {result.source}: {details} ({result.duration:.2f}s)")
        
        logger.info("=" * 60)
        
        if failed:
            logger.warning(f"{len(failed)} source(s) failed. Check logs for details.")
        else:
            logger.info("All sources processed successfully!")


def run_pipeline(
    config_path: Optional[str] = None,
    sources: Optional[List[str]] = None,
    dry_run: bool = False,
    verbose: bool = False
) -> List[PipelineResult]:
    """
    Convenience function to run the pipeline.
    
    Args:
        config_path: Path to configuration file (default: ~/.hageglede/config.yaml)
        sources: List of source names to run, or None for all sources
        dry_run: If True, only fetch and transform, don't load to database
        verbose: Enable verbose logging
        
    Returns:
        List of PipelineResult objects
    """
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )
    
    try:
        # Load configuration
        config = PipelineConfig.load(config_path)
        
        # Create and run pipeline
        pipeline = PipelineRunner(config)
        results = pipeline.run(sources=sources, dry_run=dry_run)
        
        return results
        
    except Exception as e:
        logger.error(f"Pipeline failed to start: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # Example usage
    print("Hageglede Pipeline Runner")
    print("Use via CLI: python -m scripts --help")
    print("\nOr programmatically:")
    print("from pipeline import run_pipeline")
    print("results = run_pipeline(sources=['vapi'], dry_run=True, verbose=True)")