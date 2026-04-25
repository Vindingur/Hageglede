#!/usr/bin/env python3
"""
Plant data loader for unified gardening.db.

Loads plant data from various sources into the unified database.
Supports CSV, JSON, and SQLite input formats.
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from src.hageglede.db.session import get_session
from src.hageglede.db.schema import Plant, Planting

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_plant_data(df, database_path: str = None):
    """Load plant data from DataFrame."""
    with get_session() as session:
        for _, row in df.iterrows():
            # Check if plant already exists by scientific name
            scientific_name = row.get('scientific_name') or row.get('name')
            if not scientific_name:
                logger.warning(f"Skipping row with no scientific name: {row.to_dict()}")
                continue
            
            plant = session.query(Plant).filter_by(scientific_name=scientific_name).first()
            if not plant:
                # Create new plant
                plant = Plant(
                    scientific_name=scientific_name,
                    norwegian_name=row.get('norwegian_name'),
                    family=row.get('family'),
                    genus=row.get('genus'),
                    species=row.get('species'),
                    subspecies=row.get('subspecies'),
                    variety=row.get('variety'),
                    common_name=row.get('common_name'),
                    growth_form=row.get('growth_form'),
                    is_pollinator_friendly=bool(row.get('is_pollinator_friendly', False)),
                    is_deer_resistant=bool(row.get('is_deer_resistant', False)),
                    is_drought_tolerant=bool(row.get('is_drought_tolerant', False)),
                    min_hardiness_zone=int(row['min_hardiness_zone']) if row.get('min_hardiness_zone') and pd.notna(row['min_hardiness_zone']) else None,
                    max_hardiness_zone=int(row['max_hardiness_zone']) if row.get('max_hardiness_zone') and pd.notna(row['max_hardiness_zone']) else None,
                    planting_depth_cm=float(row['planting_depth_cm']) if row.get('planting_depth_cm') and pd.notna(row['planting_depth_cm']) else None,
                    spacing_cm=float(row['spacing_cm']) if row.get('spacing_cm') and pd.notna(row['spacing_cm']) else None,
                    mature_height_cm=float(row['mature_height_cm']) if row.get('mature_height_cm') and pd.notna(row['mature_height_cm']) else None,
                    mature_width_cm=float(row['mature_width_cm']) if row.get('mature_width_cm') and pd.notna(row['mature_width_cm']) else None,
                    sun_requirements=row.get('sun_requirements'),
                    soil_type=row.get('soil_type'),
                    soil_ph_min=float(row['soil_ph_min']) if row.get('soil_ph_min') and pd.notna(row['soil_ph_min']) else None,
                    soil_ph_max=float(row['soil_ph_max']) if row.get('soil_ph_max') and pd.notna(row['soil_ph_max']) else None,
                    water_needs=row.get('water_needs'),
                    fertilizer_needs=row.get('fertilizer_needs'),
                    germination_days=int(row['germination_days']) if row.get('germination_days') and pd.notna(row['germination_days']) else None,
                    time_to_maturity_days=int(row['time_to_maturity_days']) if row.get('time_to_maturity_days') and pd.notna(row['time_to_maturity_days']) else None,
                    is_perennial=bool(row.get('is_perennial', False)),
                    is_annual=bool(row.get('is_annual', False)),
                    is_biennial=bool(row.get('is_biennial', False)),
                    is_vegetable=bool(row.get('is_vegetable', False)),
                    is_fruit=bool(row.get('is_fruit', False)),
                    is_herb=bool(row.get('is_herb', False)),
                    is_flower=bool(row.get('is_flower', False)),
                    edible_parts=row.get('edible_parts'),
                    harvest_season=row.get('harvest_season'),
                    companion_plants=row.get('companion_plants'),
                    antagonistic_plants=row.get('antagonistic_plants'),
                    diseases=row.get('diseases'),
                    pests=row.get('pests'),
                    propagation_methods=row.get('propagation_methods'),
                    pruning_requirements=row.get('pruning_requirements'),
                    notes=row.get('notes'),
                    source=row.get('source', 'pipeline'),
                    source_id=row.get('source_id')
                )
                session.add(plant)
                logger.info(f"Added new plant: {scientific_name}")
            else:
                logger.info(f"Plant already exists: {scientific_name}")
        
        session.commit()
        logger.info(f"Loaded {len(df)} plants from DataFrame")


def load_plant_csv(file_path: str):
    """Load plant data from CSV file."""
    # Read CSV using pandas to convert to DataFrame
    df = pd.read_csv(file_path)
    load_plant_data(df)


def load_plant_json(file_path: str):
    """Load plant data from JSON file."""
    import json
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    load_plant_data(df)


def migrate_from_hageplan_db():
    """Migrate plant data from old hageplan.db database."""
    import sqlite3
    
    hageplan_path = Path(__file__).parent.parent.parent / 'data' / 'hageplan.db'
    if not hageplan_path.exists():
        logger.warning(f"hageplan.db not found at {hageplan_path}")
        return
    
    conn = sqlite3.connect(hageplan_path)
    
    try:
        # Check for plants table
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plants'")
        if not cursor.fetchone():
            logger.warning("No plants table in hageplan.db")
            return
        
        # Read data into DataFrame
        df = pd.read_sql_query("SELECT * FROM plants", conn)
        
        # Add source column
        df['source'] = 'hageplan_migration'
        
        # Load data
        load_plant_data(df)
        
        logger.info(f"Migrated {len(df)} plants from hageplan.db")
        
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Load plant data into unified gardening.db')
    parser.add_argument('--csv', help='Path to CSV file with plant data')
    parser.add_argument('--json', help='Path to JSON file with plant data')
    parser.add_argument('--migrate-hageplan', action='store_true', 
                       help='Migrate data from old hageplan.db')
    
    args = parser.parse_args()
    
    if args.csv:
        load_plant_csv(args.csv)
    elif args.json:
        load_plant_json(args.json)
    elif args.migrate_hageplan:
        migrate_from_hageplan_db()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()