#!/usr/bin/env python3
"""Plant data loader aligned with the unified Plant table schema."""
# PURPOSE: SQLite upsert loader that inserts into the aligned Plant table
#          (postcode->zone->12-20 plants flow).  Accepts a DataFrame with
#          columns matching the schema and performs upsert by species name.
# CONSUMED BY: scripts/pipeline.py (via load_plant_data), scripts/loaders/__init__.py
# DEPENDS ON: src/hageglede/db/schema.py (Plant model), src/hageglede/db/session.py (get_session)
# TEST: none

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd  # noqa: E402
from src.hageglede.db.session import get_session  # noqa: E402
from src.hageglede.db.schema import Plant  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Columns expected in the transformed DataFrame that map 1-to-1 to Plant model fields.
_PLANT_COLUMNS = [
    "species",
    "family",
    "effort_level",
    "climate_zone_min",
    "climate_zone_max",
    "yield_rating",
    "meal_ideas",
    "sun_needs",
    "water_needs",
    "soil_preference",
    "days_to_maturity",
    "image_url",
]


def _coerce_str(value) -> str:
    """Return a string or None if value is effectively empty."""
    if pd.isna(value) or value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def _coerce_int(value) -> int:
    """Return an int or None."""
    if pd.isna(value) or value is None or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def load_plant_data(df: pd.DataFrame):
    """
    Upsert plant records from a transformed DataFrame into the SQLite Plant table.

    Matching is performed on ``species`` (exact string).  Existing rows are
    updated in-place; missing rows are inserted.

    The DataFrame is expected to carry the aligned columns defined in
    ``_PLANT_COLUMNS``.  Extra columns are ignored.
    """
    if df.empty:
        logger.warning("Received empty DataFrame — nothing to load.")
        return

    # Normalise any None/NaN cells to Python None so the DB handles them uniformly.
    df = df.replace(pd.NA, None).replace({float("nan"): None})

    with get_session() as session:
        upserted = 0
        inserted = 0

        for _, row in df.iterrows():
            species = _coerce_str(row.get("species"))
            if not species:
                logger.warning("Skipping row with no species name: %s", row.to_dict())
                continue

            plant = session.query(Plant).filter_by(species=species).first()

            # Build a dict of scalar columns
            fields = {
                "family": _coerce_str(row.get("family")),
                "effort_level": _coerce_str(row.get("effort_level")),
                "climate_zone_min": _coerce_str(row.get("climate_zone_min")),
                "climate_zone_max": _coerce_str(row.get("climate_zone_max")),
                "yield_rating": _coerce_str(row.get("yield_rating")),
                "meal_ideas": _coerce_str(row.get("meal_ideas")),
                "sun_needs": _coerce_str(row.get("sun_needs")),
                "water_needs": _coerce_str(row.get("water_needs")),
                "soil_preference": _coerce_str(row.get("soil_preference")),
                "days_to_maturity": _coerce_int(row.get("days_to_maturity")),
                "image_url": _coerce_str(row.get("image_url")),
            }

            if plant is None:
                plant = Plant(species=species, **fields)
                session.add(plant)
                inserted += 1
                logger.info("Inserted new plant: %s", species)
            else:
                for col, val in fields.items():
                    setattr(plant, col, val)
                upserted += 1
                logger.info("Updated existing plant: %s", species)

        session.commit()
        logger.info(
            "Plant load complete — inserted=%d, updated=%d, total rows=%d",
            inserted,
            upserted,
            len(df),
        )


def load_plant_csv(file_path: str):
    """Load plant data from a CSV file."""
    df = pd.read_csv(file_path)
    load_plant_data(df)


def load_plant_json(file_path: str):
    """Load plant data from a JSON file (list of records)."""
    import json

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    load_plant_data(df)


def main():
    parser = argparse.ArgumentParser(description="Load plant data into the unified gardening database")
    parser.add_argument("--csv", help="Path to CSV file with plant data")
    parser.add_argument("--json", help="Path to JSON file with plant data")
    args = parser.parse_args()

    if args.csv:
        load_plant_csv(args.csv)
    elif args.json:
        load_plant_json(args.json)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
