# PURPOSE: Main data collection pipeline orchestrating MET Frost and Artsdatabanken API ingestion
#          into the Hageglede SQLite database.  Fixes the broken config import that referenced a
#          missing config.settings package.
# CONSUMED BY: CLI entry-point, cron / scheduler
# DEPENDS ON: scripts.config (ConfigManager), scripts.data_collection, scripts.data_processing, utils.api_clients
# TEST: tests/test_pipeline.py
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure scripts/ is on the path so "import scripts.config" works when the CWD
# is not the repository root (e.g. cron, systemd, Docker).
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# ---------------------------------------------------------------------------
# FIXED IMPORT (was: from config.settings import DATABASE_PATH, FROST_CONFIG)
# ---------------------------------------------------------------------------
# config.settings does not exist.  The single source of truth is
# scripts/config.py which exposes module-level constants for backward
# compatibility as well as the ConfigManager class.
# ---------------------------------------------------------------------------
from scripts.config import (
    DATABASE_PATH,
    DATA_DIR,
    FROST_CONFIG,
)

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
        self.db_path = DATABASE_PATH
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def run_cycle(self) -> dict:
        """Run a single collection / processing cycle.

        Returns a status dict with counts and any error messages.
        """
        cycle_id = datetime.utcnow().isoformat()
        self.monitor.start_cycle(cycle_id)
        results = {"weather": 0, "species": 0, "errors": []}

        try:
            async with asyncio.TaskGroup() as tg:
                weather_task = tg.create_task(self._collect_weather())
                species_task = tg.create_task(self._collect_species())

            weather_items = weather_task.result()
            species_items = species_task.result()

            results["weather"] = await process_weather_batch(weather_items)
            results["species"] = await process_species_batch(species_items)

            self.monitor.record_success(cycle_id, results)
        except Exception as exc:
            logger.exception("Pipeline cycle failed")
            results["errors"].append(str(exc))
            self.monitor.record_failure(cycle_id, exc)
        finally:
            self.monitor.end_cycle(cycle_id)

        return results

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

    def health_check(self) -> dict:
        """Quick diagnostic: can we reach the DB and both APIs?"""
        checks = {
            "db": False,
            "frost": False,
            "artsdatabanken": False,
        }
        try:
            session = get_db_session(self.db_path)
            session.execute("SELECT 1")
            session.close()
            checks["db"] = True
        except Exception:
            pass

        # Lightweight ping-style probes
        try:
            checks["frost"] = self.frost.is_healthy()
        except Exception:
            pass

        try:
            checks["artsdatabanken"] = self.artsdb.is_healthy()
        except Exception:
            pass

        return checks


def main():
    """CLI entry-point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    pipeline = DataPipeline()
    health = pipeline.health_check()
    logger.info("Health check: %s", health)

    if not all(health.values()):
        logger.error("One or more dependencies are unhealthy — aborting.")
        sys.exit(1)

    results = asyncio.run(pipeline.run_cycle())
    logger.info("Pipeline cycle complete: %s", results)

    failed = results.get("errors", [])
    if failed:
        logger.error("Cycle finished with %d error(s): %s", len(failed), failed)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
