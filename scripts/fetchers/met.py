#!/usr/bin/env python3
"""
Fetches MET data from the Norwegian Meteorological Institute's API
using MET_CLIENT_ID stored in environment variables via config module.

This script downloads MET data from their API by performing the following steps:

1. Authentication via client ID (stored as environment variable MET_CLIENT_ID)
2. Fetching timeseries data for specified locations and parameters
3. Storing the raw response as JSON files in the data directory (DATA_DIR)
   and also a parquet file for tabular data

Usage:
    python3 met.py --location <location_id> --element <element_id>

Examples:
    python3 met.py --location SN18700 --element air_temperature
    python3 met.py --location SN18700 --element wind_speed
"""

import argparse
import json
import os
import sys
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

# Import configuration from the config module using relative import
try:
    from ..config import get_source, DATA_DIR, CACHE_DIR
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(Path(__file__).parent.parent.parent))
    try:
        from config import get_source, DATA_DIR, CACHE_DIR
    except ImportError as e:
        print(f"Error importing config: {e}")
        print("Please ensure get_source, DATA_DIR, and CACHE_DIR are defined in config.py")
        print("and the environment variable MET_CLIENT_ID is set.")
        sys.exit(1)

def authenticate():
    """
    Authenticate with MET API using client ID from environment variable.

    Returns:
        tuple: (auth_header, client_id) or (None, None) if authentication fails
    """
    # Get MET source configuration
    met_source = get_source('MET')
    if not met_source:
        print("ERROR: MET source configuration not found in config.")
        print("Please ensure MET is defined in SourceConfig with env_key='MET_CLIENT_ID'.")
        return None, None
    
    met_client_id = met_source.env_key
    if not met_client_id:
        print("ERROR: MET_CLIENT_ID environment variable is not set.")
        print("Please set MET_CLIENT_ID with your MET API client ID.")
        return None, None

    # MET API uses client ID in the header for authentication
    auth_header = {"X-Client-ID": met_client_id}

    # Optional test request to verify authentication
    test_url = "https://frost.met.no/sources/v0.jsonld?types=SensorSystem&country=NO&county=Troms og Finnmark"
    try:
        response = requests.get(test_url, headers=auth_header, timeout=10)
        if response.status_code == 200:
            print(f"✓ Authentication successful with client ID: {met_client_id[:8]}...")
            return auth_header, met_client_id
        else:
            print(f"✗ Authentication failed with status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"✗ Authentication request failed: {e}")
        return None, None

def fetch_met_data(location_id, element_id, auth_header):
    """
    Fetch MET timeseries data for a specific location and element.

    Args:
        location_id (str): MET location/source ID (e.g., 'SN18700')
        element_id (str): Element/parameter ID (e.g., 'air_temperature')
        auth_header (dict): Authentication header with client ID

    Returns:
        dict: JSON response from MET API or None if request fails
    """
    # Get MET base URL from configuration
    met_source = get_source('MET')
    base_url = met_source.base_url if met_source else "https://frost.met.no"
    observations_url = f"{base_url}/observations/v0.jsonld"

    # Date range: last 7 days including today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    params = {
        "sources": location_id,
        "elements": element_id,
        "referencetime": f"{start_date.date()}/{end_date.date()}",
        "timeoffsets": "PT0H",  # No time offset
        "timeresolutions": "PT1H",  # Hourly resolution
        "performancecategories": "C",  # Controlled quality only
        "exposurecategories": "1",  # Open area
        "levels": "0",
        "fields": "sourceId,referenceTime,elementId,value,unit,timeOffset,timeResolution"
    }

    print(f"Fetching MET data for location '{location_id}', element '{element_id}'...")
    print(f"Date range: {start_date.date()} to {end_date.date()}")

    try:
        response = requests.get(observations_url, headers=auth_header, params=params, timeout=30)
        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Successfully fetched {len(data.get('data', []))} observations")
            return data
        elif response.status_code == 429:
            print("✗ Rate limit exceeded. Please wait and try again later.")
            return None
        elif response.status_code == 401:
            print("✗ Authentication failed. Check your MET_CLIENT_ID.")
            return None
        else:
            print(f"✗ Request failed with status {response.status_code}: {response.text[:200]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return None

def save_raw_response(data, location_id, element_id):
    """
    Save raw JSON response to data directory.

    Args:
        data (dict): JSON response from MET API
        location_id (str): Location identifier
        element_id (str): Element identifier

    Returns:
        Path: Path to saved JSON file
    """
    # Ensure data directory exists
    raw_data_dir = Path(DATA_DIR) / "raw" / "met"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"met_{location_id}_{element_id}_{timestamp}.json"
    filepath = raw_data_dir / filename

    # Save JSON file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Raw data saved to: {filepath}")
    return filepath

def parse_to_dataframe(data):
    """
    Parse MET JSON response into a pandas DataFrame.

    Args:
        data (dict): JSON response from MET API

    Returns:
        pd.DataFrame: Parsed data or empty DataFrame if parsing fails
    """
    if not data or 'data' not in data:
        return pd.DataFrame()

    records = []
    for observation in data.get('data', []):
        source_id = observation.get('sourceId')
        reference_time = observation.get('referenceTime')
        element_id = observation.get('elementId')

        for obs_value in observation.get('observations', []):
            record = {
                'sourceId': source_id,
                'referenceTime': reference_time,
                'elementId': element_id,
                'value': obs_value.get('value'),
                'unit': obs_value.get('unit'),
                'timeOffset': obs_value.get('timeOffset'),
                'timeResolution': obs_value.get('timeResolution'),
                'level': obs_value.get('level'),
                'fetch_timestamp': datetime.now().isoformat()
            }
            records.append(record)

    if records:
        df = pd.DataFrame(records)
        # Convert referenceTime to datetime
        df['referenceTime'] = pd.to_datetime(df['referenceTime'])
        # Add human-readable columns
        df['date'] = df['referenceTime'].dt.date
        df['hour'] = df['referenceTime'].dt.hour
        return df
    else:
        return pd.DataFrame()

def save_as_parquet(df, location_id, element_id):
    """
    Save parsed data as parquet file.

    Args:
        df (pd.DataFrame): Parsed data
        location_id (str): Location identifier
        element_id (str): Element identifier

    Returns:
        Path: Path to saved parquet file or None if DataFrame is empty
    """
    if df.empty:
        return None

    # Ensure cache directory exists
    cache_dir = Path(CACHE_DIR) / "met"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    filename = f"met_{location_id}_{element_id}_{min_date}_{max_date}.parquet"
    filepath = cache_dir / filename

    # Save parquet file
    df.to_parquet(filepath, index=False)

    print(f"✓ Parquet file saved to: {filepath}")
    print(f"  Shape: {df.shape}, Columns: {list(df.columns)}")
    return filepath

def main():
    """Main function to fetch and process MET data."""
    parser = argparse.ArgumentParser(description="Fetch MET data from Norwegian Meteorological Institute")
    parser.add_argument("--location", "-l", required=True,
                        help="Location/source ID (e.g., SN18700)")
    parser.add_argument("--element", "-e", required=True,
                        help="Element/parameter ID (e.g., air_temperature, wind_speed)")
    parser.add_argument("--test-auth", action="store_true",
                        help="Test authentication only, don't fetch data")

    args = parser.parse_args()

    print("=" * 60)
    print("MET Data Fetcher")
    print("=" * 60)

    # Authenticate
    auth_header, client_id = authenticate()
    if not auth_header:
        sys.exit(1)

    if args.test_auth:
        print("✓ Authentication test passed")
        sys.exit(0)

    # Fetch data
    data = fetch_met_data(args.location, args.element, auth_header)
    if not data:
        print("✗ Failed to fetch data")
        sys.exit(1)

    # Save raw response
    json_path = save_raw_response(data, args.location, args.element)

    # Parse to DataFrame
    df = parse_to_dataframe(data)
    if df.empty:
        print("⚠ No observations found in response")
        sys.exit(0)

    print(f"✓ Parsed {len(df)} observations")

    # Save as parquet
    parquet_path = save_as_parquet(df, args.location, args.element)

    print("=" * 60)
    print("✓ MET data fetch completed successfully!")
    if json_path:
        print(f"  Raw JSON: {json_path}")
    if parquet_path:
        print(f"  Parquet: {parquet_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()