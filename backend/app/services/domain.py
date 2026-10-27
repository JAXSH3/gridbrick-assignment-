"""Pure domain logic for wind forecast cutoff selection, metrics, and buffer sizing.

This module contains no I/O or network logic. All functions are pure, deterministic,
and thoroughly unit-tested.
"""

import math
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import numpy as np
import pandas as pd

# Default generation regime thresholds in MW
LOW_WIND_THRESHOLD_MW = 6000.0
HIGH_WIND_THRESHOLD_MW = 13000.0

HORIZON_BUCKET_EDGES = [
    (0.0, 6.0, "0-6h"),
    (6.0, 12.0, "6-12h"),
    (12.0, 18.0, "12-18h"),
    (18.0, 24.0, "18-24h"),
    (24.0, 30.0, "24-30h"),
    (30.0, 36.0, "30-36h"),
    (36.0, 48.0, "36-48h"),
]


def parse_time_string(time_str: str) -> time:
    """Parse 'HH:MM' string into a datetime.time object."""
    parts = time_str.strip().split(":")
    if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 2:
        raise ValueError(f"Invalid cutoff time format '{time_str}'. Expected 'HH:MM'.")
    if not (parts[0].isdigit() and parts[1].isdigit()):
        raise ValueError(f"Cutoff time '{time_str}' must contain numeric digits.")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Cutoff time '{time_str}' out of range.")
    return time(hour, minute)


def get_cutoff_datetime(target_date: date, cutoff_str: str = "09:00") -> datetime:
    """Calculate the decision cutoff timestamp on day D-1 in UTC.

    For a power delivery day D, day-ahead purchase decisions are finalized
    on D-1 at the designated cutoff time (default 09:00 UTC).
    """
    cutoff_time = parse_time_string(cutoff_str)
    decision_date = target_date - timedelta(days=1)
    return datetime.combine(decision_date, cutoff_time, tzinfo=UTC)


def select_latest_forecasts_at_cutoff(
    forecasts_df: pd.DataFrame,
    cutoff_dt: datetime,
) -> pd.DataFrame:
    """Select the latest available forecast published on or before the cutoff.

    CRITICAL ANTI-LEAKAGE RULES:
    1. Filter: publishTime <= cutoff_dt.
       - Rows with publishTime == cutoff_dt ARE valid and included (exact boundary).
       - Rows with publishTime > cutoff_dt ARE strictly excluded (no look-ahead leakage).
    2. Group by target startTime and select the row with the maximum publishTime.

    Args:
        forecasts_df: DataFrame with ['startTime', 'publishTime', 'forecast_mw', 'horizon_hours']
        cutoff_dt: UTC datetime cutoff timestamp on D-1.

    Returns:
        DataFrame containing one row per startTime with the latest forecast at decision time.
    """
    if forecasts_df.empty:
        return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw", "horizon_hours"])

    # Ensure UTC datetime comparisons
    df = forecasts_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["publishTime"]):
        df["publish_dt"] = pd.to_datetime(df["publishTime"], utc=True)
    else:
        df["publish_dt"] = df["publishTime"]

    # Filter <= cutoff (boundary inclusive)
    cutoff_ts = pd.Timestamp(cutoff_dt)
    valid_mask = df["publish_dt"] <= cutoff_ts
    valid_df = df[valid_mask]

    if valid_df.empty:
        return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw", "horizon_hours"])

    # For each startTime, pick the record with max publishTime
    idx_latest = valid_df.groupby("startTime")["publish_dt"].idxmax()
    selected = valid_df.loc[idx_latest].sort_values("startTime").reset_index(drop=True)

    cols = ["startTime", "publishTime", "forecast_mw", "horizon_hours"]
    return selected[[c for c in cols if c in selected.columns]]


