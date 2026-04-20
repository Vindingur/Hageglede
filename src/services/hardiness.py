"""
Hardiness zone service for Norwegian postcodes.
Maps Norwegian postcodes to USDA hardiness zones based on geographic data.
"""
from typing import Dict, Optional, Tuple
import csv
import json
from pathlib import Path
from datetime import datetime

# USDA Hardiness Zone data structure
# Zone format: e.g., "8a", "7b", "6a"
# USDA zones range from 1a (coldest) to 13b (warmest)
# Norway typically ranges from zone 2 to zone 8

class HardinessZoneService:
    """Service for looking up hardiness zones by Norwegian postcode."""
    
    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize the hardiness zone service.
        
        Args:
            data_file: Path to CSV/JSON file with postcode-zone mappings.
                       If None, uses built-in sample data.
        """
        self.zones: Dict[str, Dict] = {}
        self._load_data(data_file)
    
    def _load_data(self, data_file: Optional[str] = None):
        """Load hardiness zone data from file or use sample data."""
        if data_file and Path(data_file).exists():
            self._load_from_file(data_file)
        else:
            self._load_sample_data()
    
    def _load_from_file(self, filepath: str):
        """Load data from CSV or JSON file."""
        filepath = Path(filepath)
        if filepath.suffix == '.csv':
            self._load_csv(filepath)
        elif filepath.suffix == '.json':
            self._load_json(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    def _load_csv(self, filepath: Path):
        """Load data from CSV file with columns: postcode, zone, min_temp_f, min_temp_c, region."""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                postcode = row['postcode'].strip()
                self.zones[postcode] = {
                    'zone': row['zone'],
                    'min_temp_f': float(row.get('min_temp_f', 0)),
                    'min_temp_c': float(row.get('min_temp_c', 0)),
                    'region': row.get('region', ''),
                    'last_updated': row.get('last_updated', datetime.now().isoformat())
                }
    
    def _load_json(self, filepath: Path):
        """Load data from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for postcode, zone_data in data.items():
                self.zones[postcode] = zone_data
    
    def _load_sample_data(self):
        """Load sample data for Norwegian postcodes (simplified mapping)."""
        # Sample data mapping Norwegian postcodes to USDA zones
        # This is simplified - real data would come from agricultural authorities
        sample_data = {
            "0001": {"zone": "8a", "min_temp_c": -12.2, "min_temp_f": 10, "region": "Oslo", "description": "Mild coastal"},
            "0100": {"zone": "7b", "min_temp_c": -14.9, "min_temp_f": 5, "region": "Oslo", "description": "Inland valley"},
            "5000": {"zone": "8a", "min_temp_c": -12.2, "min_temp_f": 10, "region": "Bergen", "description": "Coastal west"},
            "7000": {"zone": "7a", "min_temp_c": -17.7, "min_temp_f": 0, "region": "Trondheim", "description": "Central coastal"},
            "9000": {"zone": "6b", "min_temp_c": -20.5, "min_temp_f": -5, "region": "Tromsø", "description": "Northern coastal"},
            "9500": {"zone": "5a", "min_temp_c": -28.8, "min_temp_f": -20, "region": "Alta", "description": "Far north"},
            "9800": {"zone": "4b", "min_temp_c": -31.7, "min_temp_f": -25, "region": "Vadsø", "description": "Arctic coastal"},
        }
        
        # Add variations for common postcode ranges
        for base_postcode, data in list(sample_data.items()):
            self.zones[base_postcode] = data
            
            # Create some variations for testing
            for i in range(1, 4):
                variant = str(int(base_postcode) + i).zfill(4)
                if variant not in self.zones:
                    self.zones[variant] = {
                        **data,
                        "zone": self._adjust_zone(data["zone"], -0.5 if i % 2 == 0 else 0),
                        "description": f"Near {data['region']} area"
                    }
    
    def _adjust_zone(self, zone: str, adjustment: float) -> str:
        """Adjust a zone by a fraction (e.g., 8a -> 7b for -1 adjustment)."""
        if not zone:
            return "7a"
        
        # Parse zone like "8a" -> (8, 'a')
        zone_num = int(zone[:-1])
        zone_letter = zone[-1]
        
        # Convert letter to numeric (a=0.5, b=0.0)
        letter_value = 0.5 if zone_letter == 'a' else 0.0
        
        total = zone_num + letter_value + adjustment
        
        # Convert back to zone format
        new_zone_num = int(total)
        new_letter = 'a' if (total - new_zone_num) >= 0.5 else 'b'
        
        return f"{new_zone_num}{new_letter}"
    
    def get_zone(self, postcode: str) -> Optional[Dict]:
        """
        Get hardiness zone data for a Norwegian postcode.
        
        Args:
            postcode: Norwegian postcode (4 digits)
            
        Returns:
            Dictionary with zone information or None if not found
        """
        # Clean and validate postcode
        clean_postcode = postcode.strip().zfill(4)
        
        # Direct lookup
        if clean_postcode in self.zones:
            return self.zones[clean_postcode]
        
        # Try to find nearest postcode (simple fallback)
        if len(clean_postcode) == 4:
            # Try first 3 digits for region approximation
            prefix = clean_postcode[:3]
            for key, value in self.zones.items():
                if key.startswith(prefix):
                    return {
                        **value,
                        "estimated": True,
                        "original_postcode": clean_postcode,
                        "matched_postcode": key
                    }
        
        return None
    
    def get_zones_in_region(self, region: str) -> Dict[str, Dict]:
        """
        Get all postcodes and their zones in a region.
        
        Args:
            region: Region name
            
        Returns:
            Dictionary mapping postcodes to zone data
        """
        return {
            postcode: data 
            for postcode, data in self.zones.items() 
            if data.get('region', '').lower() == region.lower()
        }
    
    def get_zone_range(self, min_temp_c: float, max_temp_c: float) -> Dict[str, str]:
        """
        Convert temperature range to USDA zone.
        
        Args:
            min_temp_c: Minimum temperature in Celsius
            max_temp_c: Maximum temperature in Celsius
            
        Returns:
            Dictionary with zone information
        """
        # USDA zones based on average annual minimum temperature
        zone_data = [
            (1, "a", -51.1, -48.3), (1, "b", -48.3, -45.6),
            (2, "a", -45.6, -42.8), (2, "b", -42.8, -40.0),
            (3, "a", -40.0, -37.2), (3, "b", -37.2, -34.4),
            (4, "a", -34.4, -31.7), (4, "b", -31.7, -28.9),
            (5, "a", -28.9, -26.1), (5, "b", -26.1, -23.3),
            (6, "a", -23.3, -20.6), (6, "b", -20.6, -17.8),
            (7, "a", -17.8, -15.0), (7, "b", -15.0, -12.2),
            (8, "a", -12.2, -9.4), (8, "b", -9.4, -6.7),
            (9, "a", -6.7, -3.9), (9, "b", -3.9, -1.1),
            (10, "a", -1.1, 1.7), (10, "b", 1.7, 4.4),
        ]
        
        for zone_num, zone_letter, temp_min, temp_max in zone_data:
            if min_temp_c >= temp_min and min_temp_c < temp_max:
                zone = f"{zone_num}{zone_letter}"
                return {
                    "zone": zone,
                    "min_temp_c": min_temp_c,
                    "max_temp_c": max_temp_c,
                    "description": f"USDA Zone {zone}",
                    "temperature_range_c": (temp_min, temp_max)
                }
        
        # Default to zone 7 (common for Norway)
        return {
            "zone": "7a",
            "min_temp_c": min_temp_c,
            "max_temp_c": max_temp_c,
            "description": "Estimated Zone 7a",
            "temperature_range_c": (-17.8, -15.0),
            "estimated": True
        }


# Singleton instance for dependency injection
hardiness_service = HardinessZoneService()