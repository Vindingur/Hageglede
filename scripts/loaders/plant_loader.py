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

from src.hageglede.db.session import get_session
from src.hageglede.db.schema import Plant, Planting

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_plant_csv(file_path: str):
    """Load plant data from CSV file."""
    import csv
    
    with get_session() as session:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check if plant already exists by scientific name
                scientific_name = row.get('scientific_name') or row.get('name')
                if not scientific_name:
                    logger.warning(f"Skipping row with no scientific name: {row}")
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
                        is_pollinator_friendly=row.get('is_pollinator_friendly', '').lower() == 'true',
                        is_deer_resistant=row.get('is_deer_resistant', '').lower() == 'true',
                        is_drought_tolerant=row.get('is_drought_tolerant', '').lower() == 'true',
                        min_hardiness_zone=int(row['min_hardiness_zone']) if row.get('min_hardiness_zone') and row['min_hardiness_zone'].isdigit() else None,
                        max_hardiness_zone=int(row['max_hardiness_zone']) if row.get('max_hardiness_zone') and row['max_hardiness_zone'].isdigit() else None,
                        planting_depth_cm=float(row['planting_depth_cm']) if row.get('planting_depth_cm') else None,
                        spacing_cm=float(row['spacing_cm']) if row.get('spacing_cm') else None,
                        mature_height_cm=float(row['mature_height_cm']) if row.get('mature_height_cm') else None,
                        mature_width_cm=float(row['mature_width_cm']) if row.get('mature_width_cm') else None,
                        sun_requirements=row.get('sun_requirements'),
                        soil_type=row.get('soil_type'),
                        soil_ph_min=float(row['soil_ph_min']) if row.get('soil_ph_min') else None,
                        soil_ph_max=float(row['soil_ph_max']) if row.get('soil_ph_max') else None,
                        water_needs=row.get('water_needs'),
                        fertilizer_needs=row.get('fertilizer_needs'),
                        germination_days=int(row['germination_days']) if row.get('germination_days') and row['germination_days'].isdigit() else None,
                        time_to_maturity_days=int(row['time_to_maturity_days']) if row.get('time_to_maturity_days') and row['time_to_maturity_days'].isdigit() else None,
                        is_perennial=row.get('is_perennial', '').lower() == 'true',
                        is_annual=row.get('is_annual', '').lower() == 'true',
                        is_biennial=row.get('is_biennial', '').lower() == 'true',
                        is_vegetable=row.get('is_vegetable', '').lower() == 'true',
                        is_fruit=row.get('is_fruit', '').lower() == 'true',
                        is_herb=row.get('is_herb', '').lower() == 'true',
                        is_flower=row.get('is_flower', '').lower() == 'true',
                        edible_parts=row.get('edible_parts'),
                        harvest_season=row.get('harvest_season'),
                        companion_plants=row.get('companion_plants'),
                        antagonistic_plants=row.get('antagonistic_plants'),
                        diseases=row.get('diseases'),
                        pests=row.get('pests'),
                        propagation_methods=row.get('propagation_methods'),
                        pruning_requirements=row.get('pruning_requirements'),
                        notes=row.get('notes'),
                        source=row.get('source', 'csv'),
                        source_id=row.get('source_id')
                    )
                    session.add(plant)
                    logger.info(f"Added new plant: {scientific_name}")
                else:
                    logger.info(f"Plant already exists: {scientific_name}")
        
        session.commit()
        logger.info(f"Loaded {reader.line_num - 1} plants from {file_path}")


