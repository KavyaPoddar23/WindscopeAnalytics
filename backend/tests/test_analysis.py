import pytest

from app.analysis import (
    build_analysis,
    calculate_metrics,
    decision_cutoff,
    parse_time
)


def test_decision_cutoff():
    delivery = parse_time("2026-01-15T10:00:00Z")

    cutoff = decision_cutoff(delivery)

    assert cutoff.isoformat() == (
        "2026-01-14T12:00:00+00:00"
    )


def test_selects_latest_eligible_forecast():
    actuals = [
        {
            "fuelType": "WIND",
            "startTime": "2026-01-15T10:00:00Z",
            "generation": 110
        }
    ]

    forecasts = [
        {
            "startTime": "2026-01-15T10:00:00Z",
            "publishTime": "2026-01-14T09:00:00Z",
            "generation": 90
        },
        {
            "startTime": "2026-01-15T10:00:00Z",
            "publishTime": "2026-01-14T11:30:00Z",
            "generation": 100
        },
        {
            "startTime": "2026-01-15T10:00:00Z",
            "publishTime": "2026-01-14T15:00:00Z",
            "generation": 120
        }
    ]

    result = build_analysis(actuals, forecasts)

    assert len(result) == 1
    assert result[0]["forecast"] == 100
    assert result[0]["actual"] == 110
    assert result[0]["error"] == -10


def test_metrics():
    records = [
        {
            "forecast": 100,
            "actual": 110,
            "error": -10
        },
        {
            "forecast": 120,
            "actual": 110,
            "error": 10
        },
        {
            "forecast": 140,
            "actual": 150,
            "error": -10
        }
    ]

    metrics = calculate_metrics(records)

    assert metrics["mae"] == 10
    assert metrics["rmse"] == 10
    assert metrics["bias"] == -3.33


def test_no_eligible_forecast():
    actuals = [
        {
            "fuelType": "WIND",
            "startTime": "2026-01-15T10:00:00Z",
            "generation": 110
        }
    ]

    forecasts = [
        {
            "startTime": "2026-01-15T10:00:00Z",
            "publishTime": "2026-01-14T15:00:00Z",
            "generation": 120
        }
    ]

    result = build_analysis(actuals, forecasts)

    assert result == []


def test_empty_metrics():
    metrics = calculate_metrics([])

    assert metrics["count"] == 0
    assert metrics["mae"] is None