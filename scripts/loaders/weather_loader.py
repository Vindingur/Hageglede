#!/usr/bin/env python3
"""
Weather data loader module for Aletheia plant database.

Downloads historical weather data from OpenWeatherMap API and loads it into the database.

DEPENDENCIES:
    - openweathermap_api_key in config.ini or environment
    - sqlite3 (stdlib)
    - requests (external)
    - configparser (stdlib)

DATA SOURCES:
    - OpenWeatherMap historical API
    - Requires lat/lon coordinates per plant

TIMEFRAME: Past 1 year (approx 365 days)
FREQUENCY: Daily (24h aggregated)

USAGE:
    from scripts.loaders import load_weather_data
    load_weather_data(lat=52.5200, lon=13.4050, location_name="Berlin")

CLASSES:
    None - functions only
"""

import sqlite3
import requests
import configparser
import os
import json
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_api_key():
    """
    Retrieve OpenWeatherMap API key from config.ini or environment.
    
    Returns:
        str: API key or raises ValueError if not found
    """
    config = configparser.ConfigParser()
    
    # Try config.ini first
    if os.path.exists('config.ini'):
        config.read('config.ini')
        if 'openweathermap' in config and 'api_key' in config['openweathermap']:
            return config['openweathermap']['api_key']
    
    # Fallback to environment variable
    env_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    if env_key:
        return env_key
    
    raise ValueError(
        "OpenWeatherMap API key not found. "
        "Add openweathermap_api_key to config.ini under [openweathermap] section "
        "or set OPENWEATHERMAP_API_KEY environment variable."
    )

