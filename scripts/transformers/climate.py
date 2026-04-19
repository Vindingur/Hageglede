"""
Transform raw climate/weather data into SQLite schema.
"""
import pandas as pd
from typing import Dict, List, Any, Optional


def transform_met_climate_data(raw_data: List[Dict]) -> pd.DataFrame:
    """
    Transform MET Frost API climate data into normalized schema.
    
    Args:
        raw_data: List of climate observations from MET Frost API
        
    Returns:
        DataFrame with columns:
        - station_id: MET station identifier
        - station_name: Name of weather station
        - latitude: Station latitude
        - longitude: Station longitude  
        - elevation: Station elevation (m)
        - element_id: Climate element code (e.g., 'mean_temperature', 'precipitation')
        - element_name: Human-readable element name
        - value: Measured value
        - unit: Measurement unit
        - time_from: Start of measurement period (ISO format)
        - time_to: End of measurement period (ISO format)
        - source_time: When data was recorded
        - retrieval_time: When data was fetched
    """
    if not raw_data:
        return pd.DataFrame()
    
    records = []
    
    for obs in raw_data:
        station_info = obs.get('source', {})
        reference_time = obs.get('referenceTime', '')
        
        for data in obs.get('observations', []):
            element = data.get('elementId', '')
            
            # Map MET element IDs to human-readable names
            element_map = {
                'air_temperature': 'Air Temperature',
                'mean(air_temperature P1D)': 'Daily Mean Air Temperature',
                'precipitation_amount': 'Precipitation Amount',
                'sum(precipitation_amount P1D)': 'Daily Precipitation Sum',
                'wind_speed': 'Wind Speed',
                'mean(wind_speed PT10M)': '10-min Mean Wind Speed',
                'relative_humidity': 'Relative Humidity',
                'mean(relative_humidity PT10M)': '10-min Mean Relative Humidity',
                'air_pressure_at_sea_level': 'Air Pressure at Sea Level',
                'surface_air_pressure': 'Surface Air Pressure',
                'cloud_area_fraction': 'Cloud Cover',
                'mean(cloud_area_fraction P1D)': 'Daily Mean Cloud Cover'
            }
            
            element_name = element_map.get(element, element.replace('_', ' ').title())
            
            record = {
                'station_id': station_info.get('id', ''),
                'station_name': station_info.get('name', ''),
                'latitude': station_info.get('geometry', {}).get('coordinates', [None, None])[1],
                'longitude': station_info.get('geometry', {}).get('coordinates', [None, None])[0],
                'elevation': station_info.get('geometry', {}).get('coordinates', [None, None, None])[2] if len(station_info.get('geometry', {}).get('coordinates', [])) > 2 else None,
                'element_id': element,
                'element_name': element_name,
                'value': data.get('value'),
                'unit': data.get('unit', ''),
                'time_from': data.get('timeOffset', ''),
                'time_to': data.get('timeResolution', ''),
                'level': data.get('level', {}),
                'source_time': reference_time,
                'retrieval_time': pd.Timestamp.now().isoformat()
            }
            records.append(record)
    
    df = pd.DataFrame(records)
    
    # Convert numeric columns
    numeric_cols = ['latitude', 'longitude', 'elevation', 'value']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert timestamp columns
    time_cols = ['source_time', 'retrieval_time']
    for col in time_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df


