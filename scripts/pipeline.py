#!/usr/bin/env python3

"""
Main ETL pipeline for Hageglede data processing.
Coordinates fetching data from various sources, saving to data lake,
and loading into PostgreSQL.
"""

# PURPOSE: Main ETL pipeline coordinating data fetching, processing, and loading from multiple sources including GBIF and Artsdatabanken
# CONSUMED BY: CLI commands, deployment scripts, scheduled jobs
# DEPENDS ON: scripts.fetchers.gbif, scripts.fetchers.artsdatabanken, scripts.loaders.plant_loader, scripts.loaders.weather_loader

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fetchers.gbif import fetch_norwegian_plant_occurrences
from scripts.fetchers.artsdatabanken import ArtsdatabankenClient
from scripts.loaders.plant_loader import load_plant_data
from scripts.loaders.weather_loader import load_weather_data


def fetch_and_save_data(start_date: str, end_date: str, data_dir: str = "data"):
    """
    Fetch data from all sources and save to the data lake.
    
    Args:
        start_date: Start date for data fetch (YYYY-MM-DD)
        end_date: End date for data fetch (YYYY-MM-DD)
        data_dir: Directory for data lake storage
    """
    print(f"🔁 Starting data fetch from {start_date} to {end_date}")
    
    # Fetch and save GBIF data
    print("📥 Fetching GBIF data...")
    gbif_data = fetch_norwegian_plant_occurrences(start_date=start_date, end_date=end_date)
    if gbif_data is not None and len(gbif_data) > 0:
        # Convert to DataFrame for consistency with other data sources
        import pandas as pd
        gbif_df = pd.DataFrame(gbif_data)
        
        # Save to CSV directly
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gbif_path = Path(data_dir) / f"gbif_occurrences_{timestamp}.csv"
        gbif_path.parent.mkdir(parents=True, exist_ok=True)
        gbif_df.to_csv(gbif_path, index=False)
        print(f"✅ GBIF data saved to {gbif_path}")
    else:
        print("⚠️  No GBIF data fetched")
    
    # Fetch and save Artsdatabanken data
    print("📥 Fetching Artsdatabanken data...")
    arts_client = ArtsdatabankenClient()
    
    # Fetch plant species list
    plant_species = arts_client.get_plant_species()
    if plant_species is not None and not plant_species.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        species_path = Path(data_dir) / f"artsdatabanken_species_{timestamp}.csv"
        species_path.parent.mkdir(parents=True, exist_ok=True)
        plant_species.to_csv(species_path, index=False)
        print(f"✅ Artsdatabanken species list saved to {species_path}")
    else:
        print("⚠️  No Artsdatabanken species data fetched")
    
    # Optionally fetch detailed data for all plants
    # This might take a while and make many API calls
    print("📥 Fetching detailed plant data from Artsdatabanken...")
    all_plants = arts_client.fetch_all_plants()
    if all_plants is not None and not all_plants.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plants_path = Path(data_dir) / f"artsdatabanken_detailed_plants_{timestamp}.csv"
        plants_path.parent.mkdir(parents=True, exist_ok=True)
        all_plants.to_csv(plants_path, index=False)
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
    
    try:
        # Load plant data using the new plant_loader
        print("📤 Loading plant data...")
        load_plant_data(data_dir, clear_existing=clear_existing)
        
        # Load weather data using the new weather_loader
        print("📤 Loading weather data...")
        load_weather_data(data_dir, clear_existing=clear_existing)
        
        # Find and load GBIF data files
        data_path = Path(data_dir)
        if data_path.exists():
            import pandas as pd
            for file_path in data_path.glob("gbif_occurrences_*.csv"):
                print(f"📤 Loading GBIF data from {file_path.name}...")
                df = pd.read_csv(file_path)
                
                # TODO: Add GBIF loading logic here
                # For now just count records
                print(f"   Found {len(df)} GBIF occurrence records")
        
        print("✅ PostgreSQL loading complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading to PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
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