from datetime import datetime, timedelta, timezone
from collections import defaultdict
from math import sqrt
from statistics import mean


def parse_time(value):
    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    if result.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")

    return result.astimezone(timezone.utc)


def decision_cutoff(delivery_time, cutoff_hour=12):
    previous_day = delivery_time.date() - timedelta(days=1)

    return datetime(
        previous_day.year,
        previous_day.month,
        previous_day.day,
        cutoff_hour,
        0,
        tzinfo=timezone.utc
    )


def prepare_actuals(actuals):
    result = {}

    for row in actuals:
        if row.get("fuelType") != "WIND":
            continue

        if row.get("generation") is None:
            continue

        start = parse_time(row["startTime"])

        value = float(row["generation"])

        if start in result and result[start] != value:
            raise ValueError(
                f"Conflicting actual generation for {start}"
            )

        result[start] = value

    return result


def prepare_forecasts(forecasts):
    grouped = defaultdict(list)
    seen = set()

    for row in forecasts:
        if row.get("generation") is None:
            continue

        if not row.get("publishTime"):
            continue

        delivery = parse_time(row["startTime"])
        published = parse_time(row["publishTime"])
        value = float(row["generation"])

        identity = (delivery, published, value)

        if identity in seen:
            continue

        seen.add(identity)

        grouped[delivery].append({
            "publish_time": published,
            "generation": value
        })

    for delivery in grouped:
        grouped[delivery].sort(
            key=lambda row: row["publish_time"]
        )

    return grouped


def build_analysis(
    actuals,
    forecasts,
    start_date="2026-01-01",
    end_date="2026-02-02",
    cutoff_hour=12
):
    actual_map = prepare_actuals(actuals)
    forecast_map = prepare_forecasts(forecasts)

    start = parse_time(f"{start_date}T00:00:00Z")
    end = parse_time(f"{end_date}T00:00:00Z")

    records = []

    for delivery in sorted(actual_map):
        if not (start <= delivery < end):
            continue

        cutoff = decision_cutoff(delivery, cutoff_hour)

        # Only decisions made during January 2026
        if cutoff.year != 2026 or cutoff.month != 1:
            continue

        eligible = [
            item for item in forecast_map.get(delivery, [])
            if item["publish_time"] <= cutoff
        ]

        if not eligible:
            continue

        latest_time = max(
            item["publish_time"] for item in eligible
        )

        latest_records = [
            item for item in eligible
            if item["publish_time"] == latest_time
        ]

        values = {
            item["generation"] for item in latest_records
        }

        if len(values) != 1:
            raise ValueError(
                f"Conflicting forecasts for {delivery}"
            )

        forecast_value = values.pop()
        actual_value = actual_map[delivery]

        error = forecast_value - actual_value

        records.append({
            "startTime": delivery.isoformat(),
            "publishTime": latest_time.isoformat(),
            "decisionCutoff": cutoff.isoformat(),
            "forecast": round(forecast_value, 2),
            "actual": round(actual_value, 2),
            "error": round(error, 2),
            "absoluteError": round(abs(error), 2)
        })

    return records


def calculate_metrics(records):
    if not records:
        return {
            "count": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "mape": None,
            "meanActual": None,
            "meanForecast": None
        }

    errors = [row["error"] for row in records]

    absolute_errors = [abs(error) for error in errors]

    squared_errors = [error ** 2 for error in errors]

    percentage_errors = [
        abs(row["error"] / row["actual"]) * 100
        for row in records
        if row["actual"] != 0
    ]

    return {
        "count": len(records),
        "mae": round(mean(absolute_errors), 2),
        "rmse": round(sqrt(mean(squared_errors)), 2),
        "bias": round(mean(errors), 2),
        "mape": (
            round(mean(percentage_errors), 2)
            if percentage_errors else None
        ),
        "meanActual": round(
            mean(row["actual"] for row in records), 2
        ),
        "meanForecast": round(
            mean(row["forecast"] for row in records), 2
        )
    }