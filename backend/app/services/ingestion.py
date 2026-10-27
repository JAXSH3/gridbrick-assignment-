"""Elexon BMRS data ingestion service with chunking, retry backoff, and quality profiling."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.db.session import get_db_connection, init_db

logger = logging.getLogger(__name__)

BMRS_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
FUELHH_STREAM_URL = f"{BMRS_BASE_URL}/datasets/FUELHH/stream"
WINDFOR_STREAM_URL = f"{BMRS_BASE_URL}/datasets/WINDFOR/stream"


def parse_utc_iso(dt_str: str) -> datetime:
    """Parse an ISO-8601 string into an aware UTC datetime."""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).astimezone(UTC)


def format_utc_iso(dt: datetime) -> str:
    """Format aware datetime to ISO-8601 string with Z suffix."""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class ElexonIngestionService:
    """Ingests actual wind generation and forecasts from Elexon BMRS API."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            self.db_path: Path = settings.DATABASE_PATH
        elif isinstance(db_path, str):
            self.db_path = Path(db_path)
        else:
            self.db_path = db_path
        init_db(self.db_path)

    async def fetch_json_stream_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any],
        max_retries: int = 4,
    ) -> list[dict[str, Any]]:
        """Fetch JSON data from Elexon stream with exponential backoff."""
        delay = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                response = await client.get(url, params=params, timeout=45.0)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict) and "data" in data:
                        return list(data["data"])
                    return []
                logger.warning(
                    "Attempt %d/%d failed with status %d: %s",
                    attempt,
                    max_retries,
                    response.status_code,
                    response.text[:200],
                )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                logger.warning(
                    "Attempt %d/%d failed with network error: %s", attempt, max_retries, exc
                )

            if attempt < max_retries:
                await asyncio.sleep(delay)
                delay *= 2.0

        raise RuntimeError(f"Failed to fetch data from {url} after {max_retries} attempts.")

    async def ingest_actuals(
        self,
        start_date: datetime,
        end_date: datetime,
        chunk_days: int = 7,
    ) -> int:
        """Ingest FUELHH actual generation for wind into the database."""
        total_rows = 0
        current_start = start_date

        async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=chunk_days), end_date)
                logger.info(
                    "Fetching actuals from %s to %s",
                    format_utc_iso(current_start),
                    format_utc_iso(current_end),
                )
                params = {
                    "publishDateTimeFrom": format_utc_iso(current_start),
                    "publishDateTimeTo": format_utc_iso(current_end),
                    "fuelType": "WIND",
                }
                records = await self.fetch_json_stream_with_retry(client, FUELHH_STREAM_URL, params)

                # Filter and prepare batch
                rows_to_insert = []
                for r in records:
                    if r.get("fuelType") != "WIND":
                        continue
                    start_time = r.get("startTime")
                    publish_time = r.get("publishTime")
                    generation = r.get("generation")
                    settlement_date = r.get("settlementDate")
                    settlement_period = r.get("settlementPeriod")

                    if start_time and generation is not None:
                        rows_to_insert.append(
                            (
                                start_time,
                                publish_time or start_time,
                                settlement_date or start_time[:10],
                                int(settlement_period) if settlement_period else 1,
                                float(generation),
                                "WIND",
                            )
                        )

                if rows_to_insert:
                    with get_db_connection(self.db_path) as conn:
                        conn.executemany(
                            """
                            INSERT OR REPLACE INTO actuals
                            (startTime, publishTime, settlementDate, settlementPeriod, generation, fuelType)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            rows_to_insert,
                        )
                        conn.commit()
                    total_rows += len(rows_to_insert)
                    logger.info(
                        "Inserted %d actual wind records (total %d)",
                        len(rows_to_insert),
                        total_rows,
                    )

                current_start = current_end
                await asyncio.sleep(0.2)

        return total_rows

    async def ingest_forecasts(
        self,
        start_date: datetime,
        end_date: datetime,
        chunk_days: int = 7,
    ) -> int:
        """Ingest WINDFOR wind forecasts into the database and calculate horizon."""
        total_rows = 0
        current_start = start_date

        async with httpx.AsyncClient(headers={"Accept": "application/json"}) as client:
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=chunk_days), end_date)
                logger.info(
                    "Fetching forecasts from %s to %s",
                    format_utc_iso(current_start),
                    format_utc_iso(current_end),
                )
                params = {
                    "publishDateTimeFrom": format_utc_iso(current_start),
                    "publishDateTimeTo": format_utc_iso(current_end),
                }
                records = await self.fetch_json_stream_with_retry(
                    client, WINDFOR_STREAM_URL, params
                )

                rows_to_insert = []
                for r in records:
                    start_time = r.get("startTime")
                    publish_time = r.get("publishTime")
                    generation = r.get("generation")

                    if start_time and publish_time and generation is not None:
                        try:
                            start_dt = parse_utc_iso(start_time)
                            pub_dt = parse_utc_iso(publish_time)
                            horizon_hours = round((start_dt - pub_dt).total_seconds() / 3600.0, 2)
                            rows_to_insert.append(
                                (
                                    start_time,
                                    publish_time,
                                    float(generation),
                                    horizon_hours,
                                )
                            )
                        except (ValueError, TypeError):
                            continue

                if rows_to_insert:
                    with get_db_connection(self.db_path) as conn:
                        conn.executemany(
                            """
                            INSERT OR REPLACE INTO forecasts
                            (startTime, publishTime, generation, horizon_hours)
                            VALUES (?, ?, ?, ?)
                            """,
                            rows_to_insert,
                        )
                        conn.commit()
                    total_rows += len(rows_to_insert)
                    logger.info(
                        "Inserted %d forecast records (total %d)", len(rows_to_insert), total_rows
                    )

                current_start = current_end
                await asyncio.sleep(0.2)

        return total_rows

    def profile_data_quality(self) -> dict[str, Any]:
        """Perform comprehensive data quality checks on cached records."""
        with get_db_connection(self.db_path) as conn:
            actuals_count = conn.execute("SELECT COUNT(*) FROM actuals").fetchone()[0]
            forecasts_count = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]

            # Actuals date range and continuity for January 2026
            jan_actuals = conn.execute(
                """
                SELECT startTime, generation FROM actuals
                WHERE startTime >= '2026-01-01T00:00:00Z' AND startTime <= '2026-01-31T23:30:00Z'
                ORDER BY startTime ASC
                """
            ).fetchall()

            jan_actuals_count = len(jan_actuals)
            expected_jan_slots = 31 * 48  # 1488 half-hours in January (31 days)

            # Check for negative or null generation
            negative_actuals = conn.execute(
                "SELECT COUNT(*) FROM actuals WHERE generation < 0"
            ).fetchone()[0]
            actual_gen_stats = conn.execute(
                """
                SELECT MIN(generation), MAX(generation), AVG(generation)
                FROM actuals WHERE startTime >= '2026-01-01T00:00:00Z' AND startTime <= '2026-01-31T23:30:00Z'
                """
            ).fetchone()

            # Forecast statistics
            forecast_gen_stats = conn.execute(
                "SELECT MIN(generation), MAX(generation), AVG(generation), MIN(horizon_hours), MAX(horizon_hours) FROM forecasts"
            ).fetchone()
            negative_horizons = conn.execute(
                "SELECT COUNT(*) FROM forecasts WHERE horizon_hours < 0"
            ).fetchone()[0]
            negative_forecast_gen = conn.execute(
                "SELECT COUNT(*) FROM forecasts WHERE generation < 0"
            ).fetchone()[0]

            # Unique forecast delivery dates covered in Jan 2026
            jan_fc_target_slots = conn.execute(
                """
                SELECT COUNT(DISTINCT startTime) FROM forecasts
                WHERE startTime >= '2026-01-01T00:00:00Z' AND startTime <= '2026-01-31T23:30:00Z'
                """
            ).fetchone()[0]

            # Missing half-hour intervals in January actuals
            missing_slots: list[str] = []
            if jan_actuals:
                existing_stamps = {row["startTime"] for row in jan_actuals}
                cur_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
                end_dt = datetime(2026, 1, 31, 23, 30, 0, tzinfo=UTC)
                while cur_dt <= end_dt:
                    iso = format_utc_iso(cur_dt)
                    if iso not in existing_stamps:
                        missing_slots.append(iso)
                    cur_dt += timedelta(minutes=30)

            return {
                "total_actuals_rows": actuals_count,
                "jan_actuals_rows": jan_actuals_count,
                "expected_jan_actuals_rows": expected_jan_slots,
                "actuals_coverage_pct": round(jan_actuals_count / expected_jan_slots * 100, 2)
                if expected_jan_slots
                else 0,
                "missing_actual_slots": missing_slots,
                "negative_actuals_count": negative_actuals,
                "actual_min_mw": round(actual_gen_stats[0], 1)
                if actual_gen_stats[0] is not None
                else None,
                "actual_max_mw": round(actual_gen_stats[1], 1)
                if actual_gen_stats[1] is not None
                else None,
                "actual_avg_mw": round(actual_gen_stats[2], 1)
                if actual_gen_stats[2] is not None
                else None,
                "total_forecasts_rows": forecasts_count,
                "jan_forecast_distinct_slots": jan_fc_target_slots,
                "forecast_min_mw": round(forecast_gen_stats[0], 1)
                if forecast_gen_stats[0] is not None
                else None,
                "forecast_max_mw": round(forecast_gen_stats[1], 1)
                if forecast_gen_stats[1] is not None
                else None,
                "forecast_avg_mw": round(forecast_gen_stats[2], 1)
                if forecast_gen_stats[2] is not None
                else None,
                "min_horizon_hours": round(forecast_gen_stats[3], 2)
                if forecast_gen_stats[3] is not None
                else None,
                "max_horizon_hours": round(forecast_gen_stats[4], 2)
                if forecast_gen_stats[4] is not None
                else None,
                "negative_horizons_count": negative_horizons,
                "negative_forecast_gen_count": negative_forecast_gen,
            }
