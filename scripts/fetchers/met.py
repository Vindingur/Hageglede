# PURPOSE: MET Norway Frost API client for weather observations/forecasts
# CONSUMED BY: scripts.pipeline, notebooks, tests
# DEPENDS ON: requests, scripts.config
# TEST: tests/test_fetchers.py
"""
MET Norway (Frost) API fetcher.

Implements the Hageglede fetch protocol via ``fetch_daily_forecast`` which is
re-exported from the shared ``_protocol`` module.  The function name remains
``fetch_daily_forecast`` for backwards compatibility with notebooks and tests.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"


def fetch_daily_forecast(
    lat: float = 59.9139,
    lon: float = 10.7522,
    user_agent: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetch MET compact weather forecast for a given location.

    Parameters
    ----------
    lat : float
        Latitude (default: Oslo 59.9139).
    lon : float
        Longitude (default: Oslo 10.7522).
    user_agent : str or None
        Custom *User-Agent* header. If ``None``, falls back to
        ``os.environ.get("MET_USER_AGENT", "HagegledeApp/0.1")``.

    Returns
    -------
    list[dict]
        A list of time-series dictionaries from the MET API. Each dict has
        keys such as ``time``, ``air_temperature``, etc. When the API request
        fails an empty list is returned and the error is logged.
    """
    resolved_ua = user_agent or os.environ.get(
        "MET_USER_AGENT",
        "HagegledeApp/0.1"
    )
    headers = {"User-Agent": resolved_ua}
    url = f"{BASE_URL}?lat={lat:.4f}&lon={lon:.4f}"
    logger.info("MET GET %s", url)

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("MET API request failed: %s", exc)
        return []

    payload = resp.json()

    # compact format stores time-series in a list under properties > timeseries
    props = payload.get("properties", {})
    timeseries: List[Dict[str, Any]] = props.get("timeseries", [])

    flattened: List[Dict[str, Any]] = []
    for ts in timeseries:
        # Pull out instant data (time + nested data dict)
        time_str = ts.get("time")
        data = ts.get("data", {})
        instant = data.get("instant", {}).get("details", {})
        row = {"time": time_str}
        row.update(instant)
        # Optional: pull short-term next_1_hours summary if available
        next_1h = data.get("next_1_hours", {}).get("details", {})
        row["precipitation_amount_next_1h"] = next_1h.get("precipitation_amount")
        flattened.append(row)

    return flattened
