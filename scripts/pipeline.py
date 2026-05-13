# PURPOSE: Orchestrates the ETL pipeline and must import configuration from the actual scripts.config module using correct symbol names.
# CONSUMED BY: scripts/__main__.py, scheduled jobs, CLI entry points
# DEPENDS ON: scripts.config, scripts.fetchers.met, scripts.fetchers.artsdbanken, scripts.transformers.climate, scripts.transformers.plants, scripts.loaders.weather_loader, scripts.loaders.plant_loader
# TEST: none
"""
ETL orchestration:
1) fetch weather from MET API,
2) fetch plant data from Artsdatabanken API,
3) transform via climate/plants modules,
4) load into SQLite tables.
No CSV references.
"""
from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
import pandas as pd

# Ensure project root is on PYTHONPATH
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.config import DATABASE_PATH, FROST_CONFIG  # noqa: E402

logger = logging.getLogger(__name__)

# ── concrete fetchers ──────────────────────────────────────────────────────
def _import_fetcher(mod_name: str):
    try:
        return importlib.import_module(f"scripts.fetchers.{mod_name}")
    except Exception as exc:  # pragma: no cover
        logger.warning("Fetcher %s unavailable: %s", mod_name, exc)
        return None

_m = _import_fetcher("met")
_a = _import_fetcher("artsdbanken")

# ── concrete transformers ──────────────────────────────────────────────────
def _import_transformer(mod_name: str):
    try:
        return importlib.import_module(f"scripts.transformers.{mod_name}")
    except Exception as exc:  # pragma: no cover
        logger.warning("Transformer %s unavailable: %s", mod_name, exc)
        return None

_ct = _import_transformer("climate")
_pt = _import_transformer("plants")

# ── concrete loaders ───────────────────────────────────────────────────────
def _import_loader(mod_name: str):
    try:
        return importlib.import_module(f"scripts.loaders.{mod_name}")
    except Exception as exc:  # pragma: no cover
        logger.warning("Loader %s unavailable: %s", mod_name, exc)
        return None

_wl = _import_loader("weather_loader")
_pl = _import_loader("plant_loader")


def fetch_weather_posts(lat: float, lon: float, alt: float | None = None) -> list[dict]:
    """Delegate to MET fetcher (functions in that module may be renamed)."""
    if _m is None:
        return []
    func = getattr(_m, "fetch_weather_posts", None) or getattr(_m, "fetch_daily_forecast", None)
    if func is None:
        logger.error("No weather fetch function found in scripts.fetchers.met")
        return []
    kwargs = {"lat": lat, "lon": lon}
    if alt is not None:
        kwargs["alt"] = alt
    return func(**kwargs)


def fetch_plant_data(**kwargs) -> list[dict]:
    """Delegate to Artsdatabanken fetcher."""
    if _a is None:
        return []
    func = getattr(_a, "fetch_plant_data", None) or getattr(_a, "fetch_plants_for_date", None)
    if func is None:
        logger.error("No plant fetch function found in scripts.fetchers.artsdbanken")
        return []
    return func(**kwargs)


def transform_climate_records(raw: list[dict]) -> pd.DataFrame:
    """Delegate to climate transformer."""
    if _ct is None:
        return pd.DataFrame()
    func = getattr(_ct, "transform_climate_records", None) or getattr(
        _ct, "transform_climate_data", None
    ) or getattr(_ct, "transform_weather", None)
    if func is None:
        logger.error("No climate transform function found")
        return pd.DataFrame()
    return func(raw)


def transform_plant_records(raw: list[dict]) -> pd.DataFrame:
    """Delegate to plant transformer."""
    if _pt is None:
        return pd.DataFrame()
    func = getattr(_pt, "transform_plant_records", None) or getattr(
        _pt, "transform_plants_records", None
    ) or getattr(_pt, "transform_plants", None)
    if func is None:
        logger.error("No plant transform function found")
        return pd.DataFrame()
    return func(raw)


def load_weather_to_sqlite(df: pd.DataFrame, **kwargs) -> int:
    """Delegate to weather loader."""
    if _wl is None:
        return 0
    func = getattr(_wl, "load_weather_to_sqlite", None) or getattr(
        _wl, "load_weather_df", None
    ) or getattr(_wl, "load_weather_data", None)
    if func is None:
        logger.error("No weather loader function found")
        return 0
    return func(df, **kwargs)


def load_plants_to_sqlite(df: pd.DataFrame, **kwargs) -> int:
    """Delegate to plant loader."""
    if _pl is None:
        return 0
    func = getattr(_pl, "load_plants_to_sqlite", None) or getattr(
        _pl, "load_plant_df", None
    ) or getattr(_pl, "load_plant_data", None)
    if func is None:
        logger.error("No plant loader function found")
        return 0
    return func(df, **kwargs)


def enrich_plants(env: dict | None = None) -> int:
    """Optional enrichment step; delegates to loader enrichment if present."""
    if _pl is None:
        return 0
    func = getattr(_pl, "enrich_and_update_plants", None) or getattr(_pl, "enrich", None)
    if func is None:
        return 0
    return func(env or {}, str(DATABASE_PATH))


# ── pipeline entry ─────────────────────────────────────────────────────────
def run_pipeline(
    *,
    db_path: str | None = None,
    location: dict | None = None,
) -> dict:
    """
    Run full ETL:
      weather:  MET API → climate transformer → weather_loader
      plants:   Artsdatabanken API → plants transformer → plant_loader
    Returns summary dict with record counts.
    """
    db_path = db_path or str(DATABASE_PATH)
    location = location or FROST_CONFIG or {}

    lat = float(location.get("lat", 59.9))
    lon = float(location.get("lon", 10.8))
    alt = location.get("alt")

    # Ensure tables exist
    if _wl is not None:
        init = getattr(_wl, "init_weather_table", None)
        if init:
            init(db_path)
    if _pl is not None:
        init = getattr(_pl, "init_plants_table", None)
        if init:
            init(db_path)

    # Weather branch
    weather_raw = fetch_weather_posts(lat, lon, alt)
    logger.info("Fetched %d weather posts", len(weather_raw))

    weather_df = transform_climate_records(weather_raw)
    weather_count = 0
    if not weather_df.empty:
        weather_count = load_weather_to_sqlite(weather_df, db_path=db_path)
        logger.info("Loaded %d weather records", weather_count)

    # Plant branch
    plant_raw = fetch_plant_data(
        fields="TaxonId,Name,Author,RiskStatus,RiskAssessment.Id,ModelArea.Id"
    )
    logger.info("Fetched %d raw plant records", len(plant_raw))

    plant_df = transform_plant_records(plant_raw)
    plant_count = 0
    if not plant_df.empty:
        plant_count = load_plants_to_sqlite(plant_df, db_path=db_path)
        logger.info("Loaded %d plant records", plant_count)

    # Optional enrichment
    enrich_count = enrich_plants()

    return {
        "weather_fetched": len(weather_raw),
        "weather_loaded": weather_count,
        "plants_fetched": len(plant_raw),
        "plants_loaded": plant_count,
        "plants_enriched": enrich_count,
        "db_path": db_path,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    summary = run_pipeline()
    print(summary)
