"""Pydantic schemas for health and system status."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health and dataset cache diagnostics."""

    status: str = Field(..., description="System status ('healthy' or 'degraded')")
    version: str = Field(..., description="Application version")
    database_connected: bool = Field(..., description="SQLite connection state")
    total_actuals_rows: int = Field(..., description="Cached actual records count")
    total_forecasts_rows: int = Field(..., description="Cached forecast records count")
    earliest_actual_date: str | None = Field(None, description="Earliest cached actual timestamp")
    latest_actual_date: str | None = Field(None, description="Latest cached actual timestamp")