def join_forecasts_and_actuals(
    forecasts_df: pd.DataFrame,
    actuals_df: pd.DataFrame,
) -> pd.DataFrame:
    """Join cutoff-selected forecasts with actuals on target startTime.

    Computes:
    - error: forecast_mw - actual_mw (positive = over-forecast, negative = under-forecast)
    - abs_error: |forecast_mw - actual_mw|
    - shortfall: max(0, forecast_mw - actual_mw) (utility deficit risk)
    - surplus: max(0, actual_mw - forecast_mw) (utility surplus wind)

    Args:
        forecasts_df: DataFrame with ['startTime', 'forecast_mw', 'publishTime', 'horizon_hours']
        actuals_df: DataFrame with ['startTime', 'actual_mw']

    Returns:
        DataFrame with aligned slots and computed error fields.
    """
    if actuals_df.empty and forecasts_df.empty:
        return pd.DataFrame(
            columns=[
                "startTime",
                "forecast_mw",
                "actual_mw",
                "publishTime",
                "horizon_hours",
                "error",
                "abs_error",
                "shortfall",
                "surplus",
            ]
        )

    if forecasts_df.empty:
        merged = actuals_df.copy()
        merged["forecast_mw"] = np.nan
        merged["publishTime"] = None
        merged["horizon_hours"] = np.nan
    elif actuals_df.empty:
        merged = forecasts_df.copy()
        merged["actual_mw"] = np.nan
    else:
        merged = pd.merge(actuals_df, forecasts_df, on="startTime", how="outer")

    merged = merged.sort_values("startTime").reset_index(drop=True)

    # Compute error metrics where both forecast and actual exist
    has_both = merged["forecast_mw"].notna() & merged["actual_mw"].notna()

    merged["error"] = np.nan
    merged["abs_error"] = np.nan
    merged["shortfall"] = np.nan
    merged["surplus"] = np.nan

    if has_both.any():
        f = merged.loc[has_both, "forecast_mw"]
        a = merged.loc[has_both, "actual_mw"]
        err = f - a
        merged.loc[has_both, "error"] = err
        merged.loc[has_both, "abs_error"] = np.abs(err)
        merged.loc[has_both, "shortfall"] = np.maximum(0.0, err)
        merged.loc[has_both, "surplus"] = np.maximum(0.0, -err)

    return merged


def compute_accuracy_metrics(merged_df: pd.DataFrame) -> dict[str, Any]:
    """Calculate key forecast accuracy metrics over paired slots.

    Metrics:
    - MAE: Mean Absolute Error (MW)
    - RMSE: Root Mean Squared Error (MW)
    - Bias: Mean Error (forecast - actual) (MW)
    - nMAE: Normalized MAE (% of mean actual generation)
    - MAPE: Mean Absolute Percentage Error (%) for slots where actual > 50 MW
    - P50, P90, P95: Percentiles of absolute error (MW)
    """
    valid = merged_df[merged_df["forecast_mw"].notna() & merged_df["actual_mw"].notna()]
    n = len(valid)

    if n == 0:
        return {
            "sample_size": 0,
            "mean_actual_mw": 0.0,
            "mean_forecast_mw": 0.0,
            "mae": 0.0,
            "rmse": 0.0,
            "bias": 0.0,
            "nmae_pct": 0.0,
            "mape_pct": 0.0,
            "p50_abs_error": 0.0,
            "p90_abs_error": 0.0,
            "p95_abs_error": 0.0,
            "max_abs_error": 0.0,
        }

    f = valid["forecast_mw"].to_numpy()
    a = valid["actual_mw"].to_numpy()
    err = f - a
    abs_err = np.abs(err)

    mae = float(np.mean(abs_err))
    rmse = float(math.sqrt(np.mean(err**2)))
    bias = float(np.mean(err))

    mean_a = float(np.mean(a))
    mean_f = float(np.mean(f))

    # Normalized MAE: industry-standard for grid operations (capacity/mean normalized)
    nmae_pct = round((mae / mean_a * 100.0), 2) if mean_a > 0 else 0.0

    # Traditional MAPE filtered for non-near-zero actuals
    mask_pos = a > 50.0
    if mask_pos.any():
        mape_pct = round(float(np.mean(abs_err[mask_pos] / a[mask_pos]) * 100.0), 2)
    else:
        mape_pct = 0.0

    p50 = float(np.percentile(abs_err, 50))
    p90 = float(np.percentile(abs_err, 90))
    p95 = float(np.percentile(abs_err, 95))
    max_err = float(np.max(abs_err))

    return {
        "sample_size": n,
        "mean_actual_mw": round(mean_a, 1),
        "mean_forecast_mw": round(mean_f, 1),
        "mae": round(mae, 1),
        "rmse": round(rmse, 1),
        "bias": round(bias, 1),
        "nmae_pct": nmae_pct,
        "mape_pct": mape_pct,
        "p50_abs_error": round(p50, 1),
        "p90_abs_error": round(p90, 1),
        "p95_abs_error": round(p95, 1),
        "max_abs_error": round(max_err, 1),
    }


