"""Unit tests for accuracy metrics against hand-computed reference values."""

import math

import numpy as np
import pandas as pd

from app.services.domain import compute_accuracy_metrics, join_forecasts_and_actuals


def test_metrics_hand_computed_values() -> None:
    """Test MAE, RMSE, Bias, nMAE, MAPE, P50, P90, P95 against manually computed ground truth.

    Ground truth dataset:
    Slot 0: F = 1000.0, A = 1200.0 -> err = -200.0, |err| = 200.0
    Slot 1: F = 2000.0, A = 1800.0 -> err = +200.0, |err| = 200.0
    Slot 2: F = 3000.0, A = 3000.0 -> err =    0.0, |err| =   0.0
    Slot 3: F = 4000.0, A = 3500.0 -> err = +500.0, |err| = 500.0

    Hand calculations:
    N = 4
    Mean Actual = (1200 + 1800 + 3000 + 3500) / 4 = 9500 / 4 = 2375.0 MW
    Mean Forecast = (1000 + 2000 + 3000 + 4000) / 4 = 10000 / 4 = 2500.0 MW
    MAE = (200 + 200 + 0 + 500) / 4 = 900 / 4 = 225.0 MW
    RMSE = sqrt((-200^2 + 200^2 + 0^2 + 500^2) / 4)
         = sqrt((40000 + 40000 + 0 + 250000) / 4)
         = sqrt(330000 / 4) = sqrt(82500) = 287.2281323... -> 287.2 MW
    Bias = (-200 + 200 + 0 + 500) / 4 = 500 / 4 = 125.0 MW
    nMAE = (225.0 / 2375.0) * 100 = 9.47368... -> 9.47%
    MAPE:
      Slot 0: |200| / 1200 = 0.16666...
      Slot 1: |200| / 1800 = 0.11111...
      Slot 2: |0| / 3000 = 0.0
      Slot 3: |500| / 3500 = 0.142857...
      Mean MAPE = (0.166667 + 0.111111 + 0 + 0.142857) / 4 * 100 = 42.0635 / 4 = 10.52%
    Abs errors: [0.0, 200.0, 200.0, 500.0]
    P50 (median) = 200.0 MW
    P90 = np.percentile([0, 200, 200, 500], 90) = 410.0 MW
    P95 = np.percentile([0, 200, 200, 500], 95) = 455.0 MW
    Max error = 500.0 MW
    """
    df = pd.DataFrame(
        {
            "startTime": [f"2026-01-15T0{i}:00:00Z" for i in range(4)],
            "forecast_mw": [1000.0, 2000.0, 3000.0, 4000.0],
            "actual_mw": [1200.0, 1800.0, 3000.0, 3500.0],
        }
    )

    metrics = compute_accuracy_metrics(df)

    assert metrics["sample_size"] == 4
    assert metrics["mean_actual_mw"] == 2375.0
    assert metrics["mean_forecast_mw"] == 2500.0
    assert metrics["mae"] == 225.0
    assert metrics["rmse"] == round(math.sqrt(82500), 1)
    assert metrics["bias"] == 125.0
    assert metrics["nmae_pct"] == 9.47
    assert metrics["mape_pct"] == 10.52
    assert metrics["p50_abs_error"] == 200.0
    assert metrics["max_abs_error"] == 500.0
    assert metrics["p90_abs_error"] == round(float(np.percentile([0, 200, 200, 500], 90)), 1)
    assert metrics["p95_abs_error"] == round(float(np.percentile([0, 200, 200, 500], 95)), 1)


def test_metrics_empty_dataframe() -> None:
    """Verify empty or missing data returns clean zeros rather than division-by-zero errors."""
    empty_df = pd.DataFrame(columns=["startTime", "forecast_mw", "actual_mw"])
    metrics = compute_accuracy_metrics(empty_df)
    assert metrics["sample_size"] == 0
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["bias"] == 0.0


def test_join_handles_missing_slots() -> None:
    """Verify join preserves slots where actual or forecast is missing without data corruption."""
    forecasts = pd.DataFrame(
        [
            {
                "startTime": "2026-01-15T00:00:00Z",
                "forecast_mw": 5000.0,
                "publishTime": "2026-01-14T08:00:00Z",
                "horizon_hours": 16.0,
            },
            # Slot 01:00 has forecast but actual dropped
            {
                "startTime": "2026-01-15T01:00:00Z",
                "forecast_mw": 6000.0,
                "publishTime": "2026-01-14T08:00:00Z",
                "horizon_hours": 17.0,
            },
        ]
    )

    actuals = pd.DataFrame(
        [
            {"startTime": "2026-01-15T00:00:00Z", "actual_mw": 4800.0},
            # Slot 02:00 has actual but no forecast available before cutoff
            {"startTime": "2026-01-15T02:00:00Z", "actual_mw": 7200.0},
        ]
    )

    merged = join_forecasts_and_actuals(forecasts, actuals)
    assert len(merged) == 3

    # Slot 00:00 has both
    row0 = merged[merged["startTime"] == "2026-01-15T00:00:00Z"].iloc[0]
    assert row0["forecast_mw"] == 5000.0
    assert row0["actual_mw"] == 4800.0
    assert row0["error"] == 200.0
    assert row0["shortfall"] == 200.0
    assert row0["surplus"] == 0.0

    # Slot 01:00 missing actual
    row1 = merged[merged["startTime"] == "2026-01-15T01:00:00Z"].iloc[0]
    assert row1["forecast_mw"] == 6000.0
    assert pd.isna(row1["actual_mw"])
    assert pd.isna(row1["error"])

    # Slot 02:00 missing forecast
    row2 = merged[merged["startTime"] == "2026-01-15T02:00:00Z"].iloc[0]
    assert pd.isna(row2["forecast_mw"])
    assert row2["actual_mw"] == 7200.0
    assert pd.isna(row2["error"])
