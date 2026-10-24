import json
from functools import lru_cache
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import DATA_DIR
from app.analysis import build_analysis, calculate_metrics


app = FastAPI(
    title="WindScope Analytics API",
    description="UK Wind Generation Forecast Accuracy",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_origin_regex=(
        r"https://[a-zA-Z0-9-]+\.vercel\.app"
    ),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"]
)


@lru_cache(maxsize=1)
def load_data():
    actual_path = DATA_DIR / "actuals.json"
    forecast_path = DATA_DIR / "forecasts.json"

    if not actual_path.exists():
        raise FileNotFoundError(
            "actuals.json is missing. Run download_data.py"
        )

    if not forecast_path.exists():
        raise FileNotFoundError(
            "forecasts.json is missing. Run download_data.py"
        )

    with open(actual_path, encoding="utf-8") as file:
        actuals = json.load(file)

    with open(forecast_path, encoding="utf-8") as file:
        forecasts = json.load(file)

    return actuals, forecasts


@lru_cache(maxsize=1)
def get_all_records():
    actuals, forecasts = load_data()

    return build_analysis(
        actuals,
        forecasts,
        start_date="2026-01-01",
        end_date="2026-02-02",
        cutoff_hour=12
    )


@app.get("/")
def root():
    return {
        "application": "WindScope Analytics",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/analysis")
def get_analysis(
    start_date: date = Query(default=date(2026, 1, 2)),
    end_date: date = Query(default=date(2026, 2, 1))
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot exceed end_date"
        )

    if (
        start_date < date(2026, 1, 1)
        or end_date > date(2026, 2, 1)
    ):
        raise HTTPException(
            status_code=400,
            detail="Dates must be within the supported period"
        )

    try:
        records = get_all_records()

    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        )

    filtered = [
        row for row in records
        if start_date.isoformat()
        <= row["decisionCutoff"][:10]
        <= end_date.isoformat()
    ]

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "methodology": {
            "decisionCutoff": "12:00 UTC on D-1",
            "forecastSelection": "Latest published before cutoff",
            "errorDefinition": "Forecast minus actual",
            "unit": "MW"
        },
        "metrics": calculate_metrics(filtered),
        "records": filtered
    }