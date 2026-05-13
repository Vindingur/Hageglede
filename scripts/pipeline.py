#!/usr/bin/env python3
"""
Aletheia Data Pipeline

Orchestrates the full ETL workflow: fetch artwork records from multiple museum
APIs, normalise them, and persist to the local DuckDB database.
"""

# PURPOSE: Orchestrate full ETL workflow (fetch, normalise, persist to DuckDB)
# CONSUMED BY: cron job / CI / manual execution
# DEPENDS ON: scripts/config.py, scripts/fetch_met.py, scripts/fetch_artsdb.py, scripts/normalise.py, scripts/validate.py, scripts/load_db.py
# TEST: tests/test_pipeline.py

import logging
import sys
from pathlib import Path

# Allow imports when run from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.config import DATABASE_PATH, DATA_DIR, FROST_CONFIG
from scripts.fetch_met import fetch_artworks as fetch_met
from scripts.fetch_artsdb import fetch_artworks as fetch_artsdb
from scripts.normalise import normalise_artwork
from scripts.load_db import init_db, bulk_insert
from scripts.validate import validate_artwork

logger = logging.getLogger("aletheia.pipeline")


# ────────────────────────────────
# Pipeline runner
# ────────────────────────────────

def run_pipeline(limit: int = 100) -> dict:
    """Run the full ETL pipeline and return a summary dict."""
    init_db()

    logger.info("Fetching data from MET API …")
    met_raw = fetch_met(limit=limit)

    logger.info("Fetching data from ArtsDB API …")
    arts_raw = fetch_artsdb(limit=limit)

    all_records = met_raw + arts_raw

    logger.info("Normalising %d raw records …", len(all_records))
    normalised = [normalise_artwork(r) for r in all_records]

    valid_records = [r for r in normalised if validate_artwork(r)]
    invalid_count = len(normalised) - len(valid_records)

    logger.info("Loading %d valid records into DuckDB (skipped %d invalid) …", len(valid_records), invalid_count)
    bulk_insert(valid_records)

    return {
        "fetched": len(all_records),
        "valid": len(valid_records),
        "invalid": invalid_count,
        "db_path": str(DATABASE_PATH),
    }


# ────────────────────────────────
# CLI entrypoint
# ────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    summary = run_pipeline()
    print(summary)