def fetch_historical_weather(lat, lon, api_key, days_back=365):
    """
    Fetch historical weather data from OpenWeatherMap API.
    
    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
        api_key (str): OpenWeatherMap API key
        days_back (int): Number of days to go back (default: 365)
    
    Returns:
        list: List of daily weather records
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # API endpoint (One Call API 3.0 historical)
    # Note: OpenWeatherMap One Call API requires timestamps
    # We'll make monthly requests to stay within typical rate limits
    all_data = []
    
    current = start_date
    while current < end_date:
        next_month = current + timedelta(days=30)
        if next_month > end_date:
            next_month = end_date
        
        # Convert to UNIX timestamp
        start_ts = int(current.timestamp())
        end_ts = int(next_month.timestamp())
        
        url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine"
        params = {
            'lat': lat,
            'lon': lon,
            'dt': start_ts,
            'appid': api_key,
            'units': 'metric'  # Celsius, meters/sec, etc.
        }
        
        try:
            logger.info(f"Fetching weather for {current.date()} to {next_month.date()}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data:
                all_data.extend(data['data'])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch weather data for {current.date()}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response for {current.date()}: {e}")
        
        # Move to next period
        current = next_month
        
        # Rate limiting - be gentle
        import time
        time.sleep(1)
    
    return all_data

def transform_weather_data(raw_data, location_name):
    """
    Transform raw API data into database-friendly format.
    
    Args:
        raw_data (list): List of raw weather records from API
        location_name (str): Name of the location
    
    Returns:
        list: List of transformed weather records
    """
    transformed = []
    
    for record in raw_data:
        # Convert UNIX timestamp to datetime
        dt = datetime.fromtimestamp(record['dt'])
        
        # Extract main weather metrics
        transformed.append({
            'timestamp': dt.isoformat(),
            'location_name': location_name,
            'temperature_c': record.get('temp', {}).get('day', None) if isinstance(record.get('temp'), dict) else record.get('temp'),
            'feels_like_c': record.get('feels_like', {}).get('day', None) if isinstance(record.get('feels_like'), dict) else record.get('feels_like'),
            'pressure_hpa': record.get('pressure', None),
            'humidity_percent': record.get('humidity', None),
            'dew_point_c': record.get('dew_point', None),
            'clouds_percent': record.get('clouds', None),
            'visibility_m': record.get('visibility', None),
            'wind_speed_mps': record.get('wind_speed', None),
            'wind_deg': record.get('wind_deg', None),
            'weather_main': record.get('weather', [{}])[0].get('main', None),
            'weather_description': record.get('weather', [{}])[0].get('description', None),
            'rain_mm': record.get('rain', None),
            'snow_mm': record.get('snow', None),
            'uvi': record.get('uvi', None),
            'sunrise': datetime.fromtimestamp(record['sunrise']).isoformat() if 'sunrise' in record else None,
            'sunset': datetime.fromtimestamp(record['sunset']).isoformat() if 'sunset' in record else None
        })
    
    return transformed

def create_weather_table_if_not_exists(db_path='data/aletheia.db'):
    """
    Create weather table if it doesn't exist.
    
    Args:
        db_path (str): Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weather_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        location_name TEXT NOT NULL,
        temperature_c REAL,
        feels_like_c REAL,
        pressure_hpa REAL,
        humidity_percent INTEGER,
        dew_point_c REAL,
        clouds_percent INTEGER,
        visibility_m INTEGER,
        wind_speed_mps REAL,
        wind_deg INTEGER,
        weather_main TEXT,
        weather_description TEXT,
        rain_mm REAL,
        snow_mm REAL,
        uvi REAL,
        sunrise TEXT,
        sunset TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(timestamp, location_name)
    )
    ''')
    
    # Create index for faster queries by location and date
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_weather_location_date 
    ON weather_data (location_name, timestamp)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Weather table created/verified")

def load_weather_data(lat, lon, location_name, db_path='data/aletheia.db'):
    """
    Main function to load weather data for a location.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        location_name (str): Human-readable location name
        db_path (str): Path to SQLite database
    
    Returns:
        int: Number of records inserted
    """
    logger.info(f"Loading weather data for {location_name} ({lat}, {lon})")
    
    # Get API key
    try:
        api_key = get_api_key()
    except ValueError as e:
        logger.error(str(e))
        return 0
    
    # Fetch data
    raw_data = fetch_historical_weather(lat, lon, api_key)
    if not raw_data:
        logger.warning(f"No weather data fetched for {location_name}")
        return 0
    
    # Transform data
    weather_records = transform_weather_data(raw_data, location_name)
    logger.info(f"Transformed {len(weather_records)} weather records")
    
    # Ensure table exists
    create_weather_table_if_not_exists(db_path)
    
    # Insert data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inserted_count = 0
    for record in weather_records:
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO weather_data (
                timestamp, location_name, temperature_c, feels_like_c,
                pressure_hpa, humidity_percent, dew_point_c, clouds_percent,
                visibility_m, wind_speed_mps, wind_deg, weather_main,
                weather_description, rain_mm, snow_mm, uvi, sunrise, sunset
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['timestamp'], record['location_name'],
                record['temperature_c'], record['feels_like_c'],
                record['pressure_hpa'], record['humidity_percent'],
                record['dew_point_c'], record['clouds_percent'],
                record['visibility_m'], record['wind_speed_mps'],
                record['wind_deg'], record['weather_main'],
                record['weather_description'], record['rain_mm'],
                record['snow_mm'], record['uvi'], record['sunrise'],
                record['sunset']
            ))
            
            if cursor.rowcount > 0:
                inserted_count += 1
                
        except sqlite3.Error as e:
            logger.error(f"Failed to insert weather record {record['timestamp']}: {e}")
    
    conn.commit()
    
    # Log some statistics
    cursor.execute('''
    SELECT 
        COUNT(*) as total_records,
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        AVG(temperature_c) as avg_temp
    FROM weather_data 
    WHERE location_name = ?
    ''', (location_name,))
    
    stats = cursor.fetchone()
    logger.info(
        f"Weather data for {location_name}: "
        f"{stats[0]} total records, "
        f"from {stats[1]} to {stats[2]}, "
        f"average temperature: {stats[3]:.1f}°C"
    )
    
    conn.close()
    
    logger.info(f"Inserted {inserted_count} new weather records for {location_name}")
    return inserted_count

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) >= 4:
        lat = float(sys.argv[1])
        lon = float(sys.argv[2])
        location = sys.argv[3]
        load_weather_data(lat, lon, location)
    else:
        print("Usage: python weather_loader.py <lat> <lon> <location_name>")
        print("Example: python weather_loader.py 52.5200 13.4050 \"Berlin\"")