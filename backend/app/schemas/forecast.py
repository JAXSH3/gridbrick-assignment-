"""Pydantic schemas for forecast endpoints."""

from pydantic import BaseModel, Field


class ForecastSlotItem(BaseModel):
    """Forecast and actual metrics for a specific target time slot."""

    start_time: str = Field(..., description="Target delivery start time in ISO-8601 UTC")
    publish_time: str | None = Field(
        None, description="Publish time of the selected forecast in ISO-8601 UTC"
    )
    forecast_mw: float | None = Field(
        None, description="Forecasted wind generation in MW available at cutoff"
    )
    actual_mw: float | None = Field(
        None, description="Actual outturn wind generation in MW from FUELHH"
    )
    error_mw: float | None = Field(None, description="Forecast error (forecast - actual) in MW")
    abs_error_mw: float | None = Field(
        None, description="Absolute forecast error |forecast - actual| in MW"
    )
    horizon_hours: float | None = Field(
        None, description="Lead-time forecast horizon (startTime - publishTime) in hours"
    )


class DayForecastResponse(BaseModel):
    """Cutoff-selected wind forecasts for a complete delivery day."""

    target_date: str = Field(..., description="Delivery date (YYYY-MM-DD)")
    cutoff_time: str = Field(..., description="Cutoff time on D-1 (HH:MM UTC)")
    cutoff_datetime: str = Field(..., description="Exact cutoff timestamp in ISO-8601 UTC on D-1")
    slots: list[ForecastSlotItem] = Field(
        ..., description="Chronological list of target delivery slots"
    )
    slot_count: int = Field(..., description="Total slots returned")
    has_missing_actuals: bool = Field(
        False, description="Flag indicating if any delivery slot is missing actual data"
    )
    has_missing_forecasts: bool = Field(
        False, description="Flag indicating if any delivery slot has no forecast before cutoff"
    )


class VintageItem(BaseModel):
    """A single forecast publication for a target slot."""

    start_time: str = Field(..., description="Target delivery start time in ISO-8601 UTC")
    publish_time: str = Field(..., description="When forecast was published in ISO-8601 UTC")
    forecast_mw: float = Field(..., description="Forecasted wind generation in MW")
    horizon_hours: float = Field(..., description="Lead time in hours")


class VintageResponse(BaseModel):
    """All historical forecast vintages published for a specific delivery slot."""

    start_time: str = Field(..., description="Target delivery slot in ISO-8601 UTC")
    actual_mw: float | None = Field(
        None, description="Actual outturn wind generation in MW if available"
    )
    vintages: list[VintageItem] = Field(
        ..., description="Successive forecast vintages sorted chronologically by publishTime"
    )
    vintage_count: int = Field(..., description="Total number of published vintages")
