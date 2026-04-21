# Data Loaders for Unified Gardening Database

This directory contains data loaders for the unified `gardening.db` database. The system has been consolidated from multiple separate databases (hageplan.db, hageglede.db, etc.) into a single comprehensive gardening database.

## Unified Database Structure

All gardening data is now stored in a single SQLite database file: `gardening.db`

### Database Location
- **Production**: `/data/gardening.db` (on server)
- **Development**: `~/gardening.db` (local development)

### Database Schema

The unified schema includes tables from all previous gardening databases:

**Plant Management Tables:**
- `plants` - All plant information (merged from multiple sources)
- `plantings` - Planting schedule and history
- `varieties` - Plant varieties and cultivars
- `zones` - Gardening zones and regions

**Weather & Environmental Tables:**
- `weather_data` - Weather observations and forecasts
- `soil_samples` - Soil test results
- `environment_logs` - Temperature, humidity, light levels

**Harvest & Yield Tables:**
- `harvests` - Harvest records and quantities
- `yields` - Yield calculations and metrics
- `quality_ratings` - Produce quality assessments

**Planning & Schedule Tables:**
- `garden_plans` - Garden layout and planning
- `tasks` - Gardening tasks and schedules
- `reminders` - Maintenance reminders

## Available Loaders

### Plant Loader
**File**: `scripts/loaders/plant_loader.py`
**Purpose**: Load plant data from various sources into the unified database
**Usage**: `python -m scripts.loaders.plant_loader [--source SOURCE] [--file FILE]`

Sources:
- CSV files with plant catalogs
- JSON APIs from seed companies
- Existing hageplan.db migration

### Weather Loader
**File**: `scripts/loaders/weather_loader.py`
**Purpose**: Load weather and environmental data into the unified database
**Usage**: `python -m scripts.loaders.weather_loader [--source SOURCE] [--start-date DATE] [--end-date DATE]`

Sources:
- Weather API integrations
- Local weather station data
- Historical weather archives

## Database Session Management

All database operations use the unified session manager:

```python
from src.hageglede.db.session import get_session

# Get a database session
session = get_session()

# Use the session for queries
plants = session.query(Plant).filter(Plant.is_active == True).all()
```

## Migration from Legacy Databases

If migrating from older separate databases:

1. **Export data** from legacy databases (hageplan.db, hageglede.db, etc.)
2. **Transform data** to match unified schema
3. **Load data** using the appropriate loaders
4. **Verify integrity** with validation scripts

## Running Loaders in Production

Loaders are designed to run as scheduled jobs or one-time migrations:

```bash
# Load plant data
cd /path/to/hageglede
python -m scripts.loaders.plant_loader --source csv --file /data/plant_catalog.csv

# Load weather data
python -m scripts.loaders.weather_loader --source api --start-date 2024-01-01
```

## Environment Variables

Configure database paths and API keys:

```bash
# Database location
export GARDENING_DB_PATH=/data/gardening.db

# Weather API (if applicable)
export WEATHER_API_KEY=your_api_key_here

# Plant catalog API
export PLANT_API_KEY=your_plant_api_key
```

## Adding New Loaders

1. Create new loader module in `scripts/loaders/`
2. Import from `src.hageglede.db` for database access
3. Follow the established pattern for command-line arguments
4. Add documentation to this README

## Data Validation

After loading data, run validation checks:

```bash
python -m scripts.validate_data --check plants
python -m scripts.validate_data --check weather
```

## Troubleshooting

**Database locked errors**: Ensure only one loader process runs at a time
**Missing tables**: Run schema initialization: `python -m src.hageglede.db.schema --init`
**Data quality issues**: Use validation scripts to identify problems