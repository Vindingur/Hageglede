# Data Pipeline Scripts

Phase 0.5 external data pipeline for Hageglede project. These scripts fetch, transform, and load plant and climate data into SQLite databases, separate from the production code in `src/`.

## Purpose

- Fetch plant data from Artsdatabanken API
- Fetch occurrence and species data from GBIF API  
- Fetch climate/weather zone data from MET Frost API
- Transform raw data to match SQLite schema
- Load transformed data into SQLite databases for use by the main application

## Directory Structure

```
scripts/
├── README.md                 # This file
├── config.py                # Configuration settings
├── pipeline.py              # Main orchestration script
├── requirements.txt         # Python dependencies
├── fetchers/               # Data fetching modules
│   ├── __init__.py
│   ├── artsdatabanken.py   # Artsdatabanken API client
│   ├── gbif.py             # GBIF API client
│   └── met.py              # MET Frost API client
├── transformers/           # Data transformation modules
│   ├── __init__.py
│   ├── plants.py           # Plant data transformation
│   └── climate.py          # Climate data transformation
└── loaders/               # Data loading modules
    ├── __init__.py
    └── sqlite.py          # SQLite database loader
```

## Usage

1. Install dependencies:
   ```bash
   pip install -r scripts/requirements.txt
   ```

2. Configure API keys and settings in `scripts/config.py`

3. Run the full pipeline:
   ```bash
   python scripts/pipeline.py
   ```

4. Or run individual components:
   ```bash
   # Fetch data only
   python -m scripts.fetchers.artsdatabanken
   python -m scripts.fetchers.gbif
   python -m scripts.fetchers.met
   
   # Transform data only  
   python -m scripts.transformers.plants
   python -m scripts.transformers.climate
   
   # Load data only
   python -m scripts.loaders.sqlite
   ```

## Data Sources

### Artsdatabanken
- Norwegian plant species database
- Provides scientific names, Norwegian names, conservation status
- API documentation: https://api.artsdatabanken.no/

### GBIF (Global Biodiversity Information Facility)
- Global species occurrence data
- Species taxonomy and metadata
- API documentation: https://www.gbif.org/developer/summary

### MET Frost API
- Norwegian Meteorological Institute climate data
- Weather zones, temperature, precipitation data
- API documentation: https://frost.met.no/index.html

## Output

The pipeline creates/updates SQLite databases in the `data/` directory:
- `data/plants.db` - Plant species and metadata
- `data/climate.db` - Climate and weather zone data
- `data/occurrences.db` - Species occurrence records

## Notes

- This is Phase 0.5: external data pipeline separate from main application
- Data is fetched incrementally to respect API rate limits
- Transformation handles data cleaning, normalization, and schema alignment
- Loading supports upserts to update existing records