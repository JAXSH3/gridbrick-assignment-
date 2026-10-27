"""CLI script for ingesting Elexon BMRS data and running data-quality checks.

Usage:
    python -m app.ingest [--force] [--check-only]
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import logging
import sys

from app.core.config import settings
from app.services.ingestion import ElexonIngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("app.ingest")


async def main() -> None:
    """Execute ingestion pipeline and data quality audit."""
    parser = argparse.ArgumentParser(description="Ingest Elexon BMRS wind actuals and forecasts.")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion of data.")
    parser.add_argument("--check-only", action="store_true", help="Only run data quality profiling.")
    args = parser.parse_args()

    service = ElexonIngestionService()

    if not args.check_only:
        # Date ranges for January 2026 delivery:
        # Actuals: from 2026-01-01 00:00:00Z through 2026-02-02 02:00:00Z
        start_actuals = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_actuals = datetime(2026, 2, 2, 2, 0, 0, tzinfo=timezone.utc)

        # Forecasts: published late December 2025 through 2026-01-31 23:59:59Z
        start_forecasts = datetime(2025, 12, 28, 0, 0, 0, tzinfo=timezone.utc)
        end_forecasts = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

        logger.info("Starting Elexon BMRS Data Ingestion...")
        logger.info("Ingesting FUELHH Actuals (WIND)...")
        actuals_count = await service.ingest_actuals(start_actuals, end_actuals, chunk_days=7)
        logger.info("Successfully ingested %d actual wind generation records.", actuals_count)

        logger.info("Ingesting WINDFOR Forecasts...")
        forecasts_count = await service.ingest_forecasts(start_forecasts, end_forecasts, chunk_days=7)
        logger.info("Successfully ingested %d forecast generation records.", forecasts_count)

    logger.info("Running Data Quality Checks & Profiling...")
    quality_report = service.profile_data_quality()

    print("\n" + "=" * 60)
    print("        ELEXON BMRS DATA QUALITY PROFILE REPORT        ")
    print("=" * 60)
    print(json.dumps(quality_report, indent=2))
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
