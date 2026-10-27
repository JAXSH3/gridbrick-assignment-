"""Database connection and table management using SQLite."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from app.core.config import settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS actuals (
    startTime TEXT PRIMARY KEY,
    publishTime TEXT NOT NULL,
    settlementDate TEXT NOT NULL,
    settlementPeriod INTEGER NOT NULL,
    generation REAL NOT NULL,
    fuelType TEXT NOT NULL DEFAULT 'WIND'
);

CREATE TABLE IF NOT EXISTS forecasts (
    startTime TEXT NOT NULL,
    publishTime TEXT NOT NULL,
    generation REAL NOT NULL,
    horizon_hours REAL NOT NULL,
    PRIMARY KEY (startTime, publishTime)
);

CREATE INDEX IF NOT EXISTS idx_actuals_date ON actuals(settlementDate);
CREATE INDEX IF NOT EXISTS idx_forecasts_startTime ON forecasts(startTime);
CREATE INDEX IF NOT EXISTS idx_forecasts_publishTime ON forecasts(publishTime);
CREATE INDEX IF NOT EXISTS idx_forecasts_start_publish ON forecasts(startTime, publishTime);
"""


def init_db(db_path: Path | None = None) -> None:
    """Initialize database schemas and directories."""
    path = db_path or settings.DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def get_db_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a contextual SQLite connection with dictionary row access."""
    path = db_path or settings.DATABASE_PATH
    if not path.exists():
        init_db(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
