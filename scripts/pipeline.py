#!/usr/bin/env python3
"""
Pipeline module for fetching and processing weather and species data.

Coordinates data collection from MET Frost and Artsdatabanken APIs,
loads results into the Hageglede SQLite database, and exposes a CLI
entry-point suitable for cron / scheduler invocation.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure scripts/ is on the path so imports work when the CWD is not the
# repository root (e.g. cron, systemd, Docker).
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from scripts.config import DATABASE_PATH, DATA_DIR, FROST_CONFIG
from utils.api_clients import FrostAPI, ArtsdatabankenAPI
from scripts.data_collection import collect_weather_data, collect_species_data
from scripts.data_processing import process_weather_batch, process_species_batch
from scripts.database import get_db_session
from scripts.monitoring import PipelineMonitor

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates weather and species data collection cycles."""

    def __init__(self):
        self.frost = FrostAPI(FROST_CONFIG)
        self.artsdb = ArtsdatabankenAPI()
        self.monitor = PipelineMonitor()
        self.db_path = Path(DATABASE_PATH)
        self.data_dir = Path(DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def run_cycle(self) -> dict:
        """Run a single collection / processing cycle.

        Returns a status dict with counts and any error messages.
        """
        cycle_id = datetime.utcnow().isoformat()
        self.monitor.start_cycle(cycle_id)
        results = {"weather": 0, "species": 0, "errors": []}

        try:
            # Concurrent data fetching -------------------------------
            weather_items, species_items = await asyncio.gather(
                self._collect_weather(),
                self._collect_species(),
            )

            # Sequential processing / persistence ----------------------
            results["weather"] = await process_weather_batch(
                weather_items, db_path=str(self.db_path)
            )
            results["species"] = await process_species_batch(
                species_items, db_path=str(self.db_path)
            )

            self.monitor.record_success(cycle_id, results)
        except Exception as exc:
            logger.exception("Pipeline cycle %s failed", cycle_id)
            results["errors"].append(str(exc))
            self.monitor.record_failure(cycle_id, exc)
        finally:
            self.monitor.end_cycle(cycle_id)

        return results

    def health_check(self) -> dict:
        """Quick diagnostic: can we reach the DB and both APIs?"""
        checks = {
            "db": False,
            "frost": False,
            "artsdatabanken": False,
        }

        try:
            session = get_db_session(str(self.db_path))
            session.execute("SELECT 1")
            session.close()
            checks["db"] = True
        except Exception:
            pass

        try:
            checks["frost"] = self.frost.is_healthy()
        except Exception:
            pass

        try:
            checks["artsdatabanken"] = self.artsdb.is_healthy()
        except Exception:
            pass

        return checks

    async def _collect_weather(self):
        """Fetch recent MET Frost observations for the configured station."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        station_id = FROST_CONFIG.get("station_id", "SN18700")

        raw = await self.frost.get_observations(
            station_id=station_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )
        return raw.get("data", {}).get("tseries", [])

    async def _collect_species(self):
        """Fetch species observations from Artsdatabanken."""
        return await self.artsdb.search_species(
            query="rosa rugosa",
            limit=50,
        )


def main() -> int:
    """Run one pipeline cycle from the command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    pipeline = DataPipeline()
    health = pipeline.health_check()
    logger.info("Health check: %s", health)

    if not all(health.values()):
        logger.error("One or more dependencies are unhealthy — aborting.")
        return 1

    results = asyncio.run(pipeline.run_cycle())
    logger.info("Pipeline cycle complete: %s", results)

    failed = results.get("errors", [])
    if failed:
        logger.error("Cycle finished with %d error(s): %s", len(failed), failed)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