def transform_climate_zones(raw_zones: List[Dict]) -> pd.DataFrame:
    """
    Transform climate zone/region data into normalized schema.
    
    Args:
        raw_zones: List of climate zone definitions
        
    Returns:
        DataFrame with columns:
        - zone_id: Climate zone identifier
        - zone_name: Climate zone name
        - zone_type: Type of zone (e.g., 'hardiness', 'precipitation', 'temperature')
        - description: Zone description
        - min_value: Minimum value for zone (e.g., min temperature)
        - max_value: Maximum value for zone (e.g., max temperature)
        - unit: Unit of measurement
        - geometry: GeoJSON geometry (optional)
        - source: Data source
    """
    if not raw_zones:
        return pd.DataFrame()
    
    records = []
    
    for zone in raw_zones:
        record = {
            'zone_id': zone.get('id', ''),
            'zone_name': zone.get('name', ''),
            'zone_type': zone.get('type', ''),
            'description': zone.get('description', ''),
            'min_value': zone.get('min_value'),
            'max_value': zone.get('max_value'),
            'unit': zone.get('unit', ''),
            'geometry': zone.get('geometry'),
            'source': zone.get('source', ''),
            'retrieval_time': pd.Timestamp.now().isoformat()
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # Convert numeric columns
    numeric_cols = ['min_value', 'max_value']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert timestamp
    if 'retrieval_time' in df.columns:
        df['retrieval_time'] = pd.to_datetime(df['retrieval_time'])
    
    return df


def normalize_climate_data_for_sqlite(climate_df: pd.DataFrame, zones_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Prepare climate data for SQLite loading.
    
    Args:
        climate_df: DataFrame from transform_met_climate_data
        zones_df: DataFrame from transform_climate_zones
        
    Returns:
        Dictionary of DataFrames ready for SQLite:
        - 'climate_stations': Station metadata
        - 'climate_observations': Climate measurements
        - 'climate_zones': Climate zone definitions
    """
    result = {}
    
    # Climate stations
    if not climate_df.empty:
        stations_df = climate_df[['station_id', 'station_name', 'latitude', 'longitude', 'elevation']].drop_duplicates('station_id')
        stations_df = stations_df.reset_index(drop=True)
        result['climate_stations'] = stations_df
    
    # Climate observations
    if not climate_df.empty:
        obs_cols = ['station_id', 'element_id', 'element_name', 'value', 'unit', 
                   'time_from', 'time_to', 'source_time', 'retrieval_time']
        obs_df = climate_df[obs_cols].copy()
        obs_df = obs_df.reset_index(drop=True)
        result['climate_observations'] = obs_df
    
    # Climate zones
    if not zones_df.empty:
        zones_cols = ['zone_id', 'zone_name', 'zone_type', 'description', 
                     'min_value', 'max_value', 'unit', 'geometry', 'source', 'retrieval_time']
        zones_clean = zones_df[zones_cols].copy()
        zones_clean = zones_clean.reset_index(drop=True)
        result['climate_zones'] = zones_clean
    
    return result


if __name__ == '__main__':
    # Test with sample data
    import json
    
    # Sample MET data structure
    sample_met = [{
        'source': {
            'id': 'SN18700',
            'name': 'OSLO - BLINDERN',
            'geometry': {
                'coordinates': [10.72, 59.94, 94.0]
            }
        },
        'referenceTime': '2024-01-15T12:00:00Z',
        'observations': [
            {
                'elementId': 'air_temperature',
                'value': 2.5,
                'unit': 'degC',
                'timeOffset': 'PT0H',
                'timeResolution': 'PT1H'
            }
        ]
    }]
    
    # Sample climate zones
    sample_zones = [{
        'id': 'zone1',
        'name': 'Coastal Mild',
        'type': 'temperature',
        'description': 'Mild coastal climate',
        'min_value': -5,
        'max_value': 25,
        'unit': 'degC',
        'source': 'MET'
    }]
    
    climate_df = transform_met_climate_data(sample_met)
    zones_df = transform_climate_zones(sample_zones)
    normalized = normalize_climate_data_for_sqlite(climate_df, zones_df)
    
    print(f"Climate stations: {len(normalized.get('climate_stations', pd.DataFrame()))} rows")
    print(f"Climate observations: {len(normalized.get('climate_observations', pd.DataFrame()))} rows")
    print(f"Climate zones: {len(normalized.get('climate_zones', pd.DataFrame()))} rows")