def calculate_safety_buffer(
    merged_df: pd.DataFrame,
    confidence: float = 0.90,
) -> dict[str, Any]:
    """Calculate statistical procurement safety buffer and deficit distribution.

    Decision Support Logic:
    When a trader relies on wind forecast F, if actual A < F, the utility is short.
    Shortfall S = max(0, F - A).
    The safety buffer B at confidence C ensures that shortfalls exceed B at most
    (1 - C) of the time.

    Args:
        merged_df: Paired DataFrame with 'forecast_mw' and 'actual_mw'.
        confidence: Confidence level (e.g. 0.90 or 0.95).

    Returns:
        Safety buffer recommendation in MW, quantiles, and under/over distributions.
    """
    valid = merged_df[merged_df["forecast_mw"].notna() & merged_df["actual_mw"].notna()]
    n = len(valid)

    if n == 0:
        return {
            "confidence": confidence,
            "recommended_buffer_mw": 0.0,
            "buffer_90_mw": 0.0,
            "buffer_95_mw": 0.0,
            "over_forecast_count": 0,
            "under_forecast_count": 0,
            "over_forecast_pct": 0.0,
            "under_forecast_pct": 0.0,
            "mean_shortfall_mw": 0.0,
            "p90_shortfall_mw": 0.0,
            "p95_shortfall_mw": 0.0,
            "recommendation_text": "Insufficient paired data to compute buffer.",
        }

    f = valid["forecast_mw"].to_numpy()
    a = valid["actual_mw"].to_numpy()
    err = f - a

    # Shortfall: deficit when forecast > actual
    shortfalls = np.maximum(0.0, err)

    # Calculate buffer at requested confidence, as well as standards 90% and 95%
    buf_user = float(np.percentile(shortfalls, confidence * 100.0))
    buf_90 = float(np.percentile(shortfalls, 90.0))
    buf_95 = float(np.percentile(shortfalls, 95.0))

    # Over-forecast vs Under-forecast distributions
    over_mask = err > 0
    under_mask = err < 0

    over_count = int(np.sum(over_mask))
    under_count = int(np.sum(under_mask))
    over_pct = round(over_count / n * 100.0, 1)
    under_pct = round(under_count / n * 100.0, 1)

    mean_shortfall = float(np.mean(err[over_mask])) if over_count > 0 else 0.0
    p90_shortfall = float(np.percentile(err[over_mask], 90.0)) if over_count > 0 else 0.0
    p95_shortfall = float(np.percentile(err[over_mask], 95.0)) if over_count > 0 else 0.0

    mean_surplus = float(np.mean(-err[under_mask])) if under_count > 0 else 0.0
    p90_surplus = float(np.percentile(-err[under_mask], 90.0)) if under_count > 0 else 0.0

    rec_text = (
        f"At {confidence * 100:.0f}% confidence, maintaining a {buf_user:.0f} MW procurement "
        f"safety buffer ensures that day-ahead wind shortfalls are fully covered in "
        f"{confidence * 100:.0f}% of delivery settlement periods."
    )

    return {
        "confidence": confidence,
        "recommended_buffer_mw": round(buf_user, 1),
        "buffer_90_mw": round(buf_90, 1),
        "buffer_95_mw": round(buf_95, 1),
        "over_forecast_count": over_count,
        "under_forecast_count": under_count,
        "over_forecast_pct": over_pct,
        "under_forecast_pct": under_pct,
        "mean_shortfall_mw": round(mean_shortfall, 1),
        "p90_shortfall_mw": round(p90_shortfall, 1),
        "p95_shortfall_mw": round(p95_shortfall, 1),
        "mean_surplus_mw": round(mean_surplus, 1),
        "p90_surplus_mw": round(p90_surplus, 1),
        "recommendation_text": rec_text,
    }


