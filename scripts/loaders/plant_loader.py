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

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.hageglede.db.session import get_session
from src.hageglede.db.schema import Plant, Species, Planting

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_plant_csv(file_path: str):
    """Load plant data from CSV file."""
    import csv
    from datetime import datetime
    
    with get_session() as session:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Create or get species
                species = session.query(Species).filter_by(name=row.get('species')).first()
                if not species:
                    species = Species(
                        name=row.get('species'),
                        family=row.get('family'),
                        perennial=row.get('perennial', '').lower() == 'true'
                    )
                    session.add(species)
                    session.flush()
                
                # Create plant
                plant = Plant(
                    species_id=species.id,
                    planting_date=datetime.strptime(row.get('planting_date'), '%Y-%m-%d').date() if row.get('planting_date') else None,
                    harvest_date=datetime.strptime(row.get('harvest_date'), '%Y-%m-%d').date() if row.get('harvest_date') else None,
                    yield_kg=float(row.get('yield_kg')) if row.get('yield_kg') else None,
                    notes=row.get('notes')
                )
                session.add(plant)
        
        session.commit()
        logger.info(f"Loaded {reader.line_num - 1} plants from {file_path}")


def load_plant_json(file_path: str):
    """Load plant data from JSON file."""
    import json
    from datetime import datetime
    
    with get_session() as session:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            for plant_data in data:
                # Handle species
                species_data = plant_data.get('species', {})
                species = session.query(Species).filter_by(name=species_data.get('name')).first()
                if not species:
                    species = Species(
                        name=species_data.get('name'),
                        family=species_data.get('family'),
                        perennial=species_data.get('perennial', False)
                    )
                    session.add(species)
                    session.flush()
                
                # Create plant
                planting_date = plant_data.get('planting_date')
                harvest_date = plant_data.get('harvest_date')
                
                plant = Plant(
                    species_id=species.id,
                    planting_date=datetime.strptime(planting_date, '%Y-%m-%d').date() if planting_date else None,
                    harvest_date=datetime.strptime(harvest_date, '%Y-%m-%d').date() if harvest_date else None,
                    yield_kg=plant_data.get('yield_kg'),
                    notes=plant_data.get('notes')
                )
                session.add(plant)
        
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
        
        # Fetch all plants
        cursor.execute("SELECT * FROM plants")
        for row in cursor.fetchall():
            # Assuming columns: id, name, species, planting_date, harvest_date, yield, notes
            plant_name = row[1] if len(row) > 1 else None
            species_name = row[2] if len(row) > 2 else None
            
            if not species_name:
                species_name = plant_name
            
            # Create or get species
            species = session.query(Species).filter_by(name=species_name).first()
            if not species:
                species = Species(name=species_name)
                session.add(species)
                session.flush()
            
            # Create plant
            planting_date = row[3] if len(row) > 3 else None
            harvest_date = row[4] if len(row) > 4 else None
            yield_kg = row[5] if len(row) > 5 else None
            notes = row[6] if len(row) > 6 else None
            
            plant = Plant(
                species_id=species.id,
                planting_date=datetime.strptime(planting_date, '%Y-%m-%d').date() if planting_date else None,
                harvest_date=datetime.strptime(harvest_date, '%Y-%m-%d').date() if harvest_date else None,
                yield_kg=float(yield_kg) if yield_kg else None,
                notes=notes
            )
            session.add(plant)
        
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