"""Accuracy evaluation endpoints: summary metrics, horizon degradation, diurnal, wind level, buffer sizing."""

from datetime import date, timedelta
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.db.repository import DataRepository
from app.schemas.accuracy import (
    AccuracySummaryResponse,
    BufferResponse,
    ErrorDistributionResponse,
    HorizonAccuracyResponse,
    HourAccuracyResponse,
    WindLevelAccuracyResponse,
)
from app.services.domain import (
    aggregate_by_horizon,
    aggregate_by_hour,
    aggregate_by_wind_level,
    calculate_safety_buffer,
    compute_accuracy_metrics,
    compute_error_distribution,
    get_cutoff_datetime,
    join_forecasts_and_actuals,
    select_latest_forecasts_at_cutoff,
)

router = APIRouter(prefix="/accuracy", tags=["Accuracy & Safety Buffer"])


def get_cutoff_joined_data_for_range(
    start_date_str: str,
    end_date_str: str,
    cutoff_str: str,
) -> pd.DataFrame:
    """Reconstruct daily cutoff-selected forecasts matched with actuals across a date range.

    For each delivery day D in the range, selects the latest forecast available
    before the cutoff on D-1 and joins with delivery actuals.
    """
    try:
        start_d = date.fromisoformat(start_date_str)
        end_d = date.fromisoformat(end_date_str)
        if start_d > end_d:
            raise ValueError(
                f"start_date ({start_date_str}) cannot be after end_date ({end_date_str})"
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    start_iso = f"{start_date_str}T00:00:00Z"
    end_iso = f"{end_date_str}T23:30:00Z"

    repo = DataRepository()
    actuals_df = repo.get_actuals_for_range(start_iso, end_iso)
    forecasts_df = repo.get_forecasts_for_targets(start_iso, end_iso)

    frames: list[pd.DataFrame] = []
    cur = start_d
    while cur <= end_d:
        d_str = cur.isoformat()
        cutoff_dt = get_cutoff_datetime(cur, cutoff_str)
        day_fc = forecasts_df[forecasts_df["startTime"].str.startswith(d_str)]
        day_act = actuals_df[actuals_df["startTime"].str.startswith(d_str)]

        selected_fc = select_latest_forecasts_at_cutoff(day_fc, cutoff_dt)
        merged = join_forecasts_and_actuals(selected_fc, day_act)
        frames.append(merged)
        cur += timedelta(days=1)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


@router.get("/summary", response_model=AccuracySummaryResponse)
def get_accuracy_summary(
    start_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="Start delivery date (YYYY-MM-DD)",
            examples=["2026-01-01"],
        ),
    ] = "2026-01-01",
    end_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="End delivery date (YYYY-MM-DD)",
            examples=["2026-01-31"],
        ),
    ] = "2026-01-31",
    cutoff: Annotated[
        str,
        Query(
            pattern=r"^\d{2}:\d{2}$",
            description="Cutoff time on D-1 in HH:MM (UTC)",
            examples=["09:00"],
        ),
    ] = settings.DEFAULT_CUTOFF_TIME,
) -> AccuracySummaryResponse:
    """Calculate aggregate forecast accuracy metrics (MAE, RMSE, Bias, nMAE, MAPE, P90, P95)."""
    merged_df = get_cutoff_joined_data_for_range(start_date, end_date, cutoff)
    metrics = compute_accuracy_metrics(merged_df)

    return AccuracySummaryResponse(
        start_date=start_date,
        end_date=end_date,
        cutoff_time=cutoff,
        **metrics,
    )


@router.get("/by-horizon", response_model=HorizonAccuracyResponse)
def get_accuracy_by_horizon() -> HorizonAccuracyResponse:
    """Analyze forecast error degradation across lead-time horizons (0-6h, 6-12h, ... 36-48h).

    Uses all forward forecast vintages in January 2026 to reveal how accuracy degrades with lead time.
    """
    repo = DataRepository()
    all_fc, all_act = repo.get_all_january_forecasts_and_actuals()
    buckets = aggregate_by_horizon(all_fc, all_act)
    return HorizonAccuracyResponse(buckets=buckets)  # type: ignore[arg-type]


@router.get("/by-hour", response_model=HourAccuracyResponse)
def get_accuracy_by_hour(
    start_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="Start delivery date (YYYY-MM-DD)",
            examples=["2026-01-01"],
        ),
    ] = "2026-01-01",
    end_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="End delivery date (YYYY-MM-DD)",
            examples=["2026-01-31"],
        ),
    ] = "2026-01-31",
    cutoff: Annotated[
        str,
        Query(
            pattern=r"^\d{2}:\d{2}$",
            description="Cutoff time on D-1 in HH:MM (UTC)",
            examples=["09:00"],
        ),
    ] = settings.DEFAULT_CUTOFF_TIME,
) -> HourAccuracyResponse:
    """Analyze diurnal error patterns and bias across 24 hours of the day."""
    merged_df = get_cutoff_joined_data_for_range(start_date, end_date, cutoff)
    hours = aggregate_by_hour(merged_df)
    return HourAccuracyResponse(hours=hours)  # type: ignore[arg-type]


@router.get("/by-wind-level", response_model=WindLevelAccuracyResponse)
def get_accuracy_by_wind_level(
    start_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="Start delivery date (YYYY-MM-DD)",
            examples=["2026-01-01"],
        ),
    ] = "2026-01-01",
    end_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="End delivery date (YYYY-MM-DD)",
            examples=["2026-01-31"],
        ),
    ] = "2026-01-31",
    cutoff: Annotated[
        str,
        Query(
            pattern=r"^\d{2}:\d{2}$",
            description="Cutoff time on D-1 in HH:MM (UTC)",
            examples=["09:00"],
        ),
    ] = settings.DEFAULT_CUTOFF_TIME,
) -> WindLevelAccuracyResponse:
    """Evaluate accuracy across wind regimes: Low (<6 GW), Medium (6-13 GW), High (>13 GW)."""
    merged_df = get_cutoff_joined_data_for_range(start_date, end_date, cutoff)
    regimes = aggregate_by_wind_level(merged_df)
    return WindLevelAccuracyResponse(regimes=regimes)  # type: ignore[arg-type]


@router.get("/buffer", response_model=BufferResponse)
def get_safety_buffer(
    confidence: Annotated[
        float,
        Query(
            ge=0.5,
            le=0.999,
            description="Confidence level for procurement shortfall coverage (0.50 - 0.999)",
            examples=[0.90],
        ),
    ] = 0.90,
    start_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="Start delivery date (YYYY-MM-DD)",
            examples=["2026-01-01"],
        ),
    ] = "2026-01-01",
    end_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="End delivery date (YYYY-MM-DD)",
            examples=["2026-01-31"],
        ),
    ] = "2026-01-31",
    cutoff: Annotated[
        str,
        Query(
            pattern=r"^\d{2}:\d{2}$",
            description="Cutoff time on D-1 in HH:MM (UTC)",
            examples=["09:00"],
        ),
    ] = settings.DEFAULT_CUTOFF_TIME,
) -> BufferResponse:
    """Compute statistically suggested procurement safety buffer in MW and deficit distributions."""
    merged_df = get_cutoff_joined_data_for_range(start_date, end_date, cutoff)
    buffer_data = calculate_safety_buffer(merged_df, confidence=confidence)
    return BufferResponse(**buffer_data)


@router.get("/distribution", response_model=ErrorDistributionResponse)
def get_error_distribution(
    start_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="Start delivery date (YYYY-MM-DD)",
            examples=["2026-01-01"],
        ),
    ] = "2026-01-01",
    end_date: Annotated[
        str,
        Query(
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="End delivery date (YYYY-MM-DD)",
            examples=["2026-01-31"],
        ),
    ] = "2026-01-31",
    cutoff: Annotated[
        str,
        Query(
            pattern=r"^\d{2}:\d{2}$",
            description="Cutoff time on D-1 in HH:MM (UTC)",
            examples=["09:00"],
        ),
    ] = settings.DEFAULT_CUTOFF_TIME,
    bins: Annotated[int, Query(ge=5, le=50, description="Histogram bin count")] = 15,
) -> ErrorDistributionResponse:
    """Return error histogram binning and quantiles for risk distribution analysis."""
    merged_df = get_cutoff_joined_data_for_range(start_date, end_date, cutoff)
    dist = compute_error_distribution(merged_df, bin_count=bins)
    return ErrorDistributionResponse(**dist)
