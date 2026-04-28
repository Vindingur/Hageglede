# PURPOSE: Load weather data from CSV files into WeatherStation and WeatherObservation tables
# CONSUMED BY: scripts/pipeline.py
# DEPENDS ON: src/hageglede/db/schema.py
# TEST: none

import os
import csv
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

from src.hageglede.db.schema import WeatherStation, WeatherObservation


def load_weather_data(data_dir: str, database_path: str) -> None:
    """
    Load weather data from CSVs in data_dir into SQLite database.
    
    Args:
        data_dir: Directory containing weather CSV files
        database_path: Path to SQLite database file
    """
    # Map CSV field names to database column names
    WEATHER_STATION_MAP = {
        'Stasjon': 'name',
        'StasjonsID': 'station_id',
        'Latitude': 'latitude',
        'Longitude': 'longitude',
        'Elevation': 'elevation',
        'Kommunenummer': 'municipality_code'
    }
    
    WEATHER_OBSERVATION_MAP = {
        'Dato': 'date',
        'Nedbør (mm)': 'precipitation_mm',
        'Snødybde (cm)': 'snow_depth_cm',
        'Middeltemperaturen (°C)': 'avg_temperature_c',
        'Maksimumstemperatur (°C)': 'max_temperature_c',
        'Minimumstemperatur (°C)': 'min_temperature_c',
        'Middelvind (m/s)': 'avg_wind_speed_ms',
        'Maksimumvindkast (m/s)': 'max_wind_gust_ms',
        'Solskinstid (timer)': 'sunshine_hours',
        'Globalstraling (W/m²)': 'global_radiation_wm2'
    }
    
    # Connect to database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    try:
        # Process each CSV file in the data directory
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(data_dir, filename)
                print(f"Processing weather file: {filename}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    
                    station_data = {}
                    observations = []
                    
                    for row in reader:
                        # Extract station info from first row or as needed
                        if not station_data:
                            station_data = {
                                db_col: row[csv_col]
                                for csv_col, db_col in WEATHER_STATION_MAP.items()
                                if csv_col in row
                            }
                            
                            # Convert numeric fields
                            for field in ['latitude', 'longitude', 'elevation']:
                                if field in station_data:
                                    try:
                                        station_data[field] = float(station_data[field].replace(',', '.'))
                                    except (ValueError, AttributeError):
                                        station_data[field] = None
                            
                            # Insert or get station
                            cursor.execute(
                                "SELECT id FROM weather_station WHERE station_id = ?",
                                (station_data.get('station_id'),)
                            )
                            result = cursor.fetchone()
                            
                            if result:
                                station_id = result[0]
                            else:
                                cursor.execute("""
                                    INSERT INTO weather_station 
                                    (name, station_id, latitude, longitude, elevation, municipality_code)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    station_data.get('name'),
                                    station_data.get('station_id'),
                                    station_data.get('latitude'),
                                    station_data.get('longitude'),
                                    station_data.get('elevation'),
                                    station_data.get('municipality_code')
                                ))
                                station_id = cursor.lastrowid
                        
                        # Prepare observation data
                        obs = {'station_id': station_id}
                        for csv_col, db_col in WEATHER_OBSERVATION_MAP.items():
                            if csv_col in row:
                                value = row[csv_col]
                                if value:
                                    try:
                                        # Handle Norwegian decimal format
                                        value = float(value.replace(',', '.'))
                                    except ValueError:
                                        value = None
                                else:
                                    value = None
                                obs[db_col] = value
                        
                        # Parse date
                        if 'Dato' in row and row['Dato']:
                            try:
                                obs['date'] = datetime.strptime(row['Dato'], '%d.%m.%Y').date()
                            except ValueError:
                                obs['date'] = None
                        else:
                            obs['date'] = None
                        
                        observations.append(obs)
                    
                    # Insert observations in batch
                    for obs in observations:
                        cursor.execute("""
                            INSERT OR REPLACE INTO weather_observation 
                            (station_id, date, precipitation_mm, snow_depth_cm, 
                             avg_temperature_c, max_temperature_c, min_temperature_c,
                             avg_wind_speed_ms, max_wind_gust_ms, sunshine_hours,
                             global_radiation_wm2)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            obs['station_id'],
                            obs['date'],
                            obs.get('precipitation_mm'),
                            obs.get('snow_depth_cm'),
                            obs.get('avg_temperature_c'),
                            obs.get('max_temperature_c'),
                            obs.get('min_temperature_c'),
                            obs.get('avg_wind_speed_ms'),
                            obs.get('max_wind_gust_ms'),
                            obs.get('sunshine_hours'),
                            obs.get('global_radiation_wm2')
                        ))
        
        conn.commit()
        print(f"Weather data loaded successfully from {data_dir}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error loading weather data: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Test the loader with sample data
    import sys
    if len(sys.argv) == 3:
        load_weather_data(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python weather_loader.py <data_dir> <database_path>")