def aggregate_by_horizon(
    all_forecasts_df: pd.DataFrame,
    actuals_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Analyze forecast error degradation by lead-time horizon.

    Uses all forward forecasts (horizon >= 0) joined with actuals.
    """
    if all_forecasts_df.empty or actuals_df.empty:
        return []

    # Join all forecast vintages with actuals on target startTime
    merged = pd.merge(all_forecasts_df, actuals_df, on="startTime", how="inner")
    forward = merged[merged["horizon_hours"] >= 0].copy()

    results: list[dict[str, Any]] = []
    for low, high, label in HORIZON_BUCKET_EDGES:
        mask = (forward["horizon_hours"] >= low) & (forward["horizon_hours"] < high)
        bucket = forward[mask]
        if bucket.empty:
            results.append(
                {
                    "bucket": label,
                    "min_hours": low,
                    "max_hours": high,
                    "sample_size": 0,
                    "mae": 0.0,
                    "rmse": 0.0,
                    "bias": 0.0,
                    "p90_abs_error": 0.0,
                }
            )
            continue

        f = bucket["forecast_mw"].to_numpy()
        a = bucket["actual_mw"].to_numpy()
        err = f - a
        abs_err = np.abs(err)

        results.append(
            {
                "bucket": label,
                "min_hours": low,
                "max_hours": high,
                "sample_size": len(bucket),
                "mae": round(float(np.mean(abs_err)), 1),
                "rmse": round(float(math.sqrt(np.mean(err**2))), 1),
                "bias": round(float(np.mean(err)), 1),
                "p90_abs_error": round(float(np.percentile(abs_err, 90)), 1),
            }
        )

    return results


def aggregate_by_hour(merged_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Analyze forecast error and bias across 24 diurnal hours of the day."""
    valid = merged_df[merged_df["forecast_mw"].notna() & merged_df["actual_mw"].notna()].copy()
    if valid.empty:
        return []

    # Extract hour of day (0 to 23) from startTime
    valid["hour"] = pd.to_datetime(valid["startTime"], utc=True).dt.hour

    results: list[dict[str, Any]] = []
    for h in range(24):
        slot_df = valid[valid["hour"] == h]
        if slot_df.empty:
            continue

        f = slot_df["forecast_mw"].to_numpy()
        a = slot_df["actual_mw"].to_numpy()
        err = f - a
        abs_err = np.abs(err)

        results.append(
            {
                "hour": h,
                "hour_label": f"{h:02d}:00",
                "sample_size": len(slot_df),
                "avg_actual_mw": round(float(np.mean(a)), 1),
                "avg_forecast_mw": round(float(np.mean(f)), 1),
                "mae": round(float(np.mean(abs_err)), 1),
                "rmse": round(float(math.sqrt(np.mean(err**2))), 1),
                "bias": round(float(np.mean(err)), 1),
            }
        )

    return results


def aggregate_by_wind_level(
    merged_df: pd.DataFrame,
    low_threshold: float = LOW_WIND_THRESHOLD_MW,
    high_threshold: float = HIGH_WIND_THRESHOLD_MW,
) -> list[dict[str, Any]]:
    """Analyze forecast accuracy across low, medium, and high actual wind regimes."""
    valid = merged_df[merged_df["forecast_mw"].notna() & merged_df["actual_mw"].notna()].copy()
    if valid.empty:
        return []

    regimes = [
        ("Low", valid["actual_mw"] < low_threshold, f"< {low_threshold / 1000:.0f} GW"),
        (
            "Medium",
            (valid["actual_mw"] >= low_threshold) & (valid["actual_mw"] < high_threshold),
            f"{low_threshold / 1000:.0f} - {high_threshold / 1000:.0f} GW",
        ),
        ("High", valid["actual_mw"] >= high_threshold, f"> {high_threshold / 1000:.0f} GW"),
    ]

    results: list[dict[str, Any]] = []
    for name, mask, range_label in regimes:
        sub = valid[mask]
        if sub.empty:
            results.append(
                {
                    "regime": name,
                    "range_label": range_label,
                    "sample_size": 0,
                    "mean_actual_mw": 0.0,
                    "mae": 0.0,
                    "rmse": 0.0,
                    "bias": 0.0,
                    "nmae_pct": 0.0,
                }
            )
            continue

        f = sub["forecast_mw"].to_numpy()
        a = sub["actual_mw"].to_numpy()
        err = f - a
        abs_err = np.abs(err)
        mean_a = float(np.mean(a))
        mae = float(np.mean(abs_err))

        results.append(
            {
                "regime": name,
                "range_label": range_label,
                "sample_size": len(sub),
                "mean_actual_mw": round(mean_a, 1),
                "mae": round(mae, 1),
                "rmse": round(float(math.sqrt(np.mean(err**2))), 1),
                "bias": round(float(np.mean(err)), 1),
                "nmae_pct": round(mae / mean_a * 100.0, 2) if mean_a > 0 else 0.0,
            }
        )

    return results


def compute_error_distribution(
    merged_df: pd.DataFrame,
    bin_count: int = 15,
) -> dict[str, Any]:
    """Compute histogram binning and quantiles of forecast errors (F - A)."""
    valid = merged_df[merged_df["forecast_mw"].notna() & merged_df["actual_mw"].notna()]
    if valid.empty:
        return {"bins": [], "quantiles": {}}

    err = (valid["forecast_mw"] - valid["actual_mw"]).to_numpy()
    counts, bin_edges = np.histogram(err, bins=bin_count)

    bins_list = []
    for i in range(len(counts)):
        mid = float((bin_edges[i] + bin_edges[i + 1]) / 2.0)
        bins_list.append(
            {
                "bin_start": round(float(bin_edges[i]), 1),
                "bin_end": round(float(bin_edges[i + 1]), 1),
                "bin_mid": round(mid, 1),
                "count": int(counts[i]),
                "type": "Shortfall (F > A)" if mid > 0 else "Surplus (A > F)",
            }
        )

    quantiles = {
        "p05": round(float(np.percentile(err, 5)), 1),
        "p10": round(float(np.percentile(err, 10)), 1),
        "p25": round(float(np.percentile(err, 25)), 1),
        "p50": round(float(np.percentile(err, 50)), 1),
        "p75": round(float(np.percentile(err, 75)), 1),
        "p90": round(float(np.percentile(err, 90)), 1),
        "p95": round(float(np.percentile(err, 95)), 1),
    }

    return {"bins": bins_list, "quantiles": quantiles}
