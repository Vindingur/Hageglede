#!/usr/bin/env python3
"""
Weather loader for unified gardening.db.

Loads weather data from CSV files or weather API into the unified database.
"""

import csv
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.hageglede.db.session import SessionLocal
from src.hageglede.db.schema import WeatherObservation, Location

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_weather_from_csv(csv_path: Path) -> int:
    """
    Load weather data from a CSV file.
    
    CSV format expected:
        date,temperature_min,temperature_max,precipitation,humidity,wind_speed,sun_hours,location_id
    
    Returns number of records loaded.
    """
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return 0
    
    db = SessionLocal()
    loaded_count = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse date
                    date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    
                    # Parse numeric values (handle empty strings)
                    temperature_min = float(row['temperature_min']) if row['temperature_min'] else None
                    temperature_max = float(row['temperature_max']) if row['temperature_max'] else None
                    precipitation = float(row['precipitation']) if row['precipitation'] else None
                    humidity = float(row['humidity']) if row['humidity'] else None
                    wind_speed = float(row['wind_speed']) if row['wind_speed'] else None
                    sun_hours = float(row['sun_hours']) if row['sun_hours'] else None
                    
                    location_id = int(row['location_id']) if row['location_id'] else None
                    
                    # Check if record already exists
                    existing = db.query(WeatherObservation).filter_by(
                        date=date,
                        location_id=location_id
                    ).first()
                    
                    if existing:
                        logger.debug(f"Weather record already exists for {date} at location {location_id}")
                        continue
                    
                    # Create new record
                    weather = WeatherObservation(
                        date=date,
                        temperature_min=temperature_min,
                        temperature_max=temperature_max,
                        precipitation=precipitation,
                        humidity=humidity,
                        wind_speed=wind_speed,
                        sun_hours=sun_hours,
                        location_id=location_id
                    )
                    
                    db.add(weather)
                    loaded_count += 1
                    
                    if loaded_count % 100 == 0:
                        logger.info(f"Loaded {loaded_count} weather records...")
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing row: {row}. Error: {e}")
                    continue
        
        db.commit()
        logger.info(f"Successfully loaded {loaded_count} weather records from {csv_path}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading weather data: {e}")
        raise
    finally:
        db.close()
    
    return loaded_count


def create_weather_record(
    date: str,
    temperature_min: Optional[float] = None,
    temperature_max: Optional[float] = None,
    precipitation: Optional[float] = None,
    humidity: Optional[float] = None,
    wind_speed: Optional[float] = None,
    sun_hours: Optional[float] = None,
    location_id: Optional[int] = None,
    location_name: Optional[str] = None
) -> Optional[WeatherObservation]:
    """
    Create a single weather record in the database.
    
    Args:
        date: Date string in YYYY-MM-DD format
        temperature_min: Minimum temperature in °C
        temperature_max: Maximum temperature in °C
        precipitation: Precipitation in mm
        humidity: Relative humidity in %
        wind_speed: Wind speed in m/s
        sun_hours: Sunshine hours
        location_id: Location ID (optional if location_name provided)
        location_name: Location name (used if location_id not provided)
    
    Returns:
        Created WeatherObservation object or None if failed
    """
    db = SessionLocal()
    
    try:
        # Parse date
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get location_id from name if not provided
        if location_id is None and location_name:
            location = db.query(Location).filter_by(name=location_name).first()
            if location:
                location_id = location.id
            else:
                logger.error(f"Location '{location_name}' not found")
                return None
        
        # Check if record already exists
        existing = db.query(WeatherObservation).filter_by(
            date=date_obj,
            location_id=location_id
        ).first()
        
        if existing:
            logger.info(f"Weather record already exists for {date} at location {location_id}")
            return existing
        
        # Create new record
        weather = WeatherObservation(
            date=date_obj,
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            precipitation=precipitation,
            humidity=humidity,
            wind_speed=wind_speed,
            sun_hours=sun_hours,
            location_id=location_id
        )
        
        db.add(weather)
        db.commit()
        logger.info(f"Created weather record for {date}")
        
        return weather
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating weather record: {e}")
        return None
    finally:
        db.close()


def get_weather_for_period(
    start_date: str,
    end_date: str,
    location_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get weather data for a specific period.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        location_id: Optional location ID filter
    
    Returns:
        List of weather records as dictionaries
    """
    db = SessionLocal()
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        query = db.query(WeatherObservation).filter(
            WeatherObservation.date >= start,
            WeatherObservation.date <= end
        )
        
        if location_id:
            query = query.filter_by(location_id=location_id)
        
        weather_data = query.order_by(WeatherObservation.date).all()
        
        result = []
        for w in weather_data:
            result.append({
                'date': w.date.isoformat(),
                'temperature_min': w.temperature_min,
                'temperature_max': w.temperature_max,
                'precipitation': w.precipitation,
                'humidity': w.humidity,
                'wind_speed': w.wind_speed,
                'sun_hours': w.sun_hours,
                'location_id': w.location_id
            })
        
        return result
        
    finally:
        db.close()


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load weather data into unified gardening.db')
    parser.add_argument('--csv', type=Path, help='Path to CSV file with weather data')
    parser.add_argument('--date', help='Date (YYYY-MM-DD) for single record')
    parser.add_argument('--temp-min', type=float, help='Minimum temperature (°C)')
    parser.add_argument('--temp-max', type=float, help='Maximum temperature (°C)')
    parser.add_argument('--precipitation', type=float, help='Precipitation (mm)')
    parser.add_argument('--location', help='Location name or ID')
    
    args = parser.parse_args()
    
    if args.csv:
        count = load_weather_from_csv(args.csv)
        print(f"Loaded {count} weather records")
    elif args.date:
        # Try to parse location as ID first, then as name
        location_id = None
        location_name = None
        
        if args.location:
            try:
                location_id = int(args.location)
            except ValueError:
                location_name = args.location
        
        weather = create_weather_record(
            date=args.date,
            temperature_min=args.temp_min,
            temperature_max=args.temp_max,
            precipitation=args.precipitation,
            location_id=location_id,
            location_name=location_name
        )
        
        if weather:
            print(f"Created weather record for {args.date}")
        else:
            print("Failed to create weather record")
    else:
        print("Please provide either --csv or --date argument")
        parser.print_help()


if __name__ == '__main__':
    main()