"""Unit tests for horizon degradation, diurnal, wind level, and distribution aggregations."""

import pandas as pd

from app.services.domain import (
    aggregate_by_horizon,
    aggregate_by_hour,
    aggregate_by_wind_level,
    compute_error_distribution,
)


def test_aggregate_by_horizon() -> None:
    """Verify forecasts are correctly bucketed into lead time horizon bins."""
    actuals = pd.DataFrame(
        [
            {"startTime": "2026-01-15T12:00:00Z", "actual_mw": 5000.0},
            {"startTime": "2026-01-15T18:00:00Z", "actual_mw": 8000.0},
        ]
    )

    forecasts = pd.DataFrame(
        [
            # 4h horizon -> 0-6h bucket
            {
                "startTime": "2026-01-15T12:00:00Z",
                "publishTime": "2026-01-15T08:00:00Z",
                "forecast_mw": 5200.0,
                "horizon_hours": 4.0,
            },
            # 16h horizon -> 12-18h bucket
            {
                "startTime": "2026-01-15T12:00:00Z",
                "publishTime": "2026-01-14T20:00:00Z",
                "forecast_mw": 5500.0,
                "horizon_hours": 16.0,
            },
            # 22h horizon -> 18-24h bucket
            {
                "startTime": "2026-01-15T18:00:00Z",
                "publishTime": "2026-01-14T20:00:00Z",
                "forecast_mw": 7500.0,
                "horizon_hours": 22.0,
            },
        ]
    )

    results = aggregate_by_horizon(forecasts, actuals)
    assert len(results) == 7  # 7 standard buckets

    b0_6 = next(b for b in results if b["bucket"] == "0-6h")
    assert b0_6["sample_size"] == 1
    assert b0_6["mae"] == 200.0  # |5200 - 5000|

    b12_18 = next(b for b in results if b["bucket"] == "12-18h")
    assert b12_18["sample_size"] == 1
    assert b12_18["mae"] == 500.0  # |5500 - 5000|

    b18_24 = next(b for b in results if b["bucket"] == "18-24h")
    assert b18_24["sample_size"] == 1
    assert b18_24["mae"] == 500.0  # |7500 - 8000|


def test_aggregate_by_hour() -> None:
    """Verify slots are correctly aggregated by diurnal hour."""
    merged = pd.DataFrame(
        [
            {"startTime": "2026-01-15T08:00:00Z", "forecast_mw": 4000.0, "actual_mw": 3800.0},
            {"startTime": "2026-01-16T08:00:00Z", "forecast_mw": 4200.0, "actual_mw": 4000.0},
            {"startTime": "2026-01-15T14:00:00Z", "forecast_mw": 7000.0, "actual_mw": 7500.0},
        ]
    )

    hours = aggregate_by_hour(merged)
    assert len(hours) == 2  # hour 8 and hour 14

    h8 = next(h for h in hours if h["hour"] == 8)
    assert h8["sample_size"] == 2
    assert h8["mae"] == 200.0
    assert h8["bias"] == 200.0

    h14 = next(h for h in hours if h["hour"] == 14)
    assert h14["sample_size"] == 1
    assert h14["mae"] == 500.0
    assert h14["bias"] == -500.0


def test_aggregate_by_wind_level() -> None:
    """Verify grouping into Low, Medium, High wind regimes."""
    merged = pd.DataFrame(
        [
            # Low (< 6000 MW)
            {"forecast_mw": 3500.0, "actual_mw": 3000.0},
            # Medium (6000 - 13000 MW)
            {"forecast_mw": 9000.0, "actual_mw": 10000.0},
            # High (> 13000 MW)
            {"forecast_mw": 15000.0, "actual_mw": 16000.0},
        ]
    )

    regimes = aggregate_by_wind_level(merged)
    assert len(regimes) == 3

    low = next(r for r in regimes if r["regime"] == "Low")
    assert low["sample_size"] == 1
    assert low["mae"] == 500.0

    med = next(r for r in regimes if r["regime"] == "Medium")
    assert med["sample_size"] == 1
    assert med["mae"] == 1000.0

    high = next(r for r in regimes if r["regime"] == "High")
    assert high["sample_size"] == 1
    assert high["mae"] == 1000.0


def test_compute_error_distribution() -> None:
    """Verify histogram binning returns valid bins and quantiles."""
    merged = pd.DataFrame(
        {
            "forecast_mw": [1000.0, 2000.0, 3000.0, 4000.0, 5000.0],
            "actual_mw": [1200.0, 1900.0, 3000.0, 3800.0, 4800.0],
        }
    )

    dist = compute_error_distribution(merged, bin_count=5)
    assert "bins" in dist
    assert len(dist["bins"]) == 5
    assert "quantiles" in dist
    assert "p50" in dist["quantiles"]
    assert "p90" in dist["quantiles"]
