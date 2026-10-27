"""Pydantic schemas for forecast accuracy, aggregations, and safety buffer endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class AccuracySummaryResponse(BaseModel):
    """Overall forecast accuracy metrics for the specified date range and cutoff."""

    start_date: str = Field(..., description="Start delivery date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End delivery date (YYYY-MM-DD)")
    cutoff_time: str = Field(..., description="Decision cutoff time on D-1 (HH:MM UTC)")
    sample_size: int = Field(..., description="Number of evaluated paired slots")
    mean_actual_mw: float = Field(..., description="Average actual wind generation in MW")
    mean_forecast_mw: float = Field(..., description="Average forecasted wind generation in MW")
    mae: float = Field(..., description="Mean Absolute Error in MW")
    rmse: float = Field(..., description="Root Mean Squared Error in MW")
    bias: float = Field(..., description="Mean Error (forecast - actual) in MW")
    nmae_pct: float = Field(..., description="Normalized MAE (MAE / Mean Actual * 100%)")
    mape_pct: float = Field(..., description="Mean Absolute Percentage Error (%)")
    p50_abs_error: float = Field(..., description="Median absolute error (P50) in MW")
    p90_abs_error: float = Field(..., description="90th percentile absolute error (P90) in MW")
    p95_abs_error: float = Field(..., description="95th percentile absolute error (P95) in MW")
    max_abs_error: float = Field(..., description="Maximum observed absolute error in MW")


class HorizonBucketItem(BaseModel):
    """Accuracy metrics for a forecast horizon lead-time bucket."""

    bucket: str = Field(..., description="Horizon bucket label (e.g. '0-6h')")
    min_hours: float = Field(..., description="Minimum horizon hours")
    max_hours: float = Field(..., description="Maximum horizon hours")
    sample_size: int = Field(..., description="Number of forecasts evaluated")
    mae: float = Field(..., description="Mean Absolute Error in MW")
    rmse: float = Field(..., description="Root Mean Squared Error in MW")
    bias: float = Field(..., description="Mean Error (forecast - actual) in MW")
    p90_abs_error: float = Field(..., description="90th percentile absolute error in MW")


class HorizonAccuracyResponse(BaseModel):
    """Accuracy metrics bucketed by lead-time forecast horizon."""

    buckets: list[HorizonBucketItem] = Field(..., description="Lead-time buckets")


class HourAccuracyItem(BaseModel):
    """Accuracy metrics for a diurnal hour of the day (0-23 UTC)."""

    hour: int = Field(..., description="Hour of the day (0 to 23)")
    hour_label: str = Field(..., description="Formatted hour label (e.g. '09:00')")
    sample_size: int = Field(..., description="Number of slots evaluated")
    avg_actual_mw: float = Field(..., description="Average actual wind generation in MW")
    avg_forecast_mw: float = Field(..., description="Average forecasted wind generation in MW")
    mae: float = Field(..., description="Mean Absolute Error in MW")
    rmse: float = Field(..., description="Root Mean Squared Error in MW")
    bias: float = Field(..., description="Mean Error (forecast - actual) in MW")


class HourAccuracyResponse(BaseModel):
    """Diurnal accuracy breakdown across hours of the day."""

    hours: list[HourAccuracyItem] = Field(..., description="Hourly metrics")


class WindLevelAccuracyItem(BaseModel):
    """Accuracy metrics for a specific wind generation regime."""

    regime: str = Field(..., description="Regime name ('Low', 'Medium', 'High')")
    range_label: str = Field(..., description="MW range description")
    sample_size: int = Field(..., description="Number of slots evaluated")
    mean_actual_mw: float = Field(..., description="Average actual generation in MW")
    mae: float = Field(..., description="Mean Absolute Error in MW")
    rmse: float = Field(..., description="Root Mean Squared Error in MW")
    bias: float = Field(..., description="Mean Error (forecast - actual) in MW")
    nmae_pct: float = Field(..., description="Normalized MAE (%)")


class WindLevelAccuracyResponse(BaseModel):
    """Accuracy breakdown across wind generation levels."""

    regimes: list[WindLevelAccuracyItem] = Field(..., description="Regime metrics")


class BufferResponse(BaseModel):
    """Procurement safety buffer recommendation and deficit distributions."""

    confidence: float = Field(..., description="Requested confidence level (0.80 - 0.99)")
    recommended_buffer_mw: float = Field(
        ..., description="Recommended procurement safety buffer in MW"
    )
    buffer_90_mw: float = Field(..., description="Standard 90% confidence safety buffer in MW")
    buffer_95_mw: float = Field(..., description="Standard 95% confidence safety buffer in MW")
    over_forecast_count: int = Field(
        ..., description="Count of slots where forecast > actual (shortfall events)"
    )
    under_forecast_count: int = Field(
        ..., description="Count of slots where actual > forecast (surplus events)"
    )
    over_forecast_pct: float = Field(
        ..., description="Percentage of delivery periods resulting in shortfalls"
    )
    under_forecast_pct: float = Field(
        ..., description="Percentage of delivery periods resulting in surplus"
    )
    mean_shortfall_mw: float = Field(..., description="Average MW deficit during shortfall periods")
    p90_shortfall_mw: float = Field(
        ..., description="90th percentile shortfall during deficit periods (MW)"
    )
    p95_shortfall_mw: float = Field(
        ..., description="95th percentile shortfall during deficit periods (MW)"
    )
    mean_surplus_mw: float = Field(..., description="Average MW surplus during surplus periods")
    p90_surplus_mw: float = Field(
        ..., description="90th percentile surplus during surplus periods (MW)"
    )
    recommendation_text: str = Field(
        ..., description="Plain-English decision support recommendation for traders"
    )


class ErrorDistributionResponse(BaseModel):
    """Histogram distribution of forecast errors (F - A)."""

    bins: list[dict[str, Any]] = Field(..., description="Histogram bins with counts and ranges")
    quantiles: dict[str, float] = Field(..., description="Quantiles (P05, P10, P50, P90, P95)")
