"""Transform raw plant data from Artsdatabanken and GBIF to SQLite schema."""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def transform_artsdatabanken_species(raw_data: List[Dict]) -> pd.DataFrame:
    """
    Transform Artsdatabanken species data to plant_species table schema.
    
    Args:
        raw_data: List of species records from Artsdatabanken API
        
    Returns:
        DataFrame ready for plant_species table
    """
    if not raw_data:
        logger.warning("No Artsdatabanken species data to transform")
        return pd.DataFrame()
    
    records = []
    for species in raw_data:
        # Extract basic information
        record = {
            "scientific_name": species.get("scientificName"),
            "norwegian_name": species.get("norwegianName"),
            "scientific_name_id": species.get("scientificNameId"),
            "norwegian_name_id": species.get("norwegianNameId"),
            "kingdom": species.get("kingdom"),
            "phylum": species.get("phylum"),
            "class": species.get("class"),
            "order": species.get("order"),
            "family": species.get("family"),
            "genus": species.get("genus"),
            "species": species.get("species"),
            "species_group": species.get("speciesGroup"),
            "redlist_category": species.get("redlistCategory"),
            "redlist_assessment_date": species.get("redlistAssessmentDate"),
            "species_status": species.get("speciesStatus"),
            "ecological_group": species.get("ecologicalGroup"),
            "habitat": species.get("habitat"),
            "north_limit": species.get("northLimit"),
            "south_limit": species.get("southLimit"),
            "mountain_limit": species.get("mountainLimit"),
            "life_form": species.get("lifeForm"),
            "flowering_period": species.get("floweringPeriod"),
            "pollination": species.get("pollination"),
            "seed_dispersal": species.get("seedDispersal"),
            "last_updated": datetime.now().isoformat(),
            "source": "Artsdatabanken"
        }
        
        # Clean empty strings
        record = {k: (v if v not in ["", None] else None) for k, v in record.items()}
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"Transformed {len(df)} Artsdatabanken species records")
    return df


def transform_gbif_occurrences(raw_data: List[Dict]) -> pd.DataFrame:
    """
    Transform GBIF occurrence data to plant_occurrences table schema.
    
    Args:
        raw_data: List of occurrence records from GBIF API
        
    Returns:
        DataFrame ready for plant_occurrences table
    """
    if not raw_data:
        logger.warning("No GBIF occurrence data to transform")
        return pd.DataFrame()
    
    records = []
    for occ in raw_data:
        # Extract coordinates if available
        lat = occ.get("decimalLatitude")
        lon = occ.get("decimalLongitude")
        
        # Extract date information
        year = occ.get("year")
        month = occ.get("month")
        day = occ.get("day")
        
        # Create date string if possible
        if year and month and day:
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
        elif year and month:
            date_str = f"{year:04d}-{month:02d}-01"
        elif year:
            date_str = f"{year:04d}-01-01"
        else:
            date_str = None
        
        record = {
            "occurrence_id": occ.get("key"),
            "gbif_id": occ.get("gbifID"),
            "dataset_key": occ.get("datasetKey"),
            "scientific_name": occ.get("scientificName"),
            "accepted_scientific_name": occ.get("acceptedScientificName"),
            "kingdom": occ.get("kingdom"),
            "phylum": occ.get("phylum"),
            "class": occ.get("class"),
            "order": occ.get("order"),
            "family": occ.get("family"),
            "genus": occ.get("genus"),
            "species": occ.get("species"),
            "decimal_latitude": lat,
            "decimal_longitude": lon,
            "country": occ.get("country"),
            "locality": occ.get("locality"),
            "county": occ.get("county"),
            "municipality": occ.get("municipality"),
            "occurrence_date": date_str,
            "year": year,
            "month": month,
            "day": day,
            "basis_of_record": occ.get("basisOfRecord"),
            "recorded_by": occ.get("recordedBy"),
            "identified_by": occ.get("identifiedBy"),
            "license": occ.get("license"),
            "last_interpreted": occ.get("lastInterpreted"),
            "last_crawled": occ.get("lastCrawled"),
            "last_updated": datetime.now().isoformat(),
            "source": "GBIF"
        }
        
        # Clean empty strings
        record = {k: (v if v not in ["", None] else None) for k, v in record.items()}
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"Transformed {len(df)} GBIF occurrence records")
    return df


def transform_gbif_species(raw_data: List[Dict]) -> pd.DataFrame:
    """
    Transform GBIF species data to plant_species table schema.
    
    Args:
        raw_data: List of species records from GBIF API
        
    Returns:
        DataFrame ready for plant_species table
    """
    if not raw_data:
        logger.warning("No GBIF species data to transform")
        return pd.DataFrame()
    
    records = []
    for species in raw_data:
        record = {
            "scientific_name": species.get("scientificName"),
            "canonical_name": species.get("canonicalName"),
            "species_key": species.get("speciesKey"),
            "taxon_key": species.get("taxonKey"),
            "kingdom": species.get("kingdom"),
            "phylum": species.get("phylum"),
            "class": species.get("class"),
            "order": species.get("order"),
            "family": species.get("family"),
            "genus": species.get("genus"),
            "species": species.get("species"),
            "taxon_rank": species.get("taxonRank"),
            "taxonomic_status": species.get("taxonomicStatus"),
            "nub_key": species.get("nubKey"),
            "num_descendants": species.get("numDescendants"),
            "last_interpreted": species.get("lastInterpreted"),
            "last_crawled": species.get("lastCrawled"),
            "last_updated": datetime.now().isoformat(),
            "source": "GBIF"
        }
        
        # Clean empty strings
        record = {k: (v if v not in ["", None] else None) for k, v in record.items()}
        records.append(record)
    
    df = pd.DataFrame(records)
    logger.info(f"Transformed {len(df)} GBIF species records")
    return df


def combine_species_data(
    artsdatabanken_df: pd.DataFrame,
    gbif_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine species data from multiple sources.
    
    Args:
        artsdatabanken_df: DataFrame from Artsdatabanken
        gbif_df: DataFrame from GBIF
        
    Returns:
        Combined DataFrame with deduplication
    """
    if artsdatabanken_df.empty and gbif_df.empty:
        return pd.DataFrame()
    
    # Add source column if not present
    if not artsdatabanken_df.empty and "source" not in artsdatabanken_df.columns:
        artsdatabanken_df["source"] = "Artsdatabanken"
    if not gbif_df.empty and "source" not in gbif_df.columns:
        gbif_df["source"] = "GBIF"
    
    # Combine the data
    combined = pd.concat([artsdatabanken_df, gbif_df], ignore_index=True)
    
    # Simple deduplication based on scientific name
    # In a real implementation, you might want more sophisticated deduplication
    combined = combined.drop_duplicates(subset=["scientific_name"], keep="first")
    
    logger.info(f"Combined {len(combined)} unique species records")
    return combined