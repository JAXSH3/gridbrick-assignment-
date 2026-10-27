"""Integration tests for all FastAPI v1 endpoints using TestClient."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health_endpoint() -> None:
    """Verify /api/v1/health returns database connectivity and positive counts."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["total_actuals_rows"] >= 1488
    assert data["total_forecasts_rows"] >= 10000
    assert "X-Request-ID" in response.headers


def test_api_forecast_latest_jan15() -> None:
    """Verify /api/v1/forecast/latest returns valid day-ahead forecasts for 2026-01-15.

    Ensures that for cutoff 09:00 UTC, no forecast published after
    2026-01-14T09:00:00Z is leaked into the response.
    """
    response = client.get("/api/v1/forecast/latest?target_date=2026-01-15&cutoff=09:00")
    assert response.status_code == 200
    data = response.json()

    assert data["target_date"] == "2026-01-15"
    assert data["cutoff_time"] == "09:00"
    assert data["cutoff_datetime"] == "2026-01-14T09:00:00Z"
    assert data["slot_count"] >= 24

    cutoff_boundary = "2026-01-14T09:00:00Z"
    for slot in data["slots"]:
        assert "start_time" in slot
        if slot["publish_time"]:
            # ANTI-LEAKAGE ASSERTION: publish_time <= cutoff on D-1
            assert slot["publish_time"] <= cutoff_boundary


def test_api_forecast_latest_validation_error() -> None:
    """Verify invalid date or cutoff format triggers 422 Unprocessable Entity."""
    # Bad date format
    resp1 = client.get("/api/v1/forecast/latest?target_date=15-01-2026&cutoff=09:00")
    assert resp1.status_code == 422

    # Bad cutoff format
    resp2 = client.get("/api/v1/forecast/latest?target_date=2026-01-15&cutoff=9am")
    assert resp2.status_code == 422


def test_api_forecast_vintages() -> None:
    """Verify /api/v1/forecast/vintages returns successive forecast publications."""
    slot = "2026-01-15T12:00:00Z"
    response = client.get(f"/api/v1/forecast/vintages?start_time={slot}")
    assert response.status_code == 200
    data = response.json()

    assert data["start_time"] == slot
    assert data["actual_mw"] is not None
    assert data["vintage_count"] >= 5
    assert len(data["vintages"]) == data["vintage_count"]

    # Vintages should be sorted by publishTime
    pub_times = [v["publish_time"] for v in data["vintages"]]
    assert pub_times == sorted(pub_times)


def test_api_accuracy_summary_full_month() -> None:
    """Verify /api/v1/accuracy/summary computes valid metrics over January 2026."""
    response = client.get(
        "/api/v1/accuracy/summary?start_date=2026-01-01&end_date=2026-01-31&cutoff=09:00"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["sample_size"] == 744  # 31 days * 24 hourly forecast slots
    assert data["mean_actual_mw"] > 5000.0
    assert data["mae"] > 0.0
    assert data["rmse"] >= data["mae"]
    assert data["p90_abs_error"] >= data["p50_abs_error"]
    assert data["nmae_pct"] > 0.0


def test_api_accuracy_by_horizon() -> None:
    """Verify /api/v1/accuracy/by-horizon returns 7 lead-time buckets with increasing MAE."""
    response = client.get("/api/v1/accuracy/by-horizon")
    assert response.status_code == 200
    data = response.json()

    assert "buckets" in data
    assert len(data["buckets"]) == 7
    # 0-6h bucket should have lower MAE than 36-48h bucket (forecast degrades with horizon)
    b0_6 = data["buckets"][0]
    b36_48 = data["buckets"][-1]
    assert b0_6["bucket"] == "0-6h"
    assert b36_48["bucket"] == "36-48h"
    assert b0_6["mae"] <= b36_48["mae"]


def test_api_accuracy_by_hour() -> None:
    """Verify /api/v1/accuracy/by-hour returns diurnal breakdown across 24 hours."""
    response = client.get("/api/v1/accuracy/by-hour")
    assert response.status_code == 200
    data = response.json()

    assert "hours" in data
    assert len(data["hours"]) == 24
    assert data["hours"][0]["hour"] == 0
    assert data["hours"][23]["hour"] == 23


def test_api_accuracy_by_wind_level() -> None:
    """Verify /api/v1/accuracy/by-wind-level returns Low, Medium, High regimes."""
    response = client.get("/api/v1/accuracy/by-wind-level")
    assert response.status_code == 200
    data = response.json()

    assert "regimes" in data
    assert len(data["regimes"]) == 3
    regime_names = [r["regime"] for r in data["regimes"]]
    assert regime_names == ["Low", "Medium", "High"]


def test_api_accuracy_buffer() -> None:
    """Verify /api/v1/accuracy/buffer suggests positive MW safety buffers."""
    response = client.get("/api/v1/accuracy/buffer?confidence=0.90")
    assert response.status_code == 200
    data = response.json()

    assert data["confidence"] == 0.90
    assert data["recommended_buffer_mw"] > 0.0
    assert data["buffer_90_mw"] > 0.0
    assert data["buffer_95_mw"] >= data["buffer_90_mw"]
    assert data["over_forecast_count"] + data["under_forecast_count"] == 744
    assert (
        "safety buffer ensures that day-ahead wind shortfalls are fully covered"
        in data["recommendation_text"]
    )


def test_api_accuracy_distribution() -> None:
    """Verify /api/v1/accuracy/distribution returns error bins and quantiles."""
    response = client.get("/api/v1/accuracy/distribution?bins=15")
    assert response.status_code == 200
    data = response.json()

    assert "bins" in data
    assert len(data["bins"]) == 15
    assert "quantiles" in data
    assert "p10" in data["quantiles"]
    assert "p50" in data["quantiles"]
    assert "p90" in data["quantiles"]
