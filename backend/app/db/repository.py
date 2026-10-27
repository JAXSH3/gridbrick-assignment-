"""Data access repository for querying cached actuals and forecasts from SQLite."""

from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import settings
from app.db.session import get_db_connection


class DataRepository:
    """Repository querying cached Elexon BMRS wind generation data."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.DATABASE_PATH

    def get_health_stats(self) -> dict[str, Any]:
        """Query row counts and coverage dates for system health diagnostics."""
        with get_db_connection(self.db_path) as conn:
            actuals_count = conn.execute("SELECT COUNT(*) FROM actuals").fetchone()[0]
            forecasts_count = conn.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
            min_max_actual = conn.execute(
                "SELECT MIN(startTime), MAX(startTime) FROM actuals"
            ).fetchone()

            return {
                "database_connected": True,
                "total_actuals_rows": actuals_count,
                "total_forecasts_rows": forecasts_count,
                "earliest_actual_date": min_max_actual[0] if min_max_actual else None,
                "latest_actual_date": min_max_actual[1] if min_max_actual else None,
            }

    def get_actuals_for_range(self, start_time: str, end_time: str) -> pd.DataFrame:
        """Fetch actuals between start_time and end_time (inclusive)."""
        with get_db_connection(self.db_path) as conn:
            query = """
                SELECT startTime, generation AS actual_mw
                FROM actuals
                WHERE startTime >= ? AND startTime <= ?
                ORDER BY startTime ASC
            """
            rows = conn.execute(query, (start_time, end_time)).fetchall()
            if not rows:
                return pd.DataFrame(columns=["startTime", "actual_mw"])
            return pd.DataFrame([dict(r) for r in rows])

    def get_forecasts_for_targets(self, start_time: str, end_time: str) -> pd.DataFrame:
        """Fetch all forecast records where target startTime falls within the range."""
        with get_db_connection(self.db_path) as conn:
            query = """
                SELECT startTime, publishTime, generation AS forecast_mw, horizon_hours
                FROM forecasts
                WHERE startTime >= ? AND startTime <= ?
                ORDER BY startTime ASC, publishTime ASC
            """
            rows = conn.execute(query, (start_time, end_time)).fetchall()
            if not rows:
                return pd.DataFrame(
                    columns=["startTime", "publishTime", "forecast_mw", "horizon_hours"]
                )
            return pd.DataFrame([dict(r) for r in rows])

    def get_vintages_for_slot(self, start_time: str) -> tuple[float | None, list[dict[str, Any]]]:
        """Fetch all published forecast vintages and actual outturn for a single target slot."""
        with get_db_connection(self.db_path) as conn:
            # Actual outturn
            act_row = conn.execute(
                "SELECT generation FROM actuals WHERE startTime = ?", (start_time,)
            ).fetchone()
            actual_mw = float(act_row[0]) if act_row and act_row[0] is not None else None

            # All published forecast vintages
            fc_rows = conn.execute(
                """
                SELECT startTime, publishTime, generation AS forecast_mw, horizon_hours
                FROM forecasts
                WHERE startTime = ?
                ORDER BY publishTime ASC
                """,
                (start_time,),
            ).fetchall()

            vintages = [
                {
                    "start_time": r["startTime"],
                    "publish_time": r["publishTime"],
                    "forecast_mw": float(r["forecast_mw"]),
                    "horizon_hours": float(r["horizon_hours"]),
                }
                for r in fc_rows
            ]

            return actual_mw, vintages

    def get_all_january_forecasts_and_actuals(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch all January 2026 forecast vintages and actuals for horizon degradation analysis."""
        with get_db_connection(self.db_path) as conn:
            act_rows = conn.execute(
                """
                SELECT startTime, generation AS actual_mw
                FROM actuals
                WHERE startTime >= '2026-01-01T00:00:00Z' AND startTime <= '2026-01-31T23:30:00Z'
                ORDER BY startTime ASC
                """
            ).fetchall()

            fc_rows = conn.execute(
                """
                SELECT startTime, publishTime, generation AS forecast_mw, horizon_hours
                FROM forecasts
                WHERE startTime >= '2026-01-01T00:00:00Z' AND startTime <= '2026-01-31T23:30:00Z'
                ORDER BY startTime ASC, publishTime ASC
                """
            ).fetchall()

            act_df = (
                pd.DataFrame([dict(r) for r in act_rows])
                if act_rows
                else pd.DataFrame(columns=["startTime", "actual_mw"])
            )
            fc_df = (
                pd.DataFrame([dict(r) for r in fc_rows])
                if fc_rows
                else pd.DataFrame(
                    columns=["startTime", "publishTime", "forecast_mw", "horizon_hours"]
                )
            )

            return fc_df, act_df
