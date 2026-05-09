# PURPOSE: Convert raw Artsdatabanken plant records into a tidy DataFrame for plant_loader
# CONSUMED BY: scripts.pipeline, notebooks, tests
# DEPENDS ON: pandas
# TEST: tests/test_transformers.py
"""
Plant transformer.

Provides ``transform_plants_records`` which takes raw Artsdatabanken records
and produces a tidy ``pandas.DataFrame`` ready for ``load_plant_df``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = [
    "id",
    "scientific_name",
    "common_name",
    "taxon_group",
    "synonyms",
    "category",
    "ingested_at",
]


def transform_plants_records(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transform raw Artsdatabanken plant records into a tidy DataFrame.

    Parameters
    ----------
    records : list[dict]
        Normalised plant dicts (e.g. from
        :pyfunc:`scripts.fetchers.artsdatabanken.fetch_plants_for_date`).

    Returns
    -------
    pandas.DataFrame
        Tidy DataFrame with standardised columns. The ``synonyms`` column
        is stored as a JSON-string so it can sit in a single TEXT column in
        SQLite.
    """
    if not records:
        logger.warning("transform_plants_records called with empty records.")
        df = pd.DataFrame(columns=_REQUIRED_COLUMNS)
        return df

    df = pd.DataFrame(records)

    # Ensure required columns exist.
    for col in _REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Normalise synonyms to a JSON string if they are a list/dict.
    import json
    def _serialise_syn(val: Any) -> str | None:
        if val is None or (isinstance(val, str) and val == ""):
            return None
        if isinstance(val, str):
            return val
        try:
            return json.dumps(val, ensure_ascii=False)
        except (TypeError, ValueError):
            logger.debug("Could not serialise synonyms value: %s", val)
            return None

    if "synonyms" in df.columns:
        df["synonyms"] = df["synonyms"].apply(_serialise_syn)

    # ingestion timestamp
    df["ingested_at"] = pd.Timestamp.utcnow()

    df = df[_REQUIRED_COLUMNS]
    return df
