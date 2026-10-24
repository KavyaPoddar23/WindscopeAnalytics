import asyncio
from datetime import date, datetime, timedelta, timezone

from app.elexon_client import ElexonClient, save_json


async def download():
    client = ElexonClient()

    actuals = []
    forecasts = []

    current = date(2025, 12, 31)
    last_day = date(2026, 2, 3)

    while current < last_day:
        next_day = current + timedelta(days=1)

        start = f"{current.isoformat()}T00:00:00Z"
        end = f"{next_day.isoformat()}T00:00:00Z"

        print(f"Downloading {current}...")

        daily_actuals = await client.get_actuals(start, end)
        daily_forecasts = await client.get_forecasts(start, end)

        actuals.extend(
            row for row in daily_actuals
            if row.get("fuelType") == "WIND"
        )

        forecasts.extend(daily_forecasts)

        print(
            f"  Actuals: {len(daily_actuals)}"
            f" | Forecasts: {len(daily_forecasts)}"
        )

        current = next_day

        await asyncio.sleep(0.5)

    actual_path = save_json("actuals.json", actuals)
    forecast_path = save_json("forecasts.json", forecasts)

    print("\nDownload completed")
    print("Actual records:", len(actuals))
    print("Forecast records:", len(forecasts))
    print("Saved:", actual_path)
    print("Saved:", forecast_path)


if __name__ == "__main__":
    asyncio.run(download())