# PURPOSE: Main pipeline script for loading data (weather, plants) into the Hageglede database
# CONSUMED BY: scripts/__main__.py (if exists) for command-line execution
# DEPENDS ON: scripts.loaders.weather_loader, scripts.loaders.plant_loader
# TEST: none

#!/usr/bin/env python3
"""
Main pipeline for loading weather and plant data into Hageglede database.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from scripts.loaders.weather_loader import load_weather_data
from scripts.loaders.plant_loader import load_plant_data


def main():
    parser = argparse.ArgumentParser(description="Load data into Hageglede database")
    parser.add_argument("data_dir", help="Directory containing CSV files")
    parser.add_argument("database_path", help="Path to SQLite database file")
    parser.add_argument("--clear-existing", action="store_true", 
                       help="Clear existing data before loading")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    database_path = Path(args.database_path)
    clear_existing = args.clear_existing
    
    print(f"Data directory: {data_dir}")
    print(f"Database path: {database_path}")
    print(f"Clear existing: {clear_existing}")
    
    # Load weather data
    print("\n=== Loading weather data ===")
    weather_csv = data_dir / "weather.csv"
    if weather_csv.exists():
        load_weather_data(str(data_dir), str(database_path))
        print("Weather data loaded successfully")
    else:
        print(f"Warning: Weather CSV not found at {weather_csv}")
    
    # Load plant data
    print("\n=== Loading plant data ===")
    plant_csv = data_dir / "plants.csv"
    if plant_csv.exists():
        plant_df = load_plant_data(plant_csv, database_path, clear_existing)
        print(f"Plant data loaded: {len(plant_df)} records")
    else:
        print(f"Warning: Plant CSV not found at {plant_csv}")
    
    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()