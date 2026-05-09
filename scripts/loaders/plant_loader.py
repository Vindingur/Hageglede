# PURPOSE: Load a tidy plant DataFrame into the local SQLite database via upsert
# CONSUMED BY: scripts.pipeline, notebooks, tests
# DEPENDS ON: pandas
# TEST: tests/test_loaders.py
"""
Plant data loader.

Takes a **pandas DataFrame** produced by
:pyfunc:`scripts.transformers.plants.transform_plants_records` and upserts
it into a SQLite ``plants`` table.

No CSV references remain in this module.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "hageglede.db"

_SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS plants (
    id                INTEGER,
    scientific_name   TEXT PRIMARY KEY,
    common_name       TEXT,
    taxon_group       TEXT,
    synonyms          TEXT,
    category          TEXT,
    ingested_at       TEXT
);
"""

_SQL_UPSERT = """
INSERT INTO plants (
    id, scientific_name, common_name, taxon_group,
    synonyms, category, ingested_at
) VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(scientific_name) DO UPDATE SET
    id=excluded.id,
    common_name=excluded.common_name,
    taxon_group=excluded.taxon_group,
    synonyms=excluded.synonyms,
    category=excluded.category,
    ingested_at=excluded.ingested_at;
"""


def _get_connection(db_path: str):
    """Return a DBAPI connection to the SQLite database."""
    import sqlite3
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_plants_table(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Create the ``plants`` table if it does not yet exist."""
    with _get_connection(str(db_path)) as conn:
        conn.execute(_SQL_CREATE_TABLE)
        conn.commit()
    logger.info("plants table initialised at %s", db_path)


def _enforce_str(val: Any) -> str | None:
    """Coerce value to str, or None if missing / NaN."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return str(val)


def load_plant_df(
    df: pd.DataFrame,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    """
    Upsert a plant DataFrame into SQLite.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with at minimum columns matching the ``plants`` schema.
    db_path : str or Path
        Path to the SQLite database.
    """
    if df is None or df.empty:
        logger.warning("load_plant_df called with empty DataFrame; nothing to load.")
        return

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    init_plants_table(db_path)

    cols = [
        "id",
        "scientific_name",
        "common_name",
        "taxon_group",
        "synonyms",
        "category",
        "ingested_at",
    ]
    rows = df.copy()

    for col in ["id"]:
        if col in rows.columns:
            rows[col] = pd.to_numeric(rows[col], errors="coerce").astype("Int64")

    for col in cols:
        if col not in rows.columns:
            rows[col] = None

    # Drop rows where scientific_name is missing (primary key).
    rows = rows[rows["scientific_name"].notna()]

    data_tuples = rows[cols].to_records(index=False).tolist()

    if not data_tuples:
        logger.info("No valid plant rows to insert after filtering.")
        return

    with _get_connection(str(db_path)) as conn:
        conn.executemany(_SQL_UPSERT, data_tuples)
        conn.commit()

    logger.info("Inserted / updated %d plant rows.", len(data_tuples))


def load_plant_records(
    records: List[Dict[str, Any]],
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    """
    Convenience entrypoint for raw dicts (e.g. direct from fetcher).

    Wraps the records in a DataFrame and forwards to :pyfunc:`load_plant_df`.
    """
    if not records:
        logger.warning("load_plant_records called with empty list.")
        return
    df = pd.DataFrame(records)
    load_plant_df(df, db_path)


def main() -> None:
    """CLI entrypoint to initialise the plants table (no CSV input)."""
    import argparse
    parser = argparse.ArgumentParser(description="Initialise plants SQLite table.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite DB")
    args = parser.parse_args()
    init_plants_table(args.db)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
