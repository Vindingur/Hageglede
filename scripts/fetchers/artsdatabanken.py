# PURPOSE: Artsdatabanken API client for Norwegian plant species data
# CONSUMED BY: scripts.pipeline, notebooks, tests
# DEPENDS ON: requests
# TEST: tests/test_fetchers.py
"""
Artsdatabanken API fetcher for Norwegian plant species data.

Provides ``fetch_plants_for_date`` (and the back-compat alias ``fetch_plants``)
which conforms to the Hageglede fetch protocol.  Each record returned contains
scientific name, common name, taxonomic group, and optional synonym list.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.artsdatabanken.no/api/species"
DEFAULT_USER_AGENT = "HagegledeApp/0.1"


def fetch_plants_for_date(
    date: str | None = None,
    limit: int = 500,
    filter_common: str = "",
    filter_synonyms: str = "",
    user_agent: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetch plant species data from Artsdatabanken.

    Parameters
    ----------
    date : str or None
        ISO date ``YYYY-MM-DD`` used when constructing the request.
        If ``None``, the current UTC date is used.
    limit : int
        Maximum number of records to return.
    filter_common : str
        Substring that a record's common name must contain for it to be
        included in the result (case-insensitive).
    filter_synonyms : str
        Substring that a record's scientific/synonym names must contain
        (case-insensitive).
    user_agent : str or None
        Custom User-Agent header. Defaults to ``HagegledeApp/0.1`` or the
        ``ARTSDATABANKEN_USER_AGENT`` environment variable.

    Returns
    -------
    list[dict]
        A list of plant records. Each record contains at minimum:
        ``scientificName``, ``popularName`` (common name), ``taxonGroup``,
        and ``synonyms``.
    """
    resolved_date = date or datetime.utcnow().strftime("%Y-%m-%d")
    resolved_ua = user_agent or os.environ.get(
        "ARTSDATABANKEN_USER_AGENT",
        DEFAULT_USER_AGENT,
    )
    headers = {"User-Agent": resolved_ua, "Accept": "application/json"}

    params: Dict[str, Any] = {
        "limit": limit,
        "date": resolved_date,
    }

    url = f"{BASE_URL}"
    logger.info("Artsdatabanken GET %s (limit=%d, date=%s)", url, limit, resolved_date)

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Artsdatabanken API request failed: %s", exc)
        return []

    payload = resp.json()
    # The API returns a list under a key or the root may be a list.
    raw_records: List[Dict[str, Any]] = payload if isinstance(payload, list) else payload.get("species", [])

    # Flatten / normalise each record.
    cleaned: List[Dict[str, Any]] = []
    for rec in raw_records:
        flat = enrich_plant_dict(rec)
        cleaned.append(flat)

    # Apply in-memory filters.
    if filter_common:
        needle = filter_common.lower()
        cleaned = [r for r in cleaned if needle in (r.get("common_name") or "").lower()]
    if filter_synonyms:
        needle = filter_synonyms.lower()
        cleaned = [r for r in cleaned if needle in (r.get("scientific_name") or "").lower()]

    return cleaned


def enrich_plant_dict(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise a single Artsdatabanken record into a flat dictionary.

    Parameters
    ----------
    raw : dict
        Raw JSON record from the Artsdatabanken API.

    Returns
    -------
    dict
        Normalised record with keys:
        ``id``, ``scientific_name``, ``common_name``, ``taxon_group``,
        ``synonyms``, ``category``.
    """
    scientific = raw.get("scientificName") or raw.get("name", "")
    common = raw.get("popularName") or raw.get("vernacularName", "")
    taxon_group = raw.get("taxonGroup") or raw.get("group", "")
    synonyms = raw.get("synonyms") or []
    category = raw.get("category", "SP")
    _id = raw.get("id", None)

    return {
        "id": _id,
        "scientific_name": scientific,
        "common_name": common,
        "taxon_group": taxon_group,
        "synonyms": synonyms,
        "category": category,
    }
