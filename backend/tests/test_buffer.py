"""Unit tests for safety buffer sizing and deficit/surplus distributions."""

import numpy as np
import pandas as pd

from app.services.domain import calculate_safety_buffer


def test_buffer_calculation_exact_quantiles() -> None:
    """Test safety buffer sizing logic against known shortfall distribution.

    10 slots:
    Slot 0: F = 1000, A = 1200 -> err = -200 (surplus, shortfall = 0)
    Slot 1: F = 1000, A = 1100 -> err = -100 (surplus, shortfall = 0)
    Slot 2: F = 1000, A = 1050 -> err = -50  (surplus, shortfall = 0)
    Slot 3: F = 1000, A = 1000 -> err = 0    (shortfall = 0)
    Slot 4: F = 1000, A = 900  -> err = +100 (shortfall = 100)
    Slot 5: F = 1000, A = 800  -> err = +200 (shortfall = 200)
    Slot 6: F = 1000, A = 700  -> err = +300 (shortfall = 300)
    Slot 7: F = 1000, A = 600  -> err = +400 (shortfall = 400)
    Slot 8: F = 1000, A = 500  -> err = +500 (shortfall = 500)
    Slot 9: F = 1000, A = 0    -> err = +1000 (shortfall = 1000)

    Shortfall array: [0, 0, 0, 0, 100, 200, 300, 400, 500, 1000]
    90th percentile of shortfalls = np.percentile(shortfall, 90) = 550.0 MW
    Over-forecast (shortfall) count = 6 (60.0%)
    Under-forecast (surplus) count = 3 (30.0%)
    Mean shortfall on deficit periods = (100+200+300+400+500+1000) / 6 = 2500 / 6 = 416.7 MW
    """
    df = pd.DataFrame(
        {
            "forecast_mw": [1000.0] * 10,
            "actual_mw": [1200.0, 1100.0, 1050.0, 1000.0, 900.0, 800.0, 700.0, 600.0, 500.0, 0.0],
        }
    )

    res = calculate_safety_buffer(df, confidence=0.90)

    assert res["over_forecast_count"] == 6
    assert res["under_forecast_count"] == 3
    assert res["over_forecast_pct"] == 60.0
    assert res["under_forecast_pct"] == 30.0
    assert res["mean_shortfall_mw"] == round(2500.0 / 6.0, 1)

    expected_p90 = round(float(np.percentile([0, 0, 0, 0, 100, 200, 300, 400, 500, 1000], 90)), 1)
    assert res["buffer_90_mw"] == expected_p90
    assert res["recommended_buffer_mw"] == expected_p90
    assert (
        "safety buffer ensures that day-ahead wind shortfalls are fully covered"
        in res["recommendation_text"]
    )


def test_buffer_empty_dataframe() -> None:
    """Verify empty input returns zeroed metrics without crashing."""
    df = pd.DataFrame(columns=["forecast_mw", "actual_mw"])
    res = calculate_safety_buffer(df)
    assert res["recommended_buffer_mw"] == 0.0
    assert res["over_forecast_count"] == 0
    assert res["under_forecast_count"] == 0
