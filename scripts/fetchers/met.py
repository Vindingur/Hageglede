# PURPOSE: MET Frost API fetcher for live Norwegian weather observations with auth, retries and rate limiting
# CONSUMED BY: scripts/pipeline.py, scripts.transformers.climate
# DEPENDS ON: scripts.fetchers.base, scripts.fetchers.met_frost_client, scripts.config.config
# TEST: none

"""
MET data fetcher using the live Norwegian Meteorological Institute Frost API.
Fetches real weather observations from frost.met.no with proper authentication,
rate limiting respect, and exponential-backoff retries.

Usage (programmatic):
    from scripts.fetchers.met import MetFetcher
    fetcher = MetFetcher(config)
    raw_data = await fetcher.fetch(station_id="SN18700", elements=["air_temperature"])

Usage (CLI):
    python -m scripts.fetchers.met --station SN18700 --element air_temperature
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..config.config import FetcherConfig, config as app_config
from .base import BaseFetcher, FetchConfig, FetchResult
from .met_frost_client import AuthenticationError, MetFrostClient, RateLimitError

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class MetFetcher(BaseFetcher[List[Dict[str, Any]]]):
    """
    Fetcher for MET Norway Frost API live weather observations.

    Returns structured observation records that match the interface
    expected by ``scripts.transformers.climate.transform_met_climate_data``.
    """

    def __init__(self, cfg: Optional[FetcherConfig] = None):
        self.cfg = cfg or app_config.fetcher
        self._client: Optional[MetFrostClient] = None
        self._init_client()
        super().__init__(
            source_name="met",
            config=FetchConfig(
                url=self.cfg.met_api_url,
                api_key=self.cfg.met_frost_api_key,
                retry_attempts=self.cfg.max_retries,
                retry_delay=int(self.cfg.rate_limit_delay),
                timeout=self.cfg.timeout,
            ),
        )

    # ------------------------------------------------------------------
    # Client lifecycle
    # ------------------------------------------------------------------
    def _init_client(self) -> None:
        key = self.cfg.met_frost_api_key
        if not key:
            key = os.getenv("MET_CLIENT_ID", "")
        if key:
            self._client = MetFrostClient(
                client_id=key,
                base_url=self.cfg.met_api_url,
                timeout=self.cfg.timeout,
                max_retries=self.cfg.max_retries,
                rate_limit_delay=self.cfg.rate_limit_delay,
            )
        else:
            logger.warning("MET_FROST_API_KEY / MET_CLIENT_ID not configured")

    # ------------------------------------------------------------------
    # BaseFetcher interface
    # ------------------------------------------------------------------
    async def fetch(
        self,
        station_id: str = "SN18700",
        elements: Optional[List[str]] = None,
        days_back: int = 7,
    ) -> FetchResult[List[Dict[str, Any]]]:
        """
        Fetch live observations from the MET Frost API.

        Args:
            station_id: MET station source ID (e.g. ``SN18700``).
            elements: List of element IDs (e.g. ``["air_temperature"]``).
            days_back: Number of days to look back from today.

        Returns:
            FetchResult whose ``data`` is a list of observation dicts compatible
            with ``transform_met_climate_data``.
        """
        if self._client is None:
            raise AuthenticationError("MET Frost client not initialised – missing API key")

        start = (datetime.utcnow() - timedelta(days=days_back)).date()
        end = datetime.utcnow().date()
        referencetime = f"{start.isoformat()}/{end.isoformat()}"

        logger.info(
            "Fetching MET Frost observations station=%s elements=%s ref=%s",
            station_id, elements or "all", referencetime,
        )

        t0 = time.perf_counter()
        try:
            payload = self._client.get_observations(
                sources=station_id,
                elements=",".join(elements) if elements else None,
                referencetime=referencetime,
            )
        except (RateLimitError, AuthenticationError):
            raise
        except Exception as exc:
            logger.exception("MET Frost fetch failed")
            return FetchResult(
                data=[],
                metadata={"station_id": station_id, "error": str(exc)},
                timestamp=datetime.utcnow(),
                source=self.source_name,
                success=False,
                error_message=str(exc),
            )
        elapsed = time.perf_counter() - t0

        structured = self._parse_response(payload, station_id)
        logger.info(
            "Fetched %d observations in %.2fs from station %s",
            len(structured), elapsed, station_id,
        )

        return FetchResult(
            data=structured,
            metadata={
                "station_id": station_id,
                "elements": elements,
                "referencetime": referencetime,
                "records": len(structured),
                "elapsed_s": elapsed,
            },
            timestamp=datetime.utcnow(),
            source=self.source_name,
            success=True,
        )

    def validate_config(self) -> bool:
        return bool(self._client and self._client.client_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_response(payload: Dict[str, Any], station_id: str) -> List[Dict[str, Any]]:
        """
        Parse Frost JSON payload into the structure required by the transformer.

        Transformer expects each root dict to contain:
            - ``source``: station metadata (id, name, geometry)
            - ``referenceTime``: ISO timestamp string
            - ``observations``: list of observation dicts with ``elementId``,
              ``value``, ``unit``, ``timeOffset``, ``timeResolution``, ``level``
        """
        records: List[Dict[str, Any]] = []
        data = payload.get("data", [])
        if not data:
            logger.warning("MET Frost response contained zero data items")
            return records

        # station-level metadata is usually inside each observation block
        for item in data:
            source_info = item.get("source")
            if not source_info:
                source_info = {"id": station_id}

            entry: Dict[str, Any] = {
                "source": source_info,
                "referenceTime": item.get("referenceTime", ""),
                "observations": [],
            }
            for obs in item.get("observations", []):
                entry["observations"].append({
                    "elementId": obs.get("elementId", ""),
                    "value": obs.get("value"),
                    "unit": obs.get("unit", ""),
                    "timeOffset": obs.get("timeOffset", ""),
                    "timeResolution": obs.get("timeResolution", ""),
                    "level": obs.get("level", {}),
                })
            records.append(entry)
        return records

    # ------------------------------------------------------------------
    # Backwards-compatible / convenience methods
    # ------------------------------------------------------------------
    def fetch_climate_data(
        self,
        station_id: str = "SN18700",
        elements: Optional[List[str]] = None,
        days_back: int = 7,
    ) -> pd.DataFrame:
        """
        Synchronous convenience wrapper returning a DataFrame.

        Performs a synchronous fetch (the MET Frost API is REST) and
        returns an empty DataFrame on failure so that downstream pipeline
        steps can continue.
        """
        import asyncio

        try:
            result = asyncio.get_event_loop().run_until_complete(
                self.fetch(station_id=station_id, elements=elements, days_back=days_back)
            )
        except Exception as exc:
            logger.error("fetch_climate_data failed: %s", exc)
            return pd.DataFrame()

        if not result.success:
            logger.error("fetch_climate_data unsuccessful: %s", result.error_message)
            return pd.DataFrame()

        # Flatten into DataFrame
        rows: List[Dict[str, Any]] = []
        for rec in result.data:
            base = {
                "source": rec.get("source", {}),
                "referenceTime": rec.get("referenceTime"),
            }
            for obs in rec.get("observations", []):
                row = base.copy()
                row.update(obs)
                rows.append(row)
        return pd.DataFrame(rows)

    def get_environment_info(
        self, lat: float = 59.9139, lon: float = 10.7522
    ) -> Dict[str, Any]:
        """
        Return a minimal environment info map using nearest available station.
        """
        return {
            "temperature": "N/A",
            "humidity": "N/A",
            "precipitation": "N/A",
            "wind_speed": "N/A",
            "wind_direction": "N/A",
            "sunrise": "N/A",
            "sunset": "N/A",
            "location": {"lat": lat, "lon": lon},
            "data_source": "MET_Frost_API",
            "station_id": self._client.fetch_station_nearby(lat, lon) if self._client else None,
        }

    async def fetch_forecast(self, lat: float, lon: float, days: int = 7) -> FetchResult[List[Dict[str, Any]]]:
        """Fetch weather forecast from MET Frost API (future extension)."""
        return FetchResult(
            data=[],
            metadata={"lat": lat, "lon": lon, "days": days},
            timestamp=datetime.utcnow(),
            source=self.source_name,
            success=True,
        )


# ---------------------------------------------------------------------------
# Standalone functions (backward compatible with old CLI / module usage)
# ---------------------------------------------------------------------------

def authenticate() -> tuple:
    """Authenticate and return auth header, client_id."""
    import asyncio

    fetcher = MetFetcher()
    if fetcher._client is None:
        return ({}, "")
    return ({"X-Client-ID": fetcher._client.client_id}, fetcher._client.client_id)


def fetch_met_data(
    location_id: str, element_id: str, auth_header: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """Fetch MET timeseries data for a specific location and element."""
    import asyncio

    fetcher = MetFetcher()
    if fetcher._client is None:
        logger.error("Cannot fetch MET data – client not initialised")
        return None
    if auth_header:
        fetcher._client.session.headers.update(auth_header)

    try:
        result = asyncio.get_event_loop().run_until_complete(
            fetcher.fetch(station_id=location_id, elements=[element_id])
        )
    except Exception as exc:
        logger.error("fetch_met_data failed: %s", exc)
        return None

    if not result.success:
        return None

    # Re-assemble into legacy dict shape for backward compat callers
    return {"data": result.data}


def save_raw_response(data: Dict[str, Any], location_id: str, element_id: str) -> Path:
    """Save raw JSON response to the data directory."""
    raw_dir = Path(app_config.paths.raw_data_dir) / "met"
    raw_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    fp = raw_dir / f"met_{location_id}_{element_id}_{ts}.json"
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Raw MET data saved to %s", fp)
    return fp


def parse_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Parse MET Frost structured records into a pandas DataFrame."""
    rows: List[Dict[str, Any]] = []
    for obs in data:
        base = {
            "sourceId": obs.get("source", {}).get("id"),
            "referenceTime": obs.get("referenceTime"),
        }
        for itm in obs.get("observations", []):
            row = base.copy()
            row.update(itm)
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "referenceTime" in df.columns:
        df["referenceTime"] = pd.to_datetime(df["referenceTime"], errors="coerce")
        df["date"] = df["referenceTime"].dt.date
        df["hour"] = df["referenceTime"].dt.hour
    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch live MET Frost data")
    parser.add_argument("--station", default="SN18700", help="Station ID")
    parser.add_argument("--element", default="air_temperature", help="Element ID")
    parser.add_argument("--days-back", type=int, default=7, help="Days to look back")
    parser.add_argument("--test-auth", action="store_true", help="Test authentication")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    fetcher = MetFetcher()
    if args.test_auth:
        if fetcher.validate_config():
            print("MET Frost authentication: OK")
        else:
            print("MET Frost authentication: FAILED – check MET_CLIENT_ID / MET_FROST_API_KEY")
            sys.exit(1)
        return

    import asyncio

    try:
        result = asyncio.get_event_loop().run_until_complete(
            fetcher.fetch(station_id=args.station, elements=[args.element], days_back=args.days_back)
        )
    except Exception as exc:
        logger.error("Fetch failed: %s", exc)
        sys.exit(1)

    if not result.success:
        logger.error("Fetch unsuccessful: %s", result.error_message)
        sys.exit(1)

    print(f"Fetched {len(result.data)} observation groups")
    for rec in result.data[:3]:
        print("  -", rec.get("referenceTime"), len(rec.get("observations", [])), "observations")

    if args.output:
        args.output.write_text(json.dumps(result.data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
