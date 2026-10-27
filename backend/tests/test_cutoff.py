"""Unit tests for cutoff selection and anti-leakage guarantees."""

from datetime import UTC, date, datetime

import pandas as pd
import pytest

from app.services.domain import (
    get_cutoff_datetime,
    parse_time_string,
    select_latest_forecasts_at_cutoff,
)


def test_parse_time_string_valid() -> None:
    """Verify valid HH:MM strings parse to datetime.time."""
    t = parse_time_string("09:00")
    assert t.hour == 9
    assert t.minute == 0

    t2 = parse_time_string("23:45")
    assert t2.hour == 23
    assert t2.minute == 45


def test_parse_time_string_invalid() -> None:
    """Verify invalid strings raise ValueError."""
    with pytest.raises(ValueError):
        parse_time_string("9:0")
    with pytest.raises(ValueError):
        parse_time_string("25:00")
    with pytest.raises(ValueError):
        parse_time_string("invalid")


def test_get_cutoff_datetime_math() -> None:
    """Verify decision date is exactly D-1 at cutoff time in UTC."""
    target = date(2026, 1, 15)
    cutoff = get_cutoff_datetime(target, "09:00")
    assert cutoff == datetime(2026, 1, 14, 9, 0, 0, tzinfo=UTC)

    # Edge case: Jan 1 target has cutoff on Dec 31
    target_jan1 = date(2026, 1, 1)
    cutoff_jan1 = get_cutoff_datetime(target_jan1, "12:30")
    assert cutoff_jan1 == datetime(2025, 12, 31, 12, 30, 0, tzinfo=UTC)


def test_cutoff_anti_leakage_and_boundary() -> None:
    """CRITICAL TEST: Ensure exact boundary inclusion and strict exclusion of post-cutoff forecasts.

    Given a target slot 2026-01-15T12:00:00Z and cutoff at 2026-01-14T09:00:00Z:
    - Forecast 1: published 2026-01-14T07:00:00Z (valid, prior to cutoff)
    - Forecast 2: published 2026-01-14T09:00:00Z (EXACT BOUNDARY - must be included!)
    - Forecast 3: published 2026-01-14T09:00:01Z (1 sec after cutoff - MUST BE EXCLUDED!)
    - Forecast 4: published 2026-01-14T11:00:00Z (2 hours after cutoff - MUST BE EXCLUDED!)
    """
    cutoff_dt = datetime(2026, 1, 14, 9, 0, 0, tzinfo=UTC)
    target_slot = "2026-01-15T12:00:00Z"

    forecasts_df = pd.DataFrame(
        [
            {
                "startTime": target_slot,
                "publishTime": "2026-01-14T07:00:00Z",
                "forecast_mw": 10000.0,
                "horizon_hours": 29.0,
            },
            {
                "startTime": target_slot,
                "publishTime": "2026-01-14T09:00:00Z",  # Exact boundary!
                "forecast_mw": 11500.0,
                "horizon_hours": 27.0,
            },
            {
                "startTime": target_slot,
                "publishTime": "2026-01-14T09:00:01Z",  # 1 second after cutoff (leakage)
                "forecast_mw": 12000.0,
                "horizon_hours": 26.99,
            },
            {
                "startTime": target_slot,
                "publishTime": "2026-01-14T11:00:00Z",  # 2 hours after cutoff (leakage)
                "forecast_mw": 13000.0,
                "horizon_hours": 25.0,
            },
        ]
    )

    selected = select_latest_forecasts_at_cutoff(forecasts_df, cutoff_dt)

    assert len(selected) == 1
    row = selected.iloc[0]
    # Must select the exact boundary row (11500.0 MW), NOT the post-cutoff ones
    assert row["publishTime"] == "2026-01-14T09:00:00Z"
    assert row["forecast_mw"] == 11500.0
    assert row["horizon_hours"] == 27.0


def test_multiple_target_slots_selection() -> None:
    """Verify that each target slot independently selects its latest eligible vintage."""
    cutoff_dt = datetime(2026, 1, 14, 9, 0, 0, tzinfo=UTC)

    forecasts_df = pd.DataFrame(
        [
            # Slot 1
            {
                "startTime": "2026-01-15T00:00:00Z",
                "publishTime": "2026-01-14T06:00:00Z",
                "forecast_mw": 5000.0,
                "horizon_hours": 18.0,
            },
            {
                "startTime": "2026-01-15T00:00:00Z",
                "publishTime": "2026-01-14T08:30:00Z",
                "forecast_mw": 5200.0,
                "horizon_hours": 15.5,
            },
            # Slot 2 (only early forecast available before cutoff)
            {
                "startTime": "2026-01-15T01:00:00Z",
                "publishTime": "2026-01-14T03:00:00Z",
                "forecast_mw": 6000.0,
                "horizon_hours": 22.0,
            },
            {
                "startTime": "2026-01-15T01:00:00Z",
                "publishTime": "2026-01-14T10:00:00Z",  # after cutoff
                "forecast_mw": 6500.0,
                "horizon_hours": 15.0,
            },
        ]
    )

    selected = select_latest_forecasts_at_cutoff(forecasts_df, cutoff_dt)
    assert len(selected) == 2

    s0 = selected[selected["startTime"] == "2026-01-15T00:00:00Z"].iloc[0]
    assert s0["publishTime"] == "2026-01-14T08:30:00Z"
    assert s0["forecast_mw"] == 5200.0

    s1 = selected[selected["startTime"] == "2026-01-15T01:00:00Z"].iloc[0]
    assert s1["publishTime"] == "2026-01-14T03:00:00Z"
    assert s1["forecast_mw"] == 6000.0


def test_empty_forecasts_returns_empty_dataframe() -> None:
    """Verify empty input dataframe does not crash and returns appropriate columns."""
    cutoff_dt = datetime(2026, 1, 14, 9, 0, 0, tzinfo=UTC)
    empty_df = pd.DataFrame()
    selected = select_latest_forecasts_at_cutoff(empty_df, cutoff_dt)
    assert selected.empty
    assert "startTime" in selected.columns
    assert "forecast_mw" in selected.columns
