#!/usr/bin/env python3
"""
MET Frost API client for fetching climate and weather zone data.

Fetches climate data from MET Norway's Frost API including:
- Daily temperature data
- Precipitation data
- Weather station metadata
- Climate zones data

Requires MET Frost API client ID (available from frost.met.no)
"""
import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MET_CLIENT_ID, DATA_DIR, CACHE_DIR

logger = logging.getLogger(__name__)

class METFetcher:
    """Fetch climate data from MET Norway's Frost API."""
    
    BASE_URL = "https://frost.met.no"
    
    def __init__(self, client_id: str = None):
        """Initialize MET Frost API fetcher.
        
        Args:
            client_id: MET Frost API client ID. If None, reads from config.
        """
        self.client_id = client_id or MET_CLIENT_ID
        if not self.client_id:
            raise ValueError("MET_CLIENT_ID not configured. Get one from frost.met.no")
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "hageglede-data-pipeline/1.0"
        })
        
        # Cache directory for MET data
        self.cache_dir = os.path.join(CACHE_DIR, "met")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info("METFetcher initialized with client ID: %s", self.client_id[:8] + "...")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Frost API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            requests.exceptions.RequestException: On HTTP error
            ValueError: If API returns error
        """
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["client_id"] = self.client_id
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Frost API returns data in "data" field
            if "data" not in data:
                logger.warning("No 'data' field in MET response: %s", data)
                return {"data": []}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error("MET API request failed: %s", e)
            raise
        except json.JSONDecodeError as e:
            logger.error("Failed to parse MET API response: %s", e)
            raise
    
    def get_stations(self, country: str = "NO") -> List[Dict]:
        """Get weather stations for a country.
        
        Args:
            country: Country code (default: "NO" for Norway)
            
        Returns:
            List of station metadata dictionaries
        """
        logger.info("Fetching MET stations for country: %s", country)
        
        # Cache station data for 7 days
        cache_file = os.path.join(self.cache_dir, f"stations_{country}.json")
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 7 * 24 * 3600:  # 7 days
                logger.info("Loading stations from cache")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        try:
            params = {
                "country": country,
                "types": "SensorSystem",
                "fields": "id,name,geometry,masl,municipality,county,stationOwner",
                "limit": 1000
            }
            
            data = self._make_request("/sources/v0.jsonld", params)
            stations = data.get("data", [])
            
            logger.info("Found %d MET stations", len(stations))
            
            # Cache the result
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(stations, f, indent=2, ensure_ascii=False)
            
            return stations
            
        except Exception as e:
            logger.error("Failed to fetch MET stations: %s", e)
            return []
    
    def get_climate_zones(self) -> List[Dict]:
        """Get climate zone definitions for Norway.
        
        Returns:
            List of climate zone definitions
        """
        logger.info("Fetching climate zone definitions")
        
        cache_file = os.path.join(self.cache_dir, "climate_zones.json")
        if os.path.exists(cache_file):
            logger.info("Loading climate zones from cache")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # MET doesn't have a dedicated climate zones API, so we'll create
        # a simplified model based on temperature data
        try:
            # Get stations with long-term temperature records
            params = {
                "country": "NO",
                "elementids": "mean(air_temperature P1D)",
                "timeoffsets": "PT0H",
                "levels": "2",
                "limit": 50
            }
            
            data = self._make_request("/sources/v0.jsonld", params)
            stations = data.get("data", [])
            
            # Create climate zones based on altitude and location
            climate_zones = []
            for station in stations:
                zone = {
                    "station_id": station.get("id"),
                    "name": station.get("name"),
                    "county": station.get("county"),
                    "municipality": station.get("municipality"),
                    "altitude": station.get("masl", 0),
                    "geometry": station.get("geometry"),
                    "climate_zone": self._classify_climate_zone(
                        station.get("county", ""),
                        station.get("masl", 0)
                    ),
                    "source": "MET Frost API"
                }
                climate_zones.append(zone)
            
            logger.info("Created %d climate zone definitions", len(climate_zones))
            
            # Cache the result
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(climate_zones, f, indent=2, ensure_ascii=False)
            
            return climate_zones
            
        except Exception as e:
            logger.error("Failed to create climate zones: %s", e)
            return []
    
    def _classify_climate_zone(self, county: str, altitude: float) -> str:
        """Classify climate zone based on county and altitude.
        
        Args:
            county: County name
            altitude: Altitude in meters
            
        Returns:
            Climate zone classification
        """
        # Simplified climate zone classification for Norway
        if altitude > 600:
            return "alpine"
        elif altitude > 300:
            return "subalpine"
        
        # Coastal vs inland classification
        coastal_counties = ["Møre og Romsdal", "Vestland", "Rogaland", "Agder", "Vestfold og Telemark"]
        if county in coastal_counties:
            return "coastal_mild"
        else:
            return "inland_continental"
    
    def get_weather_data(self, station_id: str, 
                        element_id: str = "mean(air_temperature P1D)",
                        time_range: str = "latest") -> List[Dict]:
        """Get weather observations for a specific station.
        
        Args:
            station_id: MET station ID
            element_id: Weather element ID (default: daily mean temperature)
            time_range: Time range in ISO format or "latest"
            
        Returns:
            List of observation records
        """
        logger.info("Fetching weather data for station %s, element %s", 
                   station_id, element_id)
        
        # Create cache key
        cache_key = f"{station_id}_{element_id}_{time_range}"
        cache_file = os.path.join(self.cache_dir, f"weather_{cache_key}.json")
        
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 24 * 3600:  # 24 hours
                logger.info("Loading weather data from cache")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        try:
            params = {
                "sources": station_id,
                "elements": element_id,
                "referencetime": time_range,
                "limit": 1000
            }
            
            data = self._make_request("/observations/v0.jsonld", params)
            observations = data.get("data", [])
            
            # Extract relevant data
            weather_data = []
            for obs in observations:
                reference_time = obs.get("referenceTime")
                measurements = obs.get("observations", [])
                
                for measurement in measurements:
                    weather_data.append({
                        "station_id": station_id,
                        "reference_time": reference_time,
                        "element_id": measurement.get("elementId"),
                        "value": measurement.get("value"),
                        "unit": measurement.get("unit"),
                        "time_offset": measurement.get("timeOffset"),
                        "time_resolution": measurement.get("timeResolution"),
                        "level": measurement.get("level")
                    })
            
            logger.info("Found %d weather observations", len(weather_data))
            
            # Cache the result
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(weather_data, f, indent=2, ensure_ascii=False)
            
            return weather_data
            
        except Exception as e:
            logger.error("Failed to fetch weather data: %s", e)
            return []
    
    def get_daily_temperatures(self, station_ids: List[str] = None,
                              days_back: int = 30) -> List[Dict]:
        """Get daily temperature data for multiple stations.
        
        Args:
            station_ids: List of station IDs. If None, uses stations from major cities.
            days_back: Number of days back to fetch data for
            
        Returns:
            List of daily temperature records
        """
        if station_ids is None:
            # Default to major Norwegian cities
            station_ids = ["SN18700", "SN50540", "SN90450"]  # Oslo, Bergen, Trondheim
        
        logger.info("Fetching daily temperatures for %d stations, last %d days",
                   len(station_ids), days_back)
        
        all_temperatures = []
        
        for station_id in station_ids:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            time_range = f"{start_date.date()}/{end_date.date()}"
            
            temperatures = self.get_weather_data(
                station_id=station_id,
                element_id="mean(air_temperature P1D)",
                time_range=time_range
            )
            
            all_temperatures.extend(temperatures)
        
        logger.info("Total daily temperature records: %d", len(all_temperatures))
        return all_temperatures
    
    def save_raw_data(self) -> str:
        """Fetch and save all MET data to raw data directory.
        
        Returns:
            Path to saved data file
        """
        logger.info("Starting MET data collection")
        
        # Create output directory
        output_dir = os.path.join(DATA_DIR, "raw", "met")
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"met_data_{timestamp}.json")
        
        # Collect all data
        data = {
            "metadata": {
                "source": "MET Norway Frost API",
                "fetched_at": datetime.now().isoformat(),
                "client_id_prefix": self.client_id[:8] if self.client_id else None
            },
            "stations": self.get_stations(),
            "climate_zones": self.get_climate_zones(),
            "daily_temperatures": self.get_daily_temperatures()
        }
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info("MET data saved to: %s", output_file)
        return output_file


def main():
    """Command-line interface for MET fetcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch climate data from MET Frost API")
    parser.add_argument("--stations", action="store_true", help="Fetch station data")
    parser.add_argument("--zones", action="store_true", help="Fetch climate zones")
    parser.add_argument("--weather", action="store_true", help="Fetch weather data")
    parser.add_argument("--all", action="store_true", help="Fetch all data")
    parser.add_argument("--save", action="store_true", help="Save data to raw directory")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        fetcher = METFetcher()
        
        if args.stations or args.all:
            stations = fetcher.get_stations()
            print(f"Found {len(stations)} stations")
            if stations:
                print("Sample station:", json.dumps(stations[0], indent=2, ensure_ascii=False))
        
        if args.zones or args.all:
            zones = fetcher.get_climate_zones()
            print(f"Created {len(zones)} climate zones")
            if zones:
                print("Sample zone:", json.dumps(zones[0], indent=2, ensure_ascii=False))
        
        if args.weather or args.all:
            temps = fetcher.get_daily_temperatures(days_back=7)
            print(f"Found {len(temps)} temperature records")
            if temps:
                print("Sample temperature:", json.dumps(temps[0], indent=2, ensure_ascii=False))
        
        if args.save or args.all:
            output_file = fetcher.save_raw_data()
            print(f"Data saved to: {output_file}")
            
    except Exception as e:
        logger.error("MET fetcher failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()