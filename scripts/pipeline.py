#!/usr/bin/env python3

"""
Main ETL pipeline for Hageglede data processing.
Coordinates fetching data from various sources, saving to data lake,
and loading into PostgreSQL.
"""

# PURPOSE: Main ETL pipeline coordinating data fetching, processing, and loading from multiple sources including GBIF and Artsdatabanken
# CONSUMED BY: CLI commands, deployment scripts, scheduled jobs
# DEPENDS ON: scripts.fetchers.gbif, scripts.fetchers.artsdatabanken, scripts.utils.data_lake, scripts.utils.postgres

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fetchers.gbif import fetch_norwegian_plant_occurrences
from scripts.fetchers.artsdatabanken import ArtsdatabankenClient
from scripts.utils.data_lake import DataLake
from scripts.utils.postgres import PostgresLoader


def fetch_and_save_data(start_date: str, end_date: str, data_dir: str = "data"):
    """
    Fetch data from all sources and save to the data lake.
    
    Args:
        start_date: Start date for data fetch (YYYY-MM-DD)
        end_date: End date for data fetch (YYYY-MM-DD)
        data_dir: Directory for data lake storage
    """
    print(f"🔁 Starting data fetch from {start_date} to {end_date}")
    
    # Initialize data lake
    data_lake = DataLake(base_path=data_dir)
    
    # Fetch and save GBIF data
    print("📥 Fetching GBIF data...")
    gbif_data = fetch_norwegian_plant_occurrences(start_date=start_date, end_date=end_date)
    if gbif_data is not None and len(gbif_data) > 0:
        # Convert to DataFrame for consistency with other data sources
        import pandas as pd
        gbif_df = pd.DataFrame(gbif_data)
        
        gbif_path = data_lake.save_dataframe(
            gbif_df, 
            source="gbif", 
            data_type="occurrences",
            timestamp=datetime.now()
        )
        print(f"✅ GBIF data saved to {gbif_path}")
    else:
        print("⚠️  No GBIF data fetched")
    
    # Fetch and save Artsdatabanken data
    print("📥 Fetching Artsdatabanken data...")
    arts_client = ArtsdatabankenClient()
    
    # Fetch plant species list
    plant_species = arts_client.get_plant_species()
    if plant_species is not None and not plant_species.empty:
        species_path = data_lake.save_dataframe(
            plant_species,
            source="artsdatabanken",
            data_type="species_list",
            timestamp=datetime.now()
        )
        print(f"✅ Artsdatabanken species list saved to {species_path}")
    else:
        print("⚠️  No Artsdatabanken species data fetched")
    
    # Optionally fetch detailed data for all plants
    # This might take a while and make many API calls
    print("📥 Fetching detailed plant data from Artsdatabanken...")
    all_plants = arts_client.fetch_all_plants()
    if all_plants is not None and not all_plants.empty:
        plants_path = data_lake.save_dataframe(
            all_plants,
            source="artsdatabanken",
            data_type="detailed_plants",
            timestamp=datetime.now()
        )
        print(f"✅ Artsdatabanken detailed plant data saved to {plants_path}")
    else:
        print("⚠️  No detailed Artsdatabanken plant data fetched")
    
    print("✅ Data fetch complete!")
    return True


def load_to_postgres(data_dir: str = "data", clear_existing: bool = False):
    """
    Load data from data lake into PostgreSQL.
    
    Args:
        data_dir: Directory containing data lake
        clear_existing: Whether to clear existing tables before loading
    """
    print("🗄️  Loading data to PostgreSQL...")
    
    # Initialize data lake and loader
    data_lake = DataLake(base_path=data_dir)
    loader = PostgresLoader()
    
    try:
        # Load GBIF occurrences
        gbif_files = data_lake.find_files(source="gbif", data_type="occurrences")
        for file_path in gbif_files:
            print(f"📤 Loading GBIF data from {file_path.name}...")
            loader.load_gbif_occurrences(str(file_path), clear_existing=clear_existing)
            clear_existing = False  # Only clear first time
        
        # Load Artsdatabanken species list
        species_files = data_lake.find_files(source="artsdatabanken", data_type="species_list")
        for file_path in species_files:
            print(f"📤 Loading Artsdatabanken species from {file_path.name}...")
            loader.load_artsdatabanken_species(str(file_path), clear_existing=clear_existing)
        
        # Load Artsdatabanken detailed plants
        plant_files = data_lake.find_files(source="artsdatabanken", data_type="detailed_plants")
        for file_path in plant_files:
            print(f"📤 Loading Artsdatabanken detailed plants from {file_path.name}...")
            loader.load_artsdatabanken_plants(str(file_path), clear_existing=clear_existing)
        
        print("✅ PostgreSQL loading complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading to PostgreSQL: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Hageglede ETL Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch data from sources")
    fetch_parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    fetch_parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    fetch_parser.add_argument("--data-dir", default="data", help="Data directory")
    
    # Load command
    load_parser = subparsers.add_parser("load", help="Load data to PostgreSQL")
    load_parser.add_argument("--data-dir", default="data", help="Data directory")
    load_parser.add_argument("--clear-existing", action="store_true", 
                           help="Clear existing data before loading")
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser("run", help="Run full ETL pipeline")
    pipeline_parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    pipeline_parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    pipeline_parser.add_argument("--data-dir", default="data", help="Data directory")
    pipeline_parser.add_argument("--no-clear", action="store_true", 
                               help="Don't clear existing PostgreSQL data")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        success = fetch_and_save_data(args.start_date, args.end_date, args.data_dir)
        sys.exit(0 if success else 1)
        
    elif args.command == "load":
        success = load_to_postgres(args.data_dir, args.clear_existing)
        sys.exit(0 if success else 1)
        
    elif args.command == "run":
        print("🚀 Running full ETL pipeline...")
        
        # Fetch data
        fetch_success = fetch_and_save_data(args.start_date, args.end_date, args.data_dir)
        if not fetch_success:
            print("❌ Fetch phase failed, aborting pipeline")
            sys.exit(1)
        
        # Load to PostgreSQL
        clear_existing = not args.no_clear
        load_success = load_to_postgres(args.data_dir, clear_existing)
        sys.exit(0 if load_success else 1)
        
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()