def load_plant_json(file_path: str):
    """Load plant data from JSON file."""
    import json
    
    with get_session() as session:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            for plant_data in data:
                # Check if plant already exists by scientific name
                scientific_name = plant_data.get('scientific_name') or plant_data.get('name')
                if not scientific_name:
                    logger.warning(f"Skipping plant data with no scientific name: {plant_data}")
                    continue
                
                plant = session.query(Plant).filter_by(scientific_name=scientific_name).first()
                if not plant:
                    # Create new plant
                    plant = Plant(
                        scientific_name=scientific_name,
                        norwegian_name=plant_data.get('norwegian_name'),
                        family=plant_data.get('family'),
                        genus=plant_data.get('genus'),
                        species=plant_data.get('species'),
                        subspecies=plant_data.get('subspecies'),
                        variety=plant_data.get('variety'),
                        common_name=plant_data.get('common_name'),
                        growth_form=plant_data.get('growth_form'),
                        is_pollinator_friendly=plant_data.get('is_pollinator_friendly', False),
                        is_deer_resistant=plant_data.get('is_deer_resistant', False),
                        is_drought_tolerant=plant_data.get('is_drought_tolerant', False),
                        min_hardiness_zone=plant_data.get('min_hardiness_zone'),
                        max_hardiness_zone=plant_data.get('max_hardiness_zone'),
                        planting_depth_cm=plant_data.get('planting_depth_cm'),
                        spacing_cm=plant_data.get('spacing_cm'),
                        mature_height_cm=plant_data.get('mature_height_cm'),
                        mature_width_cm=plant_data.get('mature_width_cm'),
                        sun_requirements=plant_data.get('sun_requirements'),
                        soil_type=plant_data.get('soil_type'),
                        soil_ph_min=plant_data.get('soil_ph_min'),
                        soil_ph_max=plant_data.get('soil_ph_max'),
                        water_needs=plant_data.get('water_needs'),
                        fertilizer_needs=plant_data.get('fertilizer_needs'),
                        germination_days=plant_data.get('germination_days'),
                        time_to_maturity_days=plant_data.get('time_to_maturity_days'),
                        is_perennial=plant_data.get('is_perennial', False),
                        is_annual=plant_data.get('is_annual', False),
                        is_biennial=plant_data.get('is_biennial', False),
                        is_vegetable=plant_data.get('is_vegetable', False),
                        is_fruit=plant_data.get('is_fruit', False),
                        is_herb=plant_data.get('is_herb', False),
                        is_flower=plant_data.get('is_flower', False),
                        edible_parts=plant_data.get('edible_parts'),
                        harvest_season=plant_data.get('harvest_season'),
                        companion_plants=plant_data.get('companion_plants'),
                        antagonistic_plants=plant_data.get('antagonistic_plants'),
                        diseases=plant_data.get('diseases'),
                        pests=plant_data.get('pests'),
                        propagation_methods=plant_data.get('propagation_methods'),
                        pruning_requirements=plant_data.get('pruning_requirements'),
                        notes=plant_data.get('notes'),
                        source=plant_data.get('source', 'json'),
                        source_id=plant_data.get('source_id')
                    )
                    session.add(plant)
                    logger.info(f"Added new plant: {scientific_name}")
                else:
                    logger.info(f"Plant already exists: {scientific_name}")
        
        session.commit()
        logger.info(f"Loaded {len(data)} plants from {file_path}")


def migrate_from_hageplan_db():
    """Migrate plant data from old hageplan.db database."""
    import sqlite3
    
    hageplan_path = Path(__file__).parent.parent.parent / 'data' / 'hageplan.db'
    if not hageplan_path.exists():
        logger.warning(f"hageplan.db not found at {hageplan_path}")
        return
    
    conn = sqlite3.connect(hageplan_path)
    cursor = conn.cursor()
    
    with get_session() as session:
        # Check for plants table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plants'")
        if not cursor.fetchone():
            logger.warning("No plants table in hageplan.db")
            return
        
        # Get column names
        cursor.execute("PRAGMA table_info(plants)")
        columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Columns in hageplan.plants: {columns}")
        
        # Fetch all plants
        cursor.execute("SELECT * FROM plants")
        for row in cursor.fetchall():
            # Map columns by name
            row_dict = dict(zip(columns, row))
            
            # Extract plant name/scientific name
            scientific_name = row_dict.get('scientific_name') or row_dict.get('name')
            if not scientific_name:
                logger.warning(f"Skipping plant with no name: {row_dict}")
                continue
            
            # Check if plant already exists
            plant = session.query(Plant).filter_by(scientific_name=scientific_name).first()
            if not plant:
                # Create new plant with basic info
                plant = Plant(
                    scientific_name=scientific_name,
                    norwegian_name=row_dict.get('norwegian_name'),
                    common_name=row_dict.get('common_name'),
                    family=row_dict.get('family'),
                    genus=row_dict.get('genus'),
                    species=row_dict.get('species'),
                    notes=row_dict.get('notes'),
                    source='hageplan_migration',
                    source_id=str(row_dict.get('id'))
                )
                session.add(plant)
                logger.info(f"Migrated plant: {scientific_name}")
            else:
                logger.info(f"Plant already exists: {scientific_name}")
        
        session.commit()
        logger.info(f"Migrated plant data from hageplan.db")


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