#!/usr/bin/env python3
"""CLI entry point for the Hageglede data pipeline.

Usage:
    python -m scripts [OPTIONS]

Examples:
    python -m scripts --dry-run
    python -m scripts --verbose --source github
    python -m scripts --source github --source twitter
"""

import argparse
import logging
import sys

from scripts.pipeline import run_pipeline
from scripts.config import PipelineConfig


def main():
    """Parse CLI arguments and run the pipeline."""
    parser = argparse.ArgumentParser(
        description="Hageglede data pipeline: fetch, transform, and load data from various sources."
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline in dry-run mode (no database writes)."
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)."
    )
    
    parser.add_argument(
        "--source",
        action="append",
        choices=["twitter", "github", "rss", "blog", "all"],
        default=["all"],
        help="Specify which data source(s) to process. Use multiple times for multiple sources."
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="Path to configuration file (default: .env)."
    )
    
    parser.add_argument(
        "--database",
        type=str,
        help="Override database path from config."
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Process source argument
    if "all" in args.source:
        sources_to_run = ["twitter", "github", "rss", "blog"]
    else:
        sources_to_run = list(set(args.source))  # Remove duplicates
    
    print(f"🚀 Starting Hageglede pipeline")
    print(f"   Mode: {'DRY-RUN' if args.dry_run else 'PRODUCTION'}")
    print(f"   Sources: {', '.join(sources_to_run)}")
    print(f"   Config: {args.config}")
    
    try:
        # Load configuration
        config = PipelineConfig.from_env_file(args.config)
        
        # Override database path if specified
        if args.database:
            config.database_path = args.database
        
        # Run pipeline for each source
        for source in sources_to_run:
            print(f"\n📡 Processing {source} data...")
            result = run_pipeline(config, source, dry_run=args.dry_run)
            
            if result["status"] == "success":
                print(f"   ✅ {source}: {result['message']}")
                if "stats" in result:
                    stats = result["stats"]
                    if stats.get("fetched", 0) > 0:
                        print(f"      Fetched: {stats['fetched']}")
                    if stats.get("transformed", 0) > 0:
                        print(f"      Transformed: {stats['transformed']}")
                    if stats.get("loaded", 0) > 0:
                        print(f"      Loaded: {stats['loaded']}")
            else:
                print(f"   ❌ {source}: FAILED - {result['message']}")
                if "error" in result:
                    print(f"      Error: {result['error']}")
        
        print(f"\n✨ Pipeline completed successfully!")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()