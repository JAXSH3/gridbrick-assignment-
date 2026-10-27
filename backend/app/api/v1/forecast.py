"""Forecast endpoints: cutoff-selected daily forecasts and vintage progression."""

from datetime import date
from typing import Annotated

import numpy as np
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.db.repository import DataRepository
from app.schemas.forecast import (
    DayForecastResponse,
    ForecastSlotItem,
    VintageItem,
    VintageResponse,
)
from app.services.domain import (
    format_utc_iso,
    get_cutoff_datetime,
    join_forecasts_and_actuals,
    select_latest_forecasts_at_cutoff,
)

router = APIRouter(prefix="/forecast", tags=["Forecasts"])


@router.get("/latest", response_model=DayForecastResponse)
def get_latest_forecast_for_delivery_day(
    target_date: Annotated[
        str,
        Query(
            ...,
            pattern=r"^\d{4}-\d{2}-\d{2}$",
            description="Delivery date (YYYY-MM-DD)",
            examples=["2026-01-15"],
        ),
    ],
    cutoff: Annotated[
        str,
        Query(
            pattern=r"^\d{2}:\d{2}$",
            description="Cutoff time on D-1 in HH:MM (UTC)",
            examples=["09:00"],
        ),
    ] = settings.DEFAULT_CUTOFF_TIME,
) -> DayForecastResponse:
    """Retrieve latest available wind forecast at day-ahead decision cutoff vs actuals.

    For each delivery slot on target_date, selects the forecast with the latest
    publishTime on or before the cutoff on D-1. Forecasts published after cutoff
    are strictly excluded.
    """
    try:
        t_date = date.fromisoformat(target_date)
        cutoff_dt = get_cutoff_datetime(t_date, cutoff)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    start_iso = f"{target_date}T00:00:00Z"
    end_iso = f"{target_date}T23:30:00Z"

    repo = DataRepository()
    actuals_df = repo.get_actuals_for_range(start_iso, end_iso)
    forecasts_df = repo.get_forecasts_for_targets(start_iso, end_iso)

    selected_fc = select_latest_forecasts_at_cutoff(forecasts_df, cutoff_dt)
    merged = join_forecasts_and_actuals(selected_fc, actuals_df)

    slots: list[ForecastSlotItem] = []
    has_missing_actuals = False
    has_missing_forecasts = False

    for _, row in merged.iterrows():
        f_val = float(row["forecast_mw"]) if pd_not_na(row.get("forecast_mw")) else None
        a_val = float(row["actual_mw"]) if pd_not_na(row.get("actual_mw")) else None
        err_val = float(row["error"]) if pd_not_na(row.get("error")) else None
        abs_err_val = float(row["abs_error"]) if pd_not_na(row.get("abs_error")) else None
        horiz_val = float(row["horizon_hours"]) if pd_not_na(row.get("horizon_hours")) else None
        pub_val = str(row["publishTime"]) if pd_not_na(row.get("publishTime")) else None

        if a_val is None:
            has_missing_actuals = True
        if f_val is None:
            has_missing_forecasts = True

        slots.append(
            ForecastSlotItem(
                start_time=str(row["startTime"]),
                publish_time=pub_val,
                forecast_mw=round(f_val, 1) if f_val is not None else None,
                actual_mw=round(a_val, 1) if a_val is not None else None,
                error_mw=round(err_val, 1) if err_val is not None else None,
                abs_error_mw=round(abs_err_val, 1) if abs_err_val is not None else None,
                horizon_hours=round(horiz_val, 1) if horiz_val is not None else None,
            )
        )

    return DayForecastResponse(
        target_date=target_date,
        cutoff_time=cutoff,
        cutoff_datetime=format_utc_iso(cutoff_dt),
        slots=slots,
        slot_count=len(slots),
        has_missing_actuals=has_missing_actuals,
        has_missing_forecasts=has_missing_forecasts,
    )


@router.get("/vintages", response_model=VintageResponse)
def get_forecast_vintages_for_slot(
    start_time: Annotated[
        str,
        Query(
            ...,
            description="Target delivery slot in ISO-8601 UTC",
            examples=["2026-01-15T12:00:00Z"],
        ),
    ],
) -> VintageResponse:
    """Retrieve all historical forecast publications for a single target slot.

    Displays how the forecast evolved across successive publications leading
    up to delivery, alongside the final outturn actual.
    """
    repo = DataRepository()
    actual_mw, raw_vintages = repo.get_vintages_for_slot(start_time)

    vintages = [
        VintageItem(
            start_time=v["start_time"],
            publish_time=v["publish_time"],
            forecast_mw=round(v["forecast_mw"], 1),
            horizon_hours=round(v["horizon_hours"], 1),
        )
        for v in raw_vintages
    ]

    return VintageResponse(
        start_time=start_time,
        actual_mw=round(actual_mw, 1) if actual_mw is not None else None,
        vintages=vintages,
        vintage_count=len(vintages),
    )


def pd_not_na(val: object) -> bool:
    """Check if object is not None or NaN."""
    if val is None:
        return False
    if isinstance(val, float) and (np.isnan(val) or val != val):
        return False
    return True
