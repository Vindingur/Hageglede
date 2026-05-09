# PURPOSE: Load a tidy weather DataFrame into the local SQLite database
# CONSUMED BY: scripts.pipeline, notebooks, tests
# DEPENDS ON: pandas, sqlalchemy (optional), scripts.loader_utils
# TEST: tests/test_loaders.py
"""
Weather data loader.

Takes a **pandas DataFrame** produced by
:pyfunc:`scripts.transformers.climate.transform_climate_records` and upserts
it into a SQLite ``weather`` table.

No CSV references remain in this module.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "hageglede.db"

_SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS weather (
    time                      TEXT PRIMARY KEY,
    air_temperature           REAL,
    precipitation_amount_next_1h REAL,
    relative_humidity         REAL,
    wind_speed                REAL,
    wind_from_direction       REAL,
    cloud_area_fraction       REAL,
    lat                       REAL,
    lon                       REAL,
    elevation                 REAL
);
"""

_SQL_UPSERT = """
INSERT INTO weather (
    time, air_temperature, precipitation_amount_next_1h,
    relative_humidity, wind_speed, wind_from_direction,
    cloud_area_fraction, lat, lon, elevation
) VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
ON CONFLICT(time) DO UPDATE SET
    air_temperature=excluded.air_temperature,
    precipitation_amount_next_1h=excluded.precipitation_amount_next_1h,
    relative_humidity=excluded.relative_humidity,
    wind_speed=excluded.wind_speed,
    wind_from_direction=excluded.wind_from_direction,
    cloud_area_fraction=excluded.cloud_area_fraction,
    lat=excluded.lat,
    lon=excluded.lon,
    elevation=excluded.elevation;
"""


def _get_connection(db_path: str):
    """Return a DBAPI connection to the SQLite database."""
    import sqlite3
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_weather_table(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Create the ``weather`` table if it does not yet exist."""
    with _get_connection(str(db_path)) as conn:
        conn.execute(_SQL_CREATE_TABLE)
        conn.commit()
    logger.info("weather table initialised at %s", db_path)


def load_weather_df(
    df: pd.DataFrame,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    """
    Upsert a weather DataFrame into SQLite.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with at minimum the columns defined in the schema.
    db_path : str or Path
        Path to the SQLite database.
    """
    if df is None or df.empty:
        logger.warning("load_weather_df called with empty DataFrame; nothing to load.")
        return

    # Ensure the DB directory exists.
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    init_weather_table(db_path)

    # Prepare rows as tuples in schema order.
    cols = [
        "time",
        "air_temperature",
        "precipitation_amount_next_1h",
        "relative_humidity",
        "wind_speed",
        "wind_from_direction",
        "cloud_area_fraction",
        "lat",
        "lon",
        "elevation",
    ]
    # Only keep rows where ``time`` is non-null (PK cannot be NULL).
    rows = df[cols].copy()
    rows = rows.dropna(subset=["time"])
    data_tuples = rows.to_records(index=False).tolist()

    if not data_tuples:
        logger.info("No valid weather rows to insert after filtering.")
        return

    with _get_connection(str(db_path)) as conn:
        # Single transaction
        conn.executemany(_SQL_UPSERT, data_tuples)
        conn.commit()

    logger.info("Inserted / updated %d weather rows.", len(data_tuples))


def main() -> None:
    """CLI entrypoint to initialise the weather table (no CSV input)."""
    import argparse
    parser = argparse.ArgumentParser(description="Initialise weather SQLite table.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite DB")
    args = parser.parse_args()
    init_weather_table(args.db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
