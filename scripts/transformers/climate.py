# PURPOSE: Transform raw MET weather data into a structured DataFrame for the weather_loader.
# CONSUMED BY: scripts/pipeline.py, scripts/loaders/weather_loader.py
# DEPENDS ON: scripts.fetchers.met
# TEST: none
"""
Climate data transformer for Hageglede.

Converts raw JSON from the MET API into a clean pandas DataFrame
suitable for SQLite loading via scripts.loaders.weather_loader.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

def transform_climate_data(raw_data: dict[str, Any]) -> pd.DataFrame:
    """Transform MET JSON into a DataFrame.

    Parameters
    ----------
    raw_data : dict
        The *full* MET API response dict (usually from
        ``scripts.fetchers.met.fetch_weather``).

    Returns
    -------
    pandas.DataFrame with at minimum the columns required by
    ``scripts.loaders.weather_loader.upsert_weather_data``:
    ``forecast_time``, ``temperature``, ``precipitation``, ``wind_speed``,
    ``humidity``, ``pressure``, ``cloud_fraction``.
    """
    if not isinstance(raw_data, dict):
        logger.error("Expected dict from MET API, got %s", type(raw_data).__name__)
        return _empty_frame()

    try:
        timeseries = raw_data["properties"]["timeseries"]
    except KeyError:
        logger.error("Missing 'properties.timeseries' in MET data; keys: %s", raw_data.keys())
        return _empty_frame()

    rows: list[dict[str, Any]] = []
    for entry in timeseries:
        ts = entry.get("time")
        if not ts:
            continue
        instant = entry.get("data", {}).get("instant", {}).get("details", {})
        next_1h = (
            entry.get("data", {}).get("next_1_hours", {}).get("summary", {})
        )
        next_1h_details = (
            entry.get("data", {}).get("next_1_hours", {}).get("details", {})
        )

        row = {
            "forecast_time": datetime.fromisoformat(ts.replace("Z", "+00:00")),
            "temperature": _to_float(instant.get("air_temperature")),
            "precipitation": _to_float(
                next_1h_details.get("precipitation_amount")
                or next_1h.get("symbol_code")
            ),
            "wind_speed": _to_float(instant.get("wind_speed")),
            "humidity": _to_float(instant.get("relative_humidity")),
            "pressure": _to_float(instant.get("air_pressure_at_sea_level")),
            "cloud_fraction": _to_float(instant.get("cloud_area_fraction")),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def _to_float(value: Any) -> float | None:
    """Safely coerce a value to float; return None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _empty_frame() -> pd.DataFrame:
    """Return an empty DataFrame with the canonical columns."""
    return pd.DataFrame(
        columns=[
            "forecast_time",
            "temperature",
            "precipitation",
            "wind_speed",
            "humidity",
            "pressure",
            "cloud_fraction",
        ]
